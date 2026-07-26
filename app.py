import os
import gradio as gr
from app.main import app as fastapi_app

port = int(os.environ.get("PORT", 7860))

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

# Mount FastAPI app onto Gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=port, prevent_thread_lock=False)