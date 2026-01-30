"""Query expansion utilities (HyDE, decomposition, semantic mixes)."""

from __future__ import annotations

import asyncio
from typing import List, Optional

from .types import LLMClient


class QueryOptimizer:
    def __init__(self, llm: Optional[LLMClient] = None) -> None:
        self.llm = llm

    async def enhance_query(self, original_query: str) -> List[str]:
        variations = [original_query.strip()]
        hyde_task = asyncio.create_task(self.hypothetical_answer_generation(original_query))
        decomp_task = asyncio.create_task(self.query_decomposition(original_query))
        semantic_task = asyncio.create_task(self.semantic_variations(original_query))
        for task in (hyde_task, decomp_task, semantic_task):
            value = await task
            if isinstance(value, list):
                variations.extend(value)
            else:
                variations.append(value)
        # Deduplicate while preserving order
        ordered = list(dict.fromkeys(filter(None, (v.strip() for v in variations))))
        return ordered

    async def hypothetical_answer_generation(self, query: str) -> str:
        if self.llm is None:
            return f"Hypothetical detailed answer about: {query}"
        prompt = f"Write a concise but detailed hypothetical answer for the question: {query}"
        return await self.llm.generate(prompt, max_tokens=200)

    async def query_decomposition(self, query: str) -> List[str]:
        separators = [" and ", " vs ", " with "]
        parts: List[str] = []
        lowered = query.lower()
        for sep in separators:
            if sep in lowered:
                parts.extend(segment.strip() for segment in query.split(sep) if segment.strip())
        if not parts:
            tokens = query.split()
            midpoint = len(tokens) // 2
            if midpoint > 3:
                parts = [" ".join(tokens[:midpoint]), " ".join(tokens[midpoint:])]
        return parts or [query]

    async def semantic_variations(self, query: str) -> List[str]:
        keywords = query.split()
        variations = [f"{query} detailed explanation", f"{query} troubleshooting"]
        if keywords:
            variations.append(" ".join(sorted(set(keywords), reverse=True)))
        return variations


__all__ = ["QueryOptimizer"]
