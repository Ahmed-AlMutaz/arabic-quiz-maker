from fastapi import APIRouter
from app.api.v1.endpoints import ocr, exam, download, evaluation, health

api_router = APIRouter()

api_router.include_router(ocr.router, prefix="/ocr", tags=["OCR & Indexing"])
api_router.include_router(exam.router, prefix="/exam", tags=["Exam Generation"])
api_router.include_router(download.router, prefix="/download", tags=["Word Doc Downloads"])
api_router.include_router(evaluation.router, prefix="/eval", tags=["RAGAS Evaluation"])
api_router.include_router(health.router, tags=["System Health & Metrics"])
