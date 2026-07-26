import os
import gradio as gr
from app.main import app as fastapi_app

custom_css = """
body { direction: rtl; text-align: right; }
iframe { width: 100%; height: 950px; border: none; border-radius: 12px; }
"""

with gr.Blocks(title="Enterprise Arabic Exam SaaS", css=custom_css) as demo:
    gr.HTML(
        '''
        <iframe src="/static/index.html"></iframe>
        '''
    )

# Mount FastAPI application onto Gradio demo
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio_app")

# Standard Gradio launch for Hugging Face Spaces
if __name__ == "__main__":
    demo.launch()