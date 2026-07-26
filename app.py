import os
import gradio as gr
from app.main import app as fastapi_app

port = int(os.environ.get("PORT", 7860))

# Create a Gradio interface wrapper for Hugging Face Spaces integration
with gr.Blocks(title="Enterprise Arabic Exam SaaS") as demo:
    gr.HTML(
        '''
        <iframe src="/static/index.html" style="width: 100%; height: 950px; border: none; overflow: auto;"></iframe>
        '''
    )

# Mount FastAPI app into Gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

# Launch Gradio server on 0.0.0.0:7860 (keeps Python process running permanently)
demo.launch(server_name="0.0.0.0", server_port=port)
