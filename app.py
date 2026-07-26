import os
import uvicorn
from app.main import app

port = int(os.environ.get("PORT", 7860))

print(f"Starting Enterprise Arabic Exam SaaS on port {port}...")
uvicorn.run(app, host="0.0.0.0", port=port)
