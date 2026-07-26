import os
import gradio as gr
from app.main import app as fastapi_app

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

# Mount FastAPI application onto Gradio demo
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio_app")

if __name__ == "__main__":
    demo.launch(ssr_mode=False)