# Construction Document RAG Platform

Production-grade Retrieval-Augmented Generation (RAG) backend for construction and architectural documents. The system ingests PDFs, extracts text (native text + OCR fallback), builds per-document vector indexes, and answers questions with citations.

## What’s included

- FastAPI backend with async DB (SQLAlchemy) and clean routing (`/v1/...`)
- Hybrid extraction: native PDF text (PyMuPDF) + optional Google Vision OCR
- Embeddings + FAISS vector index persisted per document
- Optional reranking (SentenceTransformers CrossEncoder when configured)
- LLM provider abstraction: Anthropic (Claude) and OpenAI
- Structured logging, consistent error responses, and environment-based config
- Docker + docker-compose for deployment

## Quickstart (local)

Prereqs:
- Python 3.12+
- Poppler (for `pdf2image` when OCR is enabled)
  - Ubuntu/Debian: `sudo apt-get install poppler-utils`

Install:
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env
```

Run API:
```bash
uvicorn construction_rag.api.main:app --host 0.0.0.0 --port 8000
```

API docs:
- Swagger: `http://localhost:8000/docs`

## OCR configuration

`OCR_MODE`:
- `text_only`: extract embedded PDF text only (fast, no credentials)
- `google_vision`: force OCR for all pages (requires Google credentials)
- `auto`: use embedded text first; fallback to OCR when pages are mostly empty

To enable Google Vision OCR:
- Set `GOOGLE_APPLICATION_CREDENTIALS` to a service account JSON path.

## Embeddings configuration

This backend uses OpenAI embeddings (FAISS index over normalized vectors).
- Set `OPENAI_API_KEY`
- Choose `EMBEDDING_MODEL` (default: `text-embedding-3-small`)

## Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Frontend (optional)

Streamlit UI is provided as a thin client:
```bash
streamlit run frontend/streamlit_app.py
```

## Repository layout

- `construction_rag/` – application package (API, services, DB, core)
- `frontend/` – optional Streamlit UI
- `docker/` – Dockerfile + compose
- `requirements/` – dependency groups
