from fastapi import Request, status
from fastapi.responses import JSONResponse

class QuizMakerException(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

class OCRError(QuizMakerException):
    def __init__(self, message: str):
        super().__init__(message, code="OCR_EXTRACTION_FAILED")

class RAGPipelineError(QuizMakerException):
    def __init__(self, message: str):
        super().__init__(message, code="RAG_PIPELINE_FAILED")

class DocumentGenerationError(QuizMakerException):
    def __init__(self, message: str):
        super().__init__(message, code="DOCX_GENERATION_FAILED")

async def quiz_maker_exception_handler(request: Request, exc: QuizMakerException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
