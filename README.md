---
title: Quiz Maker
emoji: 📝
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.38.0
app_file: app.py
pinned: false
---
# Enterprise Arabic Exam Generator SaaS (Quiz Maker)

An enterprise-grade, production-ready AI SaaS platform for generating professional Arabic examinations and model answer keys from lesson images or text documents using OCR, Tree-Based (Parent-Child) Chunking, Hybrid Retrieval (BM25 + Qdrant Dense Vector Search), Reranking, LangGraph state orchestration, Gemini 1.5/2.0, and RTL Word (`python-docx`) document generation.

---

## 🌟 Key Features

- **Multi-Stage Arabic OCR**: Supports multi-image uploads (JPEG/PNG/PDF) with contrast enhancement, sharpening, and fallback to Gemini Vision OCR.
- **Arabic Text Normalization**: Tashkeel (diacritics) stripping, Tatweel (kashida) removal, Alef/Ya/Ta Marbuta normalization, and Western Arabic digit standardization.
- **Parent-Child Tree Chunking**: Preserves structural hierarchy (Lesson $\rightarrow$ Chapter/Section Parent ~1200 chars $\rightarrow$ Paragraph Child ~300 chars).
- **Hybrid Retrieval & RRF**: Combines BM25 sparse keyword search with Qdrant dense vector embeddings using Reciprocal Rank Fusion ($k=60$).
- **LangGraph RAG Workflow**: State-graph driven orchestration (`Retrieve` $\rightarrow$ `Rerank` $\rightarrow$ `Prompt` $\rightarrow$ `Gemini LLM` $\rightarrow$ `Validate`).
- **RTL Word Generation (`python-docx`)**:
  - `Student.docx`: Clean, printable A4 layout with school header, RTL alignment, Traditional Arabic typography, write-in lines.
  - `Teacher.docx`: Complete model answer key with explanations, marking rubrics, and parent chunk references.
- **RAGAS Evaluation Framework**: Automated evaluation of Faithfulness, Context Recall, Context Precision, Answer Relevancy, and Answer Correctness.
- **Production Architecture**: Built with FastAPI, Pydantic v2, Motor async MongoDB driver, Qdrant Client, Structured JSON logging, Docker containerization, and HuggingFace Spaces compatibility.

---

## 🚀 Quick Start

### 1. Prerequisites & Environment Setup
Clone the repository and configure `.env`:
```bash
cp .env.example .env
```
Ensure your `.env` contains your Gemini API key:
```env
GEMINI_API_KEY="your-gemini-api-key-here"
```

### 2. Run with Docker Compose (Recommended)
```bash
docker-compose up --build
```
Access the application at:
- **Web UI & OpenAPI Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc API Documentation**: `http://localhost:8000/redoc`

### 3. Run Locally with Python & Uvicorn
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
pytest -v
```

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/upload` | Upload lesson images for OCR extraction & RAG indexing |
| `POST` | `/api/v1/ocr` | Index raw Arabic lesson text directly |
| `POST` | `/api/v1/generate` | Generate professional Arabic exam and Word documents |
| `GET` | `/api/v1/status/{exam_id}` | Check status of exam generation |
| `GET` | `/api/v1/download/student/{exam_id}` | Download `Student.docx` exam file |
| `GET` | `/api/v1/download/teacher/{exam_id}` | Download `Teacher.docx` answer key |
| `POST` | `/api/v1/evaluate` | Evaluate RAG quality using RAGAS framework |
| `GET` | `/api/v1/health` | System health check |
| `GET` | `/api/v1/metrics` | System analytics and indexing metrics |

---

## 🏢 System Architecture

```
Quiz Maker/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app/
│   ├── main.py
│   ├── core/           # Settings, Security, Structured Logging, Exceptions
│   ├── db/             # Qdrant & MongoDB Async Managers with Fallbacks
│   ├── ocr/            # Image Preprocessing & Multi-stage Arabic OCR Engine
│   ├── rag/            # Arabic Cleaner, Tree Chunker, BM25, Hybrid RRF, LangGraph
│   ├── schemas/        # Pydantic v2 Request, Exam, and Evaluation DTOs
│   ├── services/       # OCR, Exam, and RAGAS Evaluation Business Logic
│   ├── word_gen/       # RTL OpenXML Word Document Generators (Student & Teacher)
│   └── api/v1/         # FastAPI Endpoint Handlers
└── tests/              # Pytest Unit & Integration Test Suite
```

---

## 📊 RAGAS Evaluation Metrics

- **Faithfulness**: Measures if generated questions are grounded in lesson text.
- **Context Recall**: Verifies all required lesson chapters are retrieved.
- **Context Precision**: Evaluates signal-to-noise ratio of context chunks.
- **Answer Relevancy**: Evaluates direct alignment between model answers and questions.
- **Answer Correctness**: Assesses accuracy of the teacher model answer key.

---
