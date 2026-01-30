"""Public API for accuralai-rag."""

from __future__ import annotations

from importlib.metadata import version

from .cache import RAGCache
from .chunking import SmartChunker
from .context import ContextualRAG
from .embeddings import MultiVectorRetriever
from .pipeline import UltraFastRAG
from .query import QueryOptimizer
from .search import HybridSearchEngine
from .types import DocumentChunk, RetrievalResult

__all__ = [
    "MultiVectorRetriever",
    "HybridSearchEngine",
    "SmartChunker",
    "QueryOptimizer",
    "ContextualRAG",
    "RAGCache",
    "UltraFastRAG",
    "DocumentChunk",
    "RetrievalResult",
    "__version__",
]


try:  # pragma: no cover - package metadata missing during editable installs
    __version__ = version("accuralai-rag")
except Exception:  # pragma: no cover
    __version__ = "0.0.0"
