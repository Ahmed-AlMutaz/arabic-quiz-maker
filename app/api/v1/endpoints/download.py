import os
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

@router.get("/student/{exam_id}", summary="Download Student Examination Word (.docx) File")
async def download_student_docx(exam_id: str):
    filename = f"Student_{exam_id}.docx"
    file_path = os.path.join(settings.EXAMS_DIR, filename)

    if not os.path.exists(file_path):
        logger.warning("Student docx requested but not found on disk", exam_id=exam_id, path=file_path)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student exam file for '{exam_id}' not found.")

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )

@router.get("/teacher/{exam_id}", summary="Download Teacher Model Answer Key Word (.docx) File")
async def download_teacher_docx(exam_id: str):
    filename = f"Teacher_{exam_id}.docx"
    file_path = os.path.join(settings.EXAMS_DIR, filename)

    if not os.path.exists(file_path):
        logger.warning("Teacher docx requested but not found on disk", exam_id=exam_id, path=file_path)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Teacher answer key file for '{exam_id}' not found.")

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )
