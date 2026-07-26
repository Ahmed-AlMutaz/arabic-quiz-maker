from fastapi import APIRouter
from app.schemas.evaluation import RAGASEvalRequest, RAGASEvalReport
from app.services.eval_service import eval_service

router = APIRouter()

@router.post("/evaluate", response_model=RAGASEvalReport, summary="Evaluate RAG Exam Quality via RAGAS Framework")
async def evaluate_exam(request: RAGASEvalRequest):
    report = await eval_service.evaluate_exam(request)
    return report
