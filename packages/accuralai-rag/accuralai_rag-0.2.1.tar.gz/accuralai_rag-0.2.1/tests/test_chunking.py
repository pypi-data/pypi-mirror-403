from accuralai_rag.chunking import SmartChunker


def test_chunker_generates_consistent_chunks():
    text = "Sentence one. Sentence two ties closely. Sentence three diverges." * 5
    chunker = SmartChunker(use_semantic_splitting=False, chunk_size=40, overlap=10)
    chunks = chunker.chunk_document(text)
    assert chunks
    assert all(chunk.chunk_id for chunk in chunks)
    assert chunks[0].total_chunks == len(chunks)
