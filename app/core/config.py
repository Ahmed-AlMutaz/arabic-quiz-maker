import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Arabic Exam SaaS"
    ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "production-secret-key-change-in-prod"

    # LLM & Embedding (Gemini)
    GEMINI_API_KEY: str = Field(default="", alias="gemini_api_key")
    LLM_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    # Qdrant Vector DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "arabic_lessons"

    # MongoDB Store
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "quiz_maker_db"

    # Redis & Celery
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # RAG & Chunking Config
    PARENT_CHUNK_SIZE: int = 1200
    PARENT_CHUNK_OVERLAP: int = 150
    CHILD_CHUNK_SIZE: int = 300
    CHILD_CHUNK_OVERLAP: int = 50
    HYBRID_SEARCH_TOP_K: int = 20
    RERANK_TOP_K: int = 6

    # Storage Paths
    STORAGE_DIR: str = "./storage"
    TEMP_DIR: str = "./storage/temp"
    EXAMS_DIR: str = "./storage/exams"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True
    )

    def get_gemini_api_key(self) -> str:
        key = self.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY") or os.environ.get("gemini_api_key")
        if not key:
            raise ValueError("GEMINI_API_KEY must be set in environment or .env file.")
        return key

settings = Settings()

# Ensure required storage directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.TEMP_DIR, exist_ok=True)
os.makedirs(settings.EXAMS_DIR, exist_ok=True)
