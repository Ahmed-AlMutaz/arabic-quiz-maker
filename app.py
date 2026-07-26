import gradio as gr
from app.main import app as fastapi_app

print(">>> APP.PY LOADED <<<")

custom_css = """
body { direction: rtl; text-align: right; }
iframe { width: 100%; height: 950px; border: none; border-radius: 12px; }
"""

with gr.Blocks(title="Enterprise Arabic Exam SaaS", css=custom_css) as demo:
    gr.HTML(
        """
        <iframe src="/static/index.html"></iframe>
        """
    )

app = gr.mount_gradio_app(fastapi_app, demo, path="/")