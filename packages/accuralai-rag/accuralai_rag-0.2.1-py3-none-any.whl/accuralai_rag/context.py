"""Context building utilities for UltraFastRAG."""

from __future__ import annotations

from typing import List, Sequence

from .types import DocumentChunk, RetrievalResult


class ContextualRAG:
    def __init__(self, context_window: int = 8192, compressor: object | None = None) -> None:
        self.context_window = context_window
        self.compressor = compressor

    # ------------------------------------------------------------------
    def build_context(self, retrieved_chunks: Sequence[RetrievalResult], query: str) -> str:
        scored = self.score_chunks(list(retrieved_chunks), query)
        ordered = self.optimize_chunk_order(scored)
        trimmed = self._enforce_window(ordered)
        return self.format_context(trimmed)

    def score_chunks(self, retrieved_chunks: Sequence[RetrievalResult], query: str) -> List[RetrievalResult]:
        query_terms = set(query.lower().split())
        seen_fingerprints = set()
        scored: List[RetrievalResult] = []
        for result in retrieved_chunks:
            text_terms = set(result.chunk.text.lower().split())
            coverage = len(query_terms & text_terms) / (len(query_terms) + 1e-6)
            novelty_penalty = 0.1 if result.chunk.fingerprint in seen_fingerprints else 0.0
            score = float(result.score) * 0.7 + coverage * 0.3 - novelty_penalty
            seen_fingerprints.add(result.chunk.fingerprint)
            scored.append(
                RetrievalResult(
                    chunk=result.chunk,
                    score=score,
                    source=result.source,
                    metadata=dict(result.metadata),
                )
            )
        return sorted(scored, key=lambda res: res.score, reverse=True)

    def optimize_chunk_order(self, chunks: Sequence[RetrievalResult]) -> List[RetrievalResult]:
        result: List[RetrievalResult] = []
        for idx, chunk in enumerate(chunks):
            if idx % 2 == 0:
                result.insert(0, chunk)
            else:
                result.append(chunk)
        return result

    def _enforce_window(self, chunks: Sequence[RetrievalResult]) -> List[RetrievalResult]:
        trimmed = list(chunks)
        while self.total_tokens(trimmed) > self.context_window and trimmed:
            trimmed.pop(len(trimmed) // 2)
        if self.compressor and self.total_tokens(trimmed) > self.context_window:
            trimmed = self.compress_context(trimmed)
        return trimmed

    def compress_context(self, chunks: Sequence[RetrievalResult]) -> List[RetrievalResult]:
        if not self.compressor:
            return list(chunks)
        compressed: List[RetrievalResult] = []
        for result in chunks:
            summary = self.compressor.compress(result.chunk.text)
            chunk = DocumentChunk(
                text=summary,
                chunk_id=f"compressed-{result.chunk.chunk_id}",
                metadata=result.chunk.metadata,
                fingerprint=result.chunk.fingerprint,
            )
            compressed.append(RetrievalResult(chunk=chunk, score=result.score, source=result.source, metadata=result.metadata))
        return compressed

    def format_context(self, chunks: Sequence[RetrievalResult]) -> str:
        sections = []
        for idx, result in enumerate(chunks):
            prefix = f"[Chunk {idx + 1}/{len(chunks)} | score={result.score:.2f}]"
            sections.append(f"{prefix}\n{result.chunk.text}\n")
        return "\n".join(sections)

    def total_tokens(self, chunks: Sequence[RetrievalResult]) -> int:
        return sum(result.chunk.token_count() for result in chunks)


__all__ = ["ContextualRAG"]
