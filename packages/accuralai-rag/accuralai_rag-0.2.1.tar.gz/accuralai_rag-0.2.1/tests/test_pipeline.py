import asyncio

from accuralai_rag.pipeline import UltraFastRAG


class StubGenerator:
    async def __call__(self, query: str, context: str) -> str:
        return f"{query}::{len(context.split())}"


def test_pipeline_runs_and_caches_results():
    rag = UltraFastRAG(generator=StubGenerator())
    documents = [
        "AccuralAI builds pragmatic RAG systems with hybrid retrieval and adaptive tooling.",
        "Retrieval augmented generation benefits from intelligent chunking and caching strategies.",
    ]
    rag.register_documents(documents)

    first = asyncio.run(rag.query("What does AccuralAI build?", use_cache=True))
    second = asyncio.run(rag.query("What does AccuralAI build?", use_cache=True))

    assert first == second
    assert "AccuralAI" in first


def test_pipeline_handles_multiple_variations():
    rag = UltraFastRAG(generator=StubGenerator())
    rag.register_documents(["Python enables high-throughput data tools."])
    response = asyncio.run(rag.query("Explain the benefits of python", use_cache=False))
    assert "python" in response.lower()
