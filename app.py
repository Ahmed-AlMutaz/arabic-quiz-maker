import gradio as gr
from app.main import app as fastapi_app

print(">>> APP.PY LOADED <<<")

with gr.Blocks(title="Enterprise Arabic Exam SaaS") as demo:
    gr.HTML(
        """
        <iframe src="/static/index.html"
                style="width:100%;height:950px;border:none;">
        </iframe>
        """
    )

app = gr.mount_gradio_app(fastapi_app, demo, path="/")