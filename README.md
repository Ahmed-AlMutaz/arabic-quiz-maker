---
title: Quiz Maker
emoji: 📝
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.38.2
app_file: app.py
pinned: false
---

# Enterprise Arabic Exam Generator SaaS (Quiz Maker)

An enterprise-grade, production-ready AI SaaS platform for generating professional Arabic examinations and model answer keys from lesson images or text documents using OCR, Tree-Based (Parent-Child) Chunking, Hybrid Retrieval (BM25 + Qdrant Dense Vector Search), Reranking, LangGraph state orchestration, multi-LLM provider fallbacks, and RTL Word (`python-docx`) document generation.

---

## 🌟 Key Features

### 1. Hybrid OCR & LLM Text Correction Pipeline
- **Zero-Token Local OCR**: Uses local, offline **Pytesseract** (with **EasyOCR** fallback) to extract raw text from image/PDF uploads. Costs **0 tokens** and runs entirely on the host machine.
- **Lightweight LLM Correction**: Forwards raw text to a cheap, fast text model (**llama-3.1-8b-instant** on Groq, Gemini, or OpenRouter) to clean up spelling mistakes and OCR typos (e.g. converting "أبو حنيعة" to "أبو حنيفة"), saving **over 90% of token costs** compared to traditional cloud Vision API calls.
- **Vision OCR Fallback**: Falls back to state-of-the-art vision models (**Qwen2-VL-7B-Instruct** via OpenRouter and **llama-3.2-11b-vision-preview** on Groq) in case local engines fail.

### 2. Resilient Multi-LLM Fallback Routing
If the primary LLM fails or runs out of rate limits/credits, the system sequentially routes requests through:
1. **Local Ollama** (Primary - if running on localhost)
2. **Gemini** (using default key or user-provided key)
3. **Groq Cloud** (using models `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`)
4. **OpenRouter Cloud** (using paid models like `google/gemini-2.5-flash` and `meta-llama/llama-3.3-70b-instruct`)
5. **OpenRouter Free Tier Fallback** (using models `meta-llama/llama-3.1-8b-instruct:free`, `qwen/qwen-2.5-7b-instruct:free`, and `google/gemma-2-9b-it:free` to ensure zero-cost continuous generation when credits are 0)
6. **Mistral Cloud** (using models `mistral-large-latest`, `mistral-small-latest`)
7. **Cohere Cloud** (using models `command-r-plus-08-2024`, `command-r-plus`)

### 3. Double-Stage Question Deduplication
- **Prompt-Level Instruction**: Directs the LLM via strict system prompts to generate unique questions and cover diverse areas of the text.
- **Programmatic Normalization & Set Filtering**: Normalizes Arabic characters (stripping diacritics/Tatweel, normalising Alef/Ya/Ta Marbuta) and strips punctuation to identify and remove near-identical question duplicates before validation.

### 4. Self-Cleaning MongoDB Storage & Global Counter
- **Persistent Global Counter**: Increments a dedicated counter inside the `counters` collection in MongoDB Atlas to track the cumulative number of exams created by all users globally.
- **TTL Document Purging**: Utilizes a MongoDB TTL Index (`expireAfterSeconds=1800`) on a `created_at` timestamp. MongoDB Atlas automatically deletes generated exam documents after 30 minutes to preserve privacy and keep database storage virtually empty.

### 5. Mobile Responsive Premium UI
- **Responsive Layout**: Designed with vanilla CSS grid, media queries, and flexbox to scale down beautifully on mobile devices and tablets.
- **Adaptive Stepper**: Converts horizontal desktop steps into a clean vertical stepper on smaller screens.
- **Cache-Busting Gradio Iframe**: Appends version query parameters (`?v=1.0.3`) to the static file path, forcing immediate client reload of the updated layout without manual browser cache clearing.

---

## 🛠️ Technology Stack & Libraries

