from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header, status
from app.schemas.ocr import OCRResponse
from app.schemas.request import RawTextIndexRequest
from app.services.ocr_service import ocr_service
from app.core.logging import logger
import google.generativeai as genai

router = APIRouter()

@router.post("/upload", response_model=OCRResponse, summary="Upload Lesson Images or PDFs for OCR & RAG Indexing")
@router.post("/ocr/upload", response_model=OCRResponse, include_in_schema=False)
async def upload_lesson_images(
    files: List[UploadFile] = File(..., description="One or multiple lesson pages (PDF, JPEG, PNG)"),
    lesson_title: str = Form(default="درس عربي جديدة", description="Title of the lesson"),
    x_gemini_api_key: Optional[str] = Header(default=None)
):
    if x_gemini_api_key and x_gemini_api_key.strip():
        logger.info("Using custom user-provided Gemini API Key from header in OCR upload")
        genai.configure(api_key=x_gemini_api_key.strip())
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")

    image_bytes_list = []
    for file in files:
        content = await file.read()
        image_bytes_list.append(content)

    logger.info("Received files for OCR upload", count=len(image_bytes_list), title=lesson_title)
    res = await ocr_service.process_images_and_index(image_bytes_list, lesson_title=lesson_title)
    return res

@router.post("/ocr", response_model=OCRResponse, summary="Index Raw Arabic Lesson Text")
@router.post("", response_model=OCRResponse, include_in_schema=False)
async def index_raw_text(request: RawTextIndexRequest, x_gemini_api_key: Optional[str] = Header(default=None)):
    if x_gemini_api_key and x_gemini_api_key.strip():
        genai.configure(api_key=x_gemini_api_key.strip())
    if not request.text_content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="text_content cannot be empty.")

    logger.info("Received raw text indexing request", title=request.lesson_title)
    res = await ocr_service.process_raw_text_and_index(request.text_content, lesson_title=request.lesson_title)
    return res
