"""Hybrid dense+sparse search with reranking."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:  # Optional ANN dependency
    import faiss  # type: ignore
except Exception:  # pragma: no cover - faiss optional
    faiss = None  # type: ignore[assignment]

try:
    from rank_bm25 import BM25Okapi
except Exception:  # pragma: no cover - bm25 optional
    BM25Okapi = None  # type: ignore[assignment]

from .types import DocumentChunk, RetrievalResult, SparseVector, Vector
from .utils import cosine_similarity, maybe_to_numpy

LOGGER = logging.getLogger(__name__)


class HybridSearchEngine:
    def __init__(
        self,
        dimension: int = 768,
        hnsw_m: int = 32,
        ef_search: int = 128,
        rrf_constant: int = 60,
        reranker: Optional[object] = None,
    ) -> None:
        self.dimension = dimension
        self.hnsw_m = hnsw_m
        self.ef_search = ef_search
        self.rrf_constant = rrf_constant
        self.reranker = reranker
        self._dense_index = self._build_index()
        self._chunk_store: Dict[str, DocumentChunk] = {}
        self._chunk_ids: List[str] = []
        self._dense_vectors: List[Vector] = []
        self._sparse_vectors: Dict[str, SparseVector] = {}
        self._bm25 = None
        self._bm25_corpus: List[List[str]] = []

    def _build_index(self):
        if faiss is None:
            return None
        index = faiss.IndexHNSWFlat(self.dimension, self.hnsw_m)
        index.hnsw.efSearch = self.ef_search
        return index

    # ------------------------------------------------------------------
    def add_documents(
        self,
        chunks: Sequence[DocumentChunk],
        dense_embeddings: Sequence[Vector],
        sparse_embeddings: Optional[Sequence[SparseVector]] = None,
    ) -> None:
        if not chunks:
            return
        if len(chunks) != len(dense_embeddings):
            raise ValueError("Chunks and dense embeddings must align")
        sparse_embeddings = sparse_embeddings or [{} for _ in chunks]
        if len(sparse_embeddings) != len(chunks):
            raise ValueError("Chunks and sparse embeddings must align")

        for chunk, dense_vec, sparse_vec in zip(chunks, dense_embeddings, sparse_embeddings):
            self._chunk_store[chunk.chunk_id] = chunk
            self._chunk_ids.append(chunk.chunk_id)
            self._dense_vectors.append(list(dense_vec))
            self._sparse_vectors[chunk.chunk_id] = dict(sparse_vec)
            self._bm25_corpus.append(chunk.text.lower().split())
            if self._dense_index is not None:
                self._dense_index.add(maybe_to_numpy([dense_vec]))

        if BM25Okapi is not None and self._bm25_corpus:
            self._bm25 = BM25Okapi(self._bm25_corpus)

    # ------------------------------------------------------------------
    def search(
        self,
        query: str,
        dense_vector: Optional[Vector],
        sparse_vector: Optional[SparseVector] = None,
        k: int = 100,
        final_k: int = 10,
    ) -> List[RetrievalResult]:
        dense_results = self.dense_search(dense_vector, k)
        sparse_results = self.sparse_search(query, sparse_vector, k)
        fused = self.reciprocal_rank_fusion([dense_results, sparse_results])
        reranked = self.neural_rerank(query, fused[: max(final_k * 2, final_k)])
        return reranked[:final_k]

    # ------------------------------------------------------------------
    def dense_search(self, dense_vector: Optional[Vector], k: int) -> List[RetrievalResult]:
        if dense_vector is None or not self._dense_vectors:
            return []
        results: List[RetrievalResult] = []
        k = min(k, len(self._chunk_ids))
        if self._dense_index is not None:
            _, indices = self._dense_index.search(maybe_to_numpy([dense_vector]), k)
            for idx in indices[0]:
                if idx == -1:
                    continue
                chunk_id = self._chunk_ids[idx]
                score = cosine_similarity(dense_vector, self._dense_vectors[idx])
                results.append(self._build_result(chunk_id, score, "dense"))
            return results

        for chunk_id, stored_vec in zip(self._chunk_ids, self._dense_vectors):
            score = cosine_similarity(dense_vector, stored_vec)
            results.append(self._build_result(chunk_id, score, "dense"))
        return sorted(results, key=lambda res: res.score, reverse=True)[:k]

    def sparse_search(self, query: str, sparse_vector: Optional[SparseVector], k: int) -> List[RetrievalResult]:
        if not self._chunk_ids:
            return []
        if self._bm25 is not None:
            tokens = query.lower().split()
            scores = self._bm25.get_scores(tokens)
            ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:k]
            return [self._build_result(self._chunk_ids[idx], float(score), "sparse") for idx, score in ranked if score > 0]

        query_terms = sparse_vector or {term: 1.0 for term in query.lower().split()}
        scored: List[RetrievalResult] = []
        for chunk_id, chunk_vector in self._sparse_vectors.items():
            overlap = sum(query_terms.get(term, 0.0) * weight for term, weight in chunk_vector.items())
            if overlap:
                scored.append(self._build_result(chunk_id, float(overlap), "sparse"))
        return sorted(scored, key=lambda res: res.score, reverse=True)[:k]

    def reciprocal_rank_fusion(self, result_sets: Sequence[Sequence[RetrievalResult]]) -> List[RetrievalResult]:
        fused: Dict[str, float] = {}
        exemplars: Dict[str, RetrievalResult] = {}
        for results in result_sets:
            for rank, result in enumerate(results):
                key = result.chunk.chunk_id
                fused[key] = fused.get(key, 0.0) + 1.0 / (self.rrf_constant + rank + 1)
                exemplars.setdefault(key, result)
        ordered = sorted(fused.items(), key=lambda item: item[1], reverse=True)
        fused_results: List[RetrievalResult] = []
        for chunk_id, score in ordered:
            exemplar = exemplars[chunk_id]
            fused_results.append(
                RetrievalResult(
                    chunk=exemplar.chunk,
                    score=score,
                    source=exemplar.source,
                    metadata=dict(exemplar.metadata),
                )
            )
        return fused_results

    def neural_rerank(self, query: str, candidates: Sequence[RetrievalResult]) -> List[RetrievalResult]:
        if not candidates:
            return []
        if self.reranker is None:
            return sorted(candidates, key=lambda res: res.score, reverse=True)

        scored: List[RetrievalResult] = []
        for result in candidates:
            try:
                if hasattr(self.reranker, "score"):
                    rerank_score = float(self.reranker.score(query, result.chunk.text))  # type: ignore[attr-defined]
                else:
                    rerank_score = float(self.reranker(query, result.chunk.text))  # type: ignore[call-arg]
            except Exception:  # pragma: no cover - reranker failure fallback
                LOGGER.exception("Reranker failed; falling back to baseline score")
                rerank_score = result.score
            merged = RetrievalResult(chunk=result.chunk, score=rerank_score, source=result.source, metadata=dict(result.metadata))
            scored.append(merged)
        return sorted(scored, key=lambda res: res.score, reverse=True)

    def _build_result(self, chunk_id: str, score: float, source: str) -> RetrievalResult:
        chunk = self._chunk_store[chunk_id]
        return RetrievalResult(chunk=chunk, score=float(score), source=source, metadata=dict(chunk.metadata))


__all__ = ["HybridSearchEngine"]
