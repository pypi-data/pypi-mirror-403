# accuralai-rag

High-performance Retrieval Augmented Generation (RAG) utilities built for the AccuralAI orchestration ecosystem. The package provides:

- Multi-vector embedding utilities with optional GPU + hybrid sparse support.
- Intelligent chunking and metadata extraction helpers tuned for large documents.
- Hybrid dense/sparse retrieval with reciprocal rank fusion and reranking hooks.
- Query optimizers (HyDE, decomposition, semantic augmentation) plus advanced context builders.
- UltraFastRAG pipeline that combines the components with aggressive caching and streaming-friendly hooks.

All heavy dependencies are optional. Install extras such as `torch`, `transformers`, `faiss`, or `redis` based on your production topology:

```bash
pip install -e packages/accuralai-rag[torch,transformers,faiss,redis]
```

See `accuralai_rag/pipeline.py` for the orchestrated entry point and `tests/` for lightweight examples.
