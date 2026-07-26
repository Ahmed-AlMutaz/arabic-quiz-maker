from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from app.core.config import settings
from app.core.logging import logger

class QdrantManager:
    """Manages Vector Database storage using Qdrant with graceful in-memory fallback."""
    
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.client: QdrantClient = self._initialize_client()
        self.vector_size = 768  # Text Embedding 004 dimension

    def _initialize_client(self) -> QdrantClient:
        try:
            # Only pass api_key if it's a real non-empty value to avoid SSL/TLS errors
            api_key = settings.QDRANT_API_KEY if settings.QDRANT_API_KEY and settings.QDRANT_API_KEY.strip() else None
            client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=api_key,
                timeout=5.0
            )
            # Test connection
            client.get_collections()
            logger.info("Connected to remote Qdrant server", host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            return client
        except Exception as e:
            logger.warning("Remote Qdrant connection failed, falling back to local in-memory Qdrant instance", error=str(e))
            return QdrantClient(location=":memory:")

    def init_collection(self, vector_size: int = 768) -> None:
        self.vector_size = vector_size
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection", collection=self.collection_name, vector_size=self.vector_size)

    def upsert_vectors(self, points: List[PointStruct]) -> bool:
        try:
            self.init_collection(self.vector_size)
            self.client.upsert(collection_name=self.collection_name, points=points)
            logger.info("Successfully upserted points to Qdrant", count=len(points))
            return True
        except Exception as e:
            logger.error("Failed to upsert vectors to Qdrant", error=str(e))
            return False

    def search_similar(self, query_vector: List[float], limit: int = 10, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        try:
            self.init_collection(len(query_vector))
            if hasattr(self.client, "query_points"):
                res = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    limit=limit
                )
                search_result = getattr(res, "points", [])
            elif hasattr(self.client, "search"):
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=limit
                )
            else:
                search_result = []

            hits = []
            for res in search_result:
                hits.append({
                    "id": res.id,
                    "score": getattr(res, "score", 1.0),
                    "payload": getattr(res, "payload", {})
                })
            return hits
        except Exception as e:
            logger.error("Qdrant similarity search error", error=str(e))
            return []

qdrant_manager = QdrantManager()
