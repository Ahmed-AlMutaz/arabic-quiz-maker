import os
import gradio as gr
import spaces
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.core.exceptions import QuizMakerException, quiz_maker_exception_handler

# Dummy function to satisfy ZeroGPU validator on Hugging Face Spaces startup
@spaces.GPU
def dummy_gpu_validator():
    return None

custom_css = """
body { direction: rtl; text-align: right; margin: 0; padding: 0; }
iframe { width: 100%; height: 96vh; border: none; display: block; }
"""

with gr.Blocks(title="مولد الامتحانات العربي 📝", css=custom_css) as demo:
    gr.HTML("""
    <div style="width:100%;height:96vh;margin:0;padding:0;overflow:hidden;">
      <iframe src="/app-static/index.html?v=1.0.3" style="width:100%;height:100%;border:none;display:block;"></iframe>
    </div>
    """)

# Monkey-patch Gradio's App.create_app to inject custom FastAPI routes
# into the actual running FastAPI app instance.
from gradio.routes import App
original_create_app = App.create_app

def patched_create_app(*args, **kwargs):
    # Call original create_app to let Gradio build the FastAPI app instance
    app = original_create_app(*args, **kwargs)
    
    # Mount our custom static files and API router on this actual app instance
    static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
    app.mount("/app-static", StaticFiles(directory=static_dir), name="app-static")
    app.include_router(api_router, prefix="/api/v1")
    
    # Add healthcheck route
    @app.get("/health", include_in_schema=False)
    async def health_check():
        return JSONResponse(content={"status": "ok"}, status_code=200)
        
    # Reorder routes so our custom routes are at the beginning
    # to prevent shadowing by Gradio's catch-all route handlers
    our_routes = []
    other_routes = []
    for r in app.router.routes:
        if hasattr(r, "path") and (r.path.startswith("/app-static") or r.path.startswith("/api/v1") or r.path == "/health"):
            our_routes.append(r)
        else:
            other_routes.append(r)
    app.router.routes = our_routes + other_routes

    # Add CORS Middleware to the app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom exception handler to the app
    app.add_exception_handler(QuizMakerException, quiz_maker_exception_handler)

    return app

# Apply monkey patch!
App.create_app = patched_create_app

if __name__ == "__main__":
    demo.launch(ssr_mode=False)