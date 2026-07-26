# Dockerfile for Enterprise Arabic Exam SaaS (Quiz Maker)
# Optimized for Hugging Face Spaces Docker SDK - CPU Basic (Free)
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

# Create non-root user for security
RUN useradd -m -u 1000 user
USER user

WORKDIR /app

# Copy and install Python dependencies (no torch - not needed)
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy all application source code
COPY --chown=user:user . .

# Create storage directory structure
RUN mkdir -p /app/storage/temp /app/storage/exams

# Expose Hugging Face Spaces standard port
EXPOSE 7860

# Run FastAPI application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]