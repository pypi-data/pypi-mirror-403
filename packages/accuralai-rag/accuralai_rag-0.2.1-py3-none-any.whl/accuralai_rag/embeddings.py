"""Multi-vector embedding utilities for dense + sparse retrieval."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Mapping, MutableSequence, Optional, Sequence

try:  # Optional heavy dependencies
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency not installed
    SentenceTransformer = None  # type: ignore[assignment]

try:
    import torch
except Exception:  # pragma: no cover - torch optional
    torch = None  # type: ignore[assignment]

from .types import SparseVector, Vector
from .utils import maybe_to_numpy, normalize_vector, stable_hash

LOGGER = logging.getLogger(__name__)


class MultiVectorRetriever:
    """Produces dense + sparse + metadata representations for documents/queries."""

    def __init__(
        self,
        dense_model_name: str = "BAAI/bge-large-en-v1.5",
        sparse_encoder: Optional[Any] = None,
        metadata_extractor: Optional[Any] = None,
        enable_gpu: bool = True,
        quantize_dense: bool = False,
        dense_batch_size: int = 64,
    ):
        self.dense_model_name = dense_model_name
        self.sparse_encoder = sparse_encoder
        self.metadata_extractor = metadata_extractor
        self.enable_gpu = enable_gpu
        self.quantize_dense = quantize_dense
        self.dense_batch_size = dense_batch_size
        self._dense_model = self._load_dense_model()

    def _load_dense_model(self) -> Optional[Any]:
        if SentenceTransformer is None:
            LOGGER.info("sentence-transformers not installed; falling back to hashed embeddings")
            return None
        try:
            model = SentenceTransformer(self.dense_model_name)
        except Exception as exc:  # pragma: no cover - network install path
            LOGGER.warning("Failed to load dense model %s: %s", self.dense_model_name, exc)
            return None
        if self.enable_gpu and torch is not None and torch.cuda.is_available():
            model = model.to("cuda")
            if hasattr(torch, "compile"):
                try:
                    model = torch.compile(model)  # type: ignore[arg-type]
                except Exception:  # pragma: no cover - compile optional
                    pass
        return model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def encode_documents(self, texts: Sequence[str]) -> Dict[str, Sequence[Any]]:
        dense = self._encode_dense(texts)
        sparse = self.generate_sparse_embeddings(texts)
        metadata = self.extract_metadata(texts)
        return {"dense": dense, "sparse": sparse, "metadata": metadata}

    def encode_queries(self, texts: Sequence[str]) -> Dict[str, Sequence[Any]]:
        return self.encode_documents(texts)

    def warmup(self) -> None:
        if not self._dense_model:
            return
        _ = self._encode_dense(["warmup text"])

    def batch_process_queries(self, queries: Sequence[str], batch_size: Optional[int] = None):
        batch = batch_size or self.dense_batch_size
        if self._dense_model is None or torch is None or not torch.cuda.is_available():
            return self._encode_dense(queries, batch_size=batch)
        stream = torch.cuda.Stream()  # type: ignore[attr-defined]
        with torch.cuda.stream(stream):  # type: ignore[attr-defined]
            embeddings = self._dense_model.encode(  # type: ignore[union-attr]
                list(queries),
                batch_size=batch,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        stream.synchronize()
        return embeddings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _encode_dense(self, texts: Sequence[str], batch_size: Optional[int] = None) -> Sequence[Sequence[float]]:
        if not texts:
            return []
        batch = batch_size or self.dense_batch_size
        if self._dense_model is None:
            return [self._fallback_dense(t) for t in texts]
        vectors = self._dense_model.encode(  # type: ignore[union-attr]
            list(texts),
            batch_size=batch,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        if self.quantize_dense:
            vectors = self._quantize(vectors)
        return vectors

    def _fallback_dense(self, text: str, dim: int = 256) -> Sequence[float]:
        tokens = text.lower().split()
        bucket: List[float] = [0.0] * dim
        for tok in tokens:
            idx = int(stable_hash(tok), 16) % dim
            bucket[idx] += 1.0
        return normalize_vector(bucket)

    def _quantize(self, vectors: Sequence[Sequence[float]]):
        if torch is not None:
            return torch.quantize_per_tensor(torch.tensor(vectors), scale=1.0 / 128, zero_point=0, dtype=torch.qint8)
        return [[float(int(v * 128) / 128.0) for v in vec] for vec in vectors]

    def generate_sparse_embeddings(self, texts: Sequence[str]) -> Sequence[SparseVector]:
        if self.sparse_encoder is not None:
            try:
                return self.sparse_encoder.encode(texts)
            except Exception:  # pragma: no cover - passthrough if encoder fails
                LOGGER.exception("Sparse encoder raised; falling back to TF counts")
        sparse_vectors: List[SparseVector] = []
        for text in texts:
            counts: Dict[str, float] = {}
            for token in text.lower().split():
                counts[token] = counts.get(token, 0.0) + 1.0
            sparse_vectors.append(counts)
        return sparse_vectors

    def extract_metadata(self, texts: Sequence[str]) -> Sequence[Mapping[str, Any]]:
        if self.metadata_extractor is not None:
            return self.metadata_extractor(texts)
        metadata: List[Dict[str, Any]] = []
        for text in texts:
            tokens = text.split()
            unique_tokens = list(dict.fromkeys(tok.lower() for tok in tokens))
            metadata.append(
                {
                    "length": len(text),
                    "token_count": len(tokens),
                    "key_phrases": unique_tokens[:8],
                    "fingerprint": stable_hash(text)[:16],
                }
            )
        return metadata


__all__ = ["MultiVectorRetriever"]
