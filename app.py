import os
import time
import threading
import uvicorn
import gradio as gr
from app.main import app as fastapi_app

PORT = int(os.environ.get("PORT", 7860))
GRADIO_PORT = PORT + 1  # e.g. 7861 for Gradio wrapper

def run_fastapi():
    uvicorn.run(fastapi_app, host="127.0.0.1", port=PORT, log_level="warning")

fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
fastapi_thread.start()
time.sleep(4)

with gr.Blocks(title="Arabic Quiz Maker") as demo:
    gr.HTML(f"""
    <iframe src="http://127.0.0.1:{PORT}/"
        style="width:100%;height:96vh;border:none;display:block;">
    </iframe>
    """)

demo.launch(server_name="0.0.0.0", server_port=GRADIO_PORT, ssr_mode=False)