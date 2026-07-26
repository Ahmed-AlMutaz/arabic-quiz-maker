import os
import gradio as gr
from app.main import app as fastapi_app

# Create a Gradio container for Hugging Face Spaces integration
with gr.Blocks(title="Enterprise Arabic Exam SaaS") as demo:
    gr.HTML(
        '''
        <iframe src="/static/index.html" style="width: 100%; height: 950px; border: none; overflow: auto;"></iframe>
        '''
    )

app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    import uvicorn
    print(f"Starting Enterprise Arabic Exam SaaS on port {port}...")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
