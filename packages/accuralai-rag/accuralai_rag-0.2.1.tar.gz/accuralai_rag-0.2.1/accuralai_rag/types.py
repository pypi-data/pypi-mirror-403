"""Shared datatypes and protocols for the accuralai-rag package."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, MutableMapping, Optional, Protocol, Sequence

Vector = Sequence[float]
SparseVector = Mapping[str, float]


@dataclass
class DocumentChunk:
    """Single chunk of text plus metadata derived during preprocessing."""

    text: str
    chunk_id: str
    context: Optional[str] = None
    position: Optional[int] = None
    total_chunks: Optional[int] = None
    metadata: MutableMapping[str, Any] = field(default_factory=dict)
    fingerprint: Optional[str] = None

    def token_count(self) -> int:
        return len(self.text.split())


@dataclass
class RetrievalResult:
    """Container for retrieved chunks with provenance and scores."""

    chunk: DocumentChunk
    score: float
    source: str = "dense"
    metadata: MutableMapping[str, Any] = field(default_factory=dict)


@dataclass
class QueryVariant:
    """Represents an augmented query text plus generation hints."""

    text: str
    hint: str


class LLMClient(Protocol):
    async def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        ...


__all__ = [
    "DocumentChunk",
    "RetrievalResult",
    "QueryVariant",
    "Vector",
    "SparseVector",
    "LLMClient",
]
