# Dockerfile for Enterprise Arabic Exam SaaS (Quiz Maker)
FROM python:3.11-slim AS base

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PORT=7860

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

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application source code & files
COPY . .

# Create storage directory structure with non-root write permissions
RUN mkdir -p /app/storage/temp /app/storage/exams && chmod -R 777 /app/storage

# Expose Hugging Face Spaces standard port
EXPOSE 7860

# Run application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]