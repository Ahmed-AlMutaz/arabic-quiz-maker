import os
import gradio as gr
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.core.exceptions import QuizMakerException, quiz_maker_exception_handler

custom_css = """
body { direction: rtl; text-align: right; }
iframe { width: 100%; height: 950px; border: none; border-radius: 12px; }
"""

with gr.Blocks(title="مولد الامتحانات العربي 📝", css=custom_css) as demo:
    gr.HTML("""
    <div style="width:100%;height:96vh;margin:0;padding:0;">
      <iframe src="/static/index.html"
        style="width:100%;height:100%;border:none;display:block;">
      </iframe>
    </div>
    """)

# Mount FastAPI app components onto Gradio's underlying FastAPI app instance
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
demo.app.mount("/static", StaticFiles(directory=static_dir), name="static")
demo.app.include_router(api_router, prefix="/api/v1")

# Add CORS Middleware to Gradio's FastAPI instance
demo.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom exception handler
demo.app.add_exception_handler(QuizMakerException, quiz_maker_exception_handler)

# Add healthcheck route for Hugging Face Space & Railway
@demo.app.get("/health", include_in_schema=False)
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)

if __name__ == "__main__":
    demo.launch(ssr_mode=False)