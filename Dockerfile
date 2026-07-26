# Dockerfile for Enterprise Arabic Exam SaaS (Quiz Maker)
FROM python:3.11-slim

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

# System dependencies for Tesseract OCR (Arabic + English) and OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies as root (ensures they are in system PATH)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create non-root user for security and copy source code
RUN useradd -m -u 1000 user
COPY --chown=user:user . .

# Create storage directory structure and set permissions
RUN mkdir -p /app/storage/temp /app/storage/exams && chown -R user:user /app/storage

# Switch to non-root user
USER user

# Expose port
EXPOSE 7860

# Run FastAPI application using Uvicorn on the dynamic port assigned by the host
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1