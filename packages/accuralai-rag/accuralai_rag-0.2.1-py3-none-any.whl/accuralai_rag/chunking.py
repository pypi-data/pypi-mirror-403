"""Chunking utilities used by the RAG pipeline."""

from __future__ import annotations

import re
from typing import Any, List, Mapping, MutableMapping, Optional, Sequence

try:  # Optional dependency for semantic chunking
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional import
    SentenceTransformer = None  # type: ignore[assignment]

from .types import DocumentChunk
from .utils import cosine_similarity, stable_hash


class SmartChunker:
    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 128,
        use_semantic_splitting: bool = True,
        semantic_threshold: float = 0.7,
        chunk_id_prefix: str = "chunk",
    ) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.semantic_threshold = semantic_threshold
        self.chunk_id_prefix = chunk_id_prefix
        self._sentence_model = None
        if use_semantic_splitting and SentenceTransformer is not None:
            try:
                self._sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:  # pragma: no cover - optional download error
                self._sentence_model = None

    # ------------------------------------------------------------------
    def chunk_document(self, text: str, metadata: Optional[Mapping[str, Any]] = None) -> List[DocumentChunk]:
        if not text.strip():
            return []
        sentences = self._split_sentences(text)
        if self._sentence_model is not None:
            raw_chunks = self.semantic_chunk(sentences)
        else:
            raw_chunks = self.sliding_window_chunk(text)
        total = len(raw_chunks)
        chunks: List[DocumentChunk] = []
        for idx, chunk in enumerate(raw_chunks):
            base_meta: MutableMapping[str, Any] = dict(metadata or {})
            base_meta.update({"chunk_length": len(chunk), "chunk_tokens": len(chunk.split())})
            chunk_id = f"{self.chunk_id_prefix}-{stable_hash(chunk)[:12]}"
            chunks.append(
                DocumentChunk(
                    text=chunk,
                    chunk_id=chunk_id,
                    context=self.get_surrounding_context(chunk, text),
                    position=idx,
                    total_chunks=total,
                    metadata=base_meta,
                    fingerprint=stable_hash(chunk),
                )
            )
        return chunks

    # ------------------------------------------------------------------
    def semantic_chunk(self, sentences: Sequence[str]) -> List[str]:
        if not sentences:
            return []
        embeddings = self._sentence_model.encode(  # type: ignore[union-attr]
            list(sentences), normalize_embeddings=True, show_progress_bar=False
        )
        chunks: List[str] = []
        current: List[str] = []
        for idx, sentence in enumerate(sentences):
            current.append(sentence)
            boundary = False
            if idx < len(sentences) - 1:
                similarity = cosine_similarity(embeddings[idx], embeddings[idx + 1])
                boundary = similarity < self.semantic_threshold
            if len(" ".join(current)) >= self.chunk_size:
                boundary = True
            if boundary:
                chunks.append(" ".join(current).strip())
                if self.overlap and len(current) > 1:
                    current = current[-2:]
                else:
                    current = []
        if current:
            chunks.append(" ".join(current).strip())
        return [chunk for chunk in chunks if chunk]

    def sliding_window_chunk(self, text: str) -> List[str]:
        tokens = text.split()
        if not tokens:
            return []
        chunks: List[str] = []
        start = 0
        while start < len(tokens):
            end = min(len(tokens), start + self.chunk_size)
            chunks.append(" ".join(tokens[start:end]))
            if end == len(tokens):
                break
            start = max(end - self.overlap, start + 1)
        return chunks

    def get_surrounding_context(self, chunk: str, document: str, padding: int = 200) -> str:
        snippet = chunk[: min(len(chunk), 32)]
        idx = document.find(snippet)
        if idx == -1:
            return chunk
        start = max(idx - padding, 0)
        end = min(len(document), idx + len(chunk) + padding)
        return document[start:end]

    def _split_sentences(self, text: str) -> List[str]:
        pattern = re.compile(r"(?<=[.!?])\s+")
        sentences = re.split(pattern, text)
        return [sent.strip() for sent in sentences if sent.strip()]


__all__ = ["SmartChunker"]
