import re
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from app.rag.text_cleaner import text_cleaner
from app.core.logging import logger

class BM25Indexer:
    """In-Memory BM25 Indexer optimized for Arabic tokenization."""

    def __init__(self):
        self.bm25: BM25Okapi = None
        self.corpus_nodes: List[Dict[str, Any]] = []

    def _tokenize_arabic(self, text: str) -> List[str]:
        cleaned = text_cleaner.clean(text, remove_tashkeel=True, normalize_letters=True)
        # Extract Arabic and alphanumeric words
        tokens = re.findall(r'\w+', cleaned.lower())
        return tokens

    def fit(self, child_nodes: List[Dict[str, Any]]) -> None:
        self.corpus_nodes = child_nodes
        tokenized_corpus = [self._tokenize_arabic(node["text"]) for node in child_nodes]
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info("BM25 Index fitted successfully", document_count=len(child_nodes))

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.corpus_nodes:
            return []

        tokenized_query = self._tokenize_arabic(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Zip nodes with scores and sort
        scored_nodes = list(zip(self.corpus_nodes, scores))
        scored_nodes.sort(key=lambda x: x[1], reverse=True)

        results = []
        for node, score in scored_nodes[:top_k]:
            if score > 0:
                results.append({
                    "id": node["id"],
                    "score": float(score),
                    "text": node["text"],
                    "parent_id": node["parent_id"],
                    "lesson_id": node["lesson_id"],
                    "metadata": node.get("metadata", {})
                })
        return results

bm25_indexer = BM25Indexer()