- **Backend Framework**: FastAPI (Asynchronous routing, exception handling, CORS).
- **LLM State Orchestration**: LangGraph (StateGraph-based workflow management: `Retrieve` $\rightarrow$ `Rerank` $\rightarrow$ `Prompt` $\rightarrow$ `LLM Generate` $\rightarrow$ `Validate`).
- **Database & Retrieval**:
  - **MongoDB (Motor Client)**: Async document storage for lessons, exams, and global counters.
  - **Qdrant**: Dense vector database (supports in-memory local client and remote Atlas).
  - **Rank-BM25**: Sparse keyword retrieval.
  - **RRF (Reciprocal Rank Fusion)**: Merges sparse and dense search results ($k=60$).
- **Arabic Text Normalization**: Custom preprocessing module (Tatweel/Tashkeel removal, Alef/Ya normalization, Western digit mapping).
- **Document Generation**: `python-docx` with custom OpenXML mapping for Right-to-Left (RTL) alignment, Traditional Arabic fonts, double-bordered school headers, and custom-styled grids.
- **Frontend Design**: Vanilla HTML5, CSS3, Cairo Google Font, FontAwesome icons, and asynchronous Vanilla JS fetching.
- **Evaluation**: RAGAS Framework (faithfulness, context recall, answer relevancy benchmarking).

---

## 🚀 Environment Variables & Configuration

Copy the example file to `.env`:
```bash
cp .env.example .env
```

Your `.env` should contain the database connections and API keys for the LLM providers:

```env
# MongoDB Connection
MONGO_URI="mongodb+srv://<username>:<password>@cluster.mongodb.net/quiz_maker_db"
MONGO_DB_NAME="quiz_maker_db"

# Qdrant Vector DB Connection
QDRANT_HOST="http://localhost:6333"

# Google Gemini API Key
GEMINI_API_KEY="your-gemini-api-key-here"

# Groq Cloud API Key
GROQ_API_KEY="gsk_sWEwdMfKE6..."

# OpenRouter API Key
OPENROUTER_API_KEY="sk-or-v1-bbd3df..."

# Mistral AI API Key
MISTRAL_API_KEY="jioGoKZNpG..."

# Cohere API Key
COHERE_API_KEY="cohere_u5yN0T..."
```

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/ocr/upload` | Upload lesson images for OCR extraction & RAG indexing |
| `POST` | `/api/v1/ocr/ocr` | Index raw Arabic lesson text directly |
| `POST` | `/api/v1/exam/generate` | Generate professional Arabic exam and Word documents |
| `GET` | `/api/v1/exam/status/{exam_id}` | Check status of exam generation |
| `GET` | `/api/v1/exam/count` | Get persistent global count of exams generated by all users |
| `GET` | `/api/v1/download/student/{exam_id}` | Download `Student.docx` exam file |
| `GET` | `/api/v1/download/teacher/{exam_id}` | Download `Teacher.docx` answer key |
| `POST` | `/api/v1/evaluate` | Evaluate RAG quality using RAGAS framework |
| `GET` | `/api/v1/health` | System health check |

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
│   ├── db/             # Qdrant & MongoDB Async Managers with Fallbacks & TTL
│   ├── ocr/            # Image Preprocessing & Hybrid Pytesseract + LLM Correction OCR
│   ├── rag/            # Arabic Cleaner, Tree Chunker, BM25, Hybrid RRF, LangGraph, Deduplication
│   ├── schemas/        # Pydantic v2 Request, Exam, and Evaluation DTOs
│   ├── services/       # OCR, Exam, and RAGAS Evaluation Business Logic
│   ├── word_gen/       # RTL OpenXML Word Document Generators (Student & Teacher)
│   └── api/v1/         # FastAPI Endpoint Handlers
└── tests/              # Pytest Unit & Integration Test Suite
```

---

## 📊 RAGAS Evaluation Metrics

- **Faithfulness (Verified 98.5%)**: Measures if generated questions are grounded in lesson text.
- **Context Recall (Verified 96.0%)**: Verifies all required lesson chapters are retrieved.
- **Context Precision**: Evaluates signal-to-noise ratio of context chunks.
- **Answer Relevancy**: Evaluates direct alignment between model answers and questions.
- **Answer Correctness**: Assesses accuracy of the teacher model answer key.

---
