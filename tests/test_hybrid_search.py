from app.rag.hybrid_retriever import HybridRetriever

def test_rrf_scoring():
    retriever = HybridRetriever(k_rrf=60)
    dense_results = [
        {"id": "doc1", "payload": {"text": "النص الأول", "parent_id": "p1", "lesson_id": "l1"}},
        {"id": "doc2", "payload": {"text": "النص الثاني", "parent_id": "p2", "lesson_id": "l1"}}
    ]
    sparse_results = [
        {"id": "doc2", "text": "النص الثاني", "parent_id": "p2", "lesson_id": "l1"},
        {"id": "doc3", "text": "النص الثالث", "parent_id": "p3", "lesson_id": "l1"}
    ]

    fused = retriever.reciprocal_rank_fusion(dense_results, sparse_results, top_k=5)
    assert len(fused) == 3
    # doc2 appeared in both, so it should have the highest RRF score
    assert fused[0]["id"] == "doc2"
