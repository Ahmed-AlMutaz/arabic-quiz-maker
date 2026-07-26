from typing import List, Dict, Any
import numpy as np
from app.rag.embeddings import embedding_generator
from app.core.config import settings
from app.core.logging import logger

class ReRanker:
    """Re-ranking Engine for retrieved parent candidates."""

    def __init__(self):
        self.top_k = settings.RERANK_TOP_K

    def rerank(self, query: str, candidate_parents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not candidate_parents:
            return []

        logger.info("Re-ranking candidate parent chunks...", count=len(candidate_parents))

        query_vec = np.array(embedding_generator.embed_query(query))
        
        scored_candidates = []
        for cand in candidate_parents:
            cand_text = cand["text"]
            cand_vec = np.array(embedding_generator.embed_text(cand_text[:500]))
            
            # Cosine similarity score
            dot_product = np.dot(query_vec, cand_vec)
            norm_q = np.linalg.norm(query_vec)
            norm_c = np.linalg.norm(cand_vec)
            
            similarity = dot_product / (norm_q * norm_c + 1e-8) if norm_q > 0 and norm_c > 0 else 0.0
            
            # Hybrid combined score (RRF + Semantic Similarity)
            final_score = 0.4 * cand.get("rrf_score", 0.0) + 0.6 * float(similarity)
            
            scored_candidates.append({
                **cand,
                "rerank_score": final_score
            })

        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        final_top = scored_candidates[:self.top_k]

        logger.info("Re-ranking completed", top_selected=len(final_top))
        return final_top

reranker = ReRanker()
