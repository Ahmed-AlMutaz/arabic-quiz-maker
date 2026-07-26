import os
import gradio as gr
import uvicorn
from app.main import app as fastapi_app

# ─── Mount Gradio onto FastAPI ────────────────────────────────────────────────
# Gradio is served at /gradio path, FastAPI owns the root (static UI + API)
with gr.Blocks(title="Arabic Quiz Maker - مولد الامتحانات") as demo:
    gr.HTML("""
    <div style="width:100%;height:96vh;margin:0;padding:0;overflow:hidden;">
        <iframe src="/"
            style="width:100%;height:100%;border:none;display:block;"
            allow="camera;microphone;clipboard-write">
        </iframe>
    </div>
    """)

# Mount Gradio onto FastAPI at /gradio path
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

# ─── Start Server ─────────────────────────────────────────────────────────────
# HF Spaces Gradio SDK runs `python app.py` - we run uvicorn here at top level
# so it blocks and keeps the process alive on port 7860
port = int(os.environ.get("PORT", 7860))
uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")