import os
import gradio as gr
from app.main import app as fastapi_app

# ── Mount FastAPI into Gradio's internal server ───────────────────────────────
# Gradio serves port 7860 (the only port HF Spaces exposes)
# FastAPI is mounted at /api path so all /api/v1/* routes work
# Static files and root / are served by FastAPI through Gradio's server

with gr.Blocks(title="مولد الامتحانات العربي 📝") as demo:
    gr.HTML("""
    <div style="width:100%;height:96vh;margin:0;padding:0;">
      <iframe src="/static/index.html"
        style="width:100%;height:100%;border:none;display:block;">
      </iframe>
    </div>
    """)

# Mount the full FastAPI app onto Gradio at root path
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

# Launch Gradio - HF Spaces runs this file and proxies port 7860
# ssr_mode=False prevents Node.js SSR server from crashing the process
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    ssr_mode=False,
    show_error=True,
)