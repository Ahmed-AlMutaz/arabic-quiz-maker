import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.exceptions import QuizMakerException, quiz_maker_exception_handler
from app.api.v1.router import api_router


print(">>> MAIN.PY LOADED <<<")

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.DEBUG)
    logger.info("Starting Enterprise Arabic Exam SaaS (Quiz Maker)", env=settings.ENV)
    yield
    logger.info("Shutting down Enterprise Arabic Exam SaaS service")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-Grade AI SaaS Platform for Generating Professional Arabic Exams from Lesson Images",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handler
app.add_exception_handler(QuizMakerException, quiz_maker_exception_handler)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Static Files Directory Setup
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Health check & Root endpoint مضمون 100% لـ Hugging Face Spaces
@app.get("/", include_in_schema=False)
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Quiz Maker AI Engine Live</h1>", status_code=200)

# إضافة مسار خاص للـ Healthcheck صراحة
@app.get("/health", include_in_schema=False)
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)

if __name__ == "__main__": 
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)