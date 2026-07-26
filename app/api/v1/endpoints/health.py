from fastapi import APIRouter
from app.core.config import settings
from app.db.qdrant_client import qdrant_manager
from app.db.mongo_client import mongo_manager

router = APIRouter()

@router.get("/health", summary="Service Health Check")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "qdrant_status": "connected" if qdrant_manager.client else "in_memory",
        "mongo_status": "connected" if mongo_manager.use_mongo else "in_memory"
    }

@router.get("/metrics", summary="System Analytics Metrics")
async def get_metrics():
    return {
        "total_lessons_indexed": len(mongo_manager._in_memory_store["lessons"]),
        "total_exams_generated": len(mongo_manager._in_memory_store["exams"]),
        "total_evaluations_run": len(mongo_manager._in_memory_store["evaluations"]),
        "rag_pipeline": "Parent-Child Tree + BM25 + Qdrant RRF + Gemini 1.5"
    }
