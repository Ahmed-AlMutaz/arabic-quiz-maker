import os
import uvicorn
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

# Mount Gradio demo onto FastAPI app
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"Starting Enterprise Arabic Exam SaaS on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)