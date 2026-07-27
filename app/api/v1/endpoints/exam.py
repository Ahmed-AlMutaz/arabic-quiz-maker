from typing import Optional
from fastapi import APIRouter, HTTPException, Header, status
from app.schemas.request import ExamGenerationRequest
from app.schemas.exam import GeneratedExam
from app.services.exam_service import exam_service
from app.db.mongo_client import mongo_manager
from app.core.logging import logger
import google.generativeai as genai

router = APIRouter()

@router.post("/generate", response_model=GeneratedExam, summary="Generate Professional Arabic Exam & Word Docs")
async def generate_exam(request: ExamGenerationRequest, x_gemini_api_key: Optional[str] = Header(default=None)):
    logger.info("Received Exam Generation Request", lesson_id=request.lesson_id)
    if x_gemini_api_key and x_gemini_api_key.strip():
        logger.info("Using custom user-provided Gemini API Key from header")
        genai.configure(api_key=x_gemini_api_key.strip())
    exam = await exam_service.generate_exam(request, gemini_api_key=x_gemini_api_key)
    return exam

@router.get("/status/{exam_id}", summary="Check Status of Exam Generation Task")
async def check_exam_status(exam_id: str):
    exam = await mongo_manager.get_exam(exam_id)
    if not exam:
        return {"exam_id": exam_id, "status": "processing_or_not_found"}
    return {"exam_id": exam_id, "status": "completed", "student_url": exam.get("student_docx_url"), "teacher_url": exam.get("teacher_docx_url")}

@router.get("/count", summary="Get total number of exams generated")
async def get_exams_count():
    try:
        count = await mongo_manager.get_exams_count()
        return {"count": count}
    except Exception as e:
        logger.error("Error fetching exams count", error=str(e))
        return {"count": 0}
