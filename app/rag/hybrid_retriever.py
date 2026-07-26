from typing import List, Dict, Any
from app.rag.embeddings import embedding_generator
from app.db.qdrant_client import qdrant_manager
from app.rag.bm25_indexer import bm25_indexer
from app.core.config import settings
from app.core.logging import logger

class HybridRetriever:
    """Combines BM25 Sparse Search + Qdrant Dense Vector Search using Reciprocal Rank Fusion (RRF)."""

    def __init__(self, k_rrf: int = 60):
        self.k_rrf = k_rrf

    def reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        top_k: int = settings.HYBRID_SEARCH_TOP_K
    ) -> List[Dict[str, Any]]:
        """Applies RRF algorithm to merge dense and sparse rank lists."""
        rrf_scores: Dict[str, float] = {}
        node_map: Dict[str, Dict[str, Any]] = {}

        # Process Dense results
        for rank, hit in enumerate(dense_results):
            c_id = hit["id"]
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (self.k_rrf + rank + 1))
            if c_id not in node_map:
                payload = hit.get("payload", {})
                node_map[c_id] = {
                    "id": c_id,
                    "text": payload.get("text", ""),
                    "parent_id": payload.get("parent_id", ""),
                    "lesson_id": payload.get("lesson_id", ""),
                    "metadata": payload
                }

        # Process Sparse results
        for rank, hit in enumerate(sparse_results):
            c_id = hit["id"]
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (self.k_rrf + rank + 1))
            if c_id not in node_map:
                node_map[c_id] = {
                    "id": c_id,
                    "text": hit["text"],
                    "parent_id": hit["parent_id"],
                    "lesson_id": hit["lesson_id"],
                    "metadata": hit.get("metadata", {})
                }

        # Sort nodes by combined RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        fused_list = []
        for c_id in sorted_ids[:top_k]:
            node = node_map[c_id]
            node["rrf_score"] = rrf_scores[c_id]
            fused_list.append(node)

        logger.info("RRF Hybrid Fusion completed", fused_count=len(fused_list))
        return fused_list

    def retrieve(
        self,
        query: str,
        lesson_parents: Dict[str, Any],
        top_k: int = settings.HYBRID_SEARCH_TOP_K
    ) -> List[Dict[str, Any]]:
        """Performs hybrid search and maps retrieved child chunks to their Parent Documents."""
        # 1. Dense retrieval
        query_vec = embedding_generator.embed_query(query)
        dense_hits = qdrant_manager.search_similar(query_vec, limit=top_k)

        # 2. Sparse retrieval
        sparse_hits = bm25_indexer.search(query, top_k=top_k)

        # 3. Reciprocal Rank Fusion
        child_candidates = self.reciprocal_rank_fusion(dense_hits, sparse_hits, top_k=top_k)

        # 4. Parent Document Mapping
        retrieved_parents = []
        seen_parent_ids = set()

        for child in child_candidates:
            p_id = child.get("parent_id")
            if p_id and p_id in lesson_parents and p_id not in seen_parent_ids:
                seen_parent_ids.add(p_id)
                parent_node = lesson_parents[p_id]
                retrieved_parents.append({
                    "parent_id": p_id,
                    "text": parent_node.text if hasattr(parent_node, "text") else parent_node.get("text", ""),
                    "matched_child_id": child["id"],
                    "rrf_score": child["rrf_score"]
                })

        logger.info("Hybrid Retrieval mapped to Parent Documents", parents_count=len(retrieved_parents))
        return retrieved_parents

hybrid_retriever = HybridRetriever()
