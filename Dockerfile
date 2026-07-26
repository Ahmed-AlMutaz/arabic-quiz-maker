# Dockerfile for Enterprise Arabic Exam SaaS (Quiz Maker)
FROM python:3.11-slim AS base

# System dependencies for OCR (Tesseract Arabic), OpenCV, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition
COPY requirements.txt .

# Install CPU-only PyTorch first to keep Docker image lightweight
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app/
COPY README.md .

# Create storage directory structure
RUN mkdir -p /app/storage/temp /app/storage/exams

# Expose port (8000 for FastAPI / HuggingFace Spaces standard 7860)
EXPOSE 7860

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=7860

# Run application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
