"""UltraFastRAG pipeline wiring all components together."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, List, Mapping, Optional, Sequence

from .cache import RAGCache
from .chunking import SmartChunker
from .context import ContextualRAG
from .embeddings import MultiVectorRetriever
from .query import QueryOptimizer
from .search import HybridSearchEngine
from .types import DocumentChunk, RetrievalResult
from .utils import stable_hash

try:  # pragma: no cover - optional import for instrumentation
    from accuralai_core.core.context import ExecutionContext
except Exception:  # pragma: no cover - used in typing only
    ExecutionContext = None  # type: ignore[assignment]

GeneratorCallable = Callable[[str, str], Awaitable[str]]


class UltraFastRAG:
    def __init__(
        self,
        retriever: Optional[MultiVectorRetriever] = None,
        search_engine: Optional[HybridSearchEngine] = None,
        query_optimizer: Optional[QueryOptimizer] = None,
        context_manager: Optional[ContextualRAG] = None,
        chunker: Optional[SmartChunker] = None,
        cache: Optional[RAGCache] = None,
        generator: Optional[GeneratorCallable] = None,
        execution_context: Optional[ExecutionContext] = None,
    ) -> None:
        self.retriever = retriever or MultiVectorRetriever()
        self.search_engine = search_engine or HybridSearchEngine()
        self.query_optimizer = query_optimizer or QueryOptimizer()
        self.context_manager = context_manager or ContextualRAG()
        self.chunker = chunker or SmartChunker()
        self.cache = cache or RAGCache()
        self.generator = generator or self._default_generator
        self.execution_context = execution_context
        self._registered_chunks = 0

    # ------------------------------------------------------------------
    def precompute_embeddings(self) -> None:
        self.retriever.warmup()

    def register_documents(
        self,
        documents: Sequence[str],
        metadatas: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> None:
        if not documents:
            return
        metadata_seq = metadatas or [{} for _ in documents]
        if len(metadata_seq) != len(documents):
            raise ValueError("documents and metadata lengths must match")
        chunks: List[DocumentChunk] = []
        for text, meta in zip(documents, metadata_seq):
            chunks.extend(self.chunker.chunk_document(text, metadata=meta))
        self._add_chunks(chunks)

    # ------------------------------------------------------------------
    async def query(self, user_query: str, use_cache: bool = True) -> str:
        cache_key = f"response:{user_query}"
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                self._record_event(
                    "rag.query_executed",
                    {"query": user_query, "retrieved_chunks": 0, "cached": True},
                )
                return cached
        enhanced_queries = await self.query_optimizer.enhance_query(user_query)
        all_results: List[RetrievalResult] = []
        for variation in enhanced_queries:
            encoded = self.retriever.encode_queries([variation])
            dense_vec = encoded.get("dense")
            sparse_vec = encoded.get("sparse")
            dense_vector = dense_vec[0] if dense_vec else None
            sparse_vector = sparse_vec[0] if sparse_vec else None
            results = self.search_engine.search(
                variation,
                dense_vector=dense_vector,
                sparse_vector=sparse_vector,
                k=50,
                final_k=10,
            )
            all_results.extend(results)
        unique_chunks = self.deduplicate_and_score(all_results)
        context = self.context_manager.build_context(unique_chunks, user_query)
        response = await self.generate_with_streaming(user_query, context)
        self.cache.set(cache_key, response)
        self._record_event(
            "rag.query_executed",
            {
                "query": user_query,
                "retrieved_chunks": len(unique_chunks),
                "cached": False,
            },
        )
        return response

    # ------------------------------------------------------------------
    def deduplicate_and_score(self, results: Sequence[RetrievalResult]) -> List[RetrievalResult]:
        deduped: dict[str, RetrievalResult] = {}
        for result in results:
            fingerprint = result.chunk.fingerprint or stable_hash(result.chunk.text)
            existing = deduped.get(fingerprint)
            if existing is None or result.score > existing.score:
                deduped[fingerprint] = RetrievalResult(
                    chunk=result.chunk,
                    score=result.score,
                    source=result.source,
                    metadata=result.metadata,
                )
        return sorted(deduped.values(), key=lambda res: res.score, reverse=True)

    async def generate_with_streaming(self, query: str, context: str) -> str:
        return await self.generator(query, context)

    async def _default_generator(self, query: str, context: str) -> str:
        return f"Query: {query}\nContext:\n{context}"

    # ------------------------------------------------------------------
    def _add_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        if not chunks:
            return
        embeddings = self.retriever.encode_documents([chunk.text for chunk in chunks])
        metadata = embeddings.get("metadata") or [{} for _ in chunks]
        for chunk, extra in zip(chunks, metadata):
            chunk.metadata.update(extra)
        self.search_engine.add_documents(
            chunks,
            dense_embeddings=embeddings.get("dense") or [],
            sparse_embeddings=embeddings.get("sparse") or None,
        )
        self._registered_chunks += len(chunks)
        self._record_event(
            "rag.chunks_registered",
            {"count": len(chunks), "total_chunks": self._registered_chunks},
        )

    def _record_event(self, name: str, payload: Mapping[str, Any]) -> None:
        if not self.execution_context:
            return
        try:
            self.execution_context.record_event(name, payload)
        except Exception:
            pass


__all__ = ["UltraFastRAG"]
