# PDF Knowledge Assistant — Project 03

A learning-focused semantic PDF search application. It extracts text with PyPDF, creates overlapping chunks, requests embeddings directly from OpenAI, stores vectors in ChromaDB, and returns the most similar source chunks. It does **not** generate answers with an LLM.

## Architecture

```text
frontend/ (React + Vite)
        │ upload / search / manage
        ▼
backend/ (FastAPI)
        ├── PyPDF page extraction
        ├── explicit character chunking
        ├── OpenAI Embeddings API
        ├── ChromaDB cosine search
        └── JSON document registry + stored PDFs
```

## Run the backend

Python 3.11+ is recommended.

```bash
cd pdf-knowledge-assistant/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example .env
# Put your OpenAI API key in .env
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`; interactive docs are at `http://localhost:8000/docs`.

Paths in `.env` are resolved from the directory where the backend is started. The default setup stores uploaded PDFs, the JSON registry, and the persistent Chroma database under `backend/data/`.

## Run the frontend

In another terminal:

```bash
cd pdf-knowledge-assistant/frontend
cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`.

## Run tests

```bash
cd pdf-knowledge-assistant/backend
source .venv/bin/activate
pytest
```

Tests replace OpenAI with deterministic embeddings and use Chroma's in-memory client. They cover extraction, page metadata, chunk overlap, the full embedding/search flow, document management, invalid PDFs, and PDFs without extractable text.

## API summary

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/documents` | Upload and index a PDF; accepts `chunk_size` and `chunk_overlap` form fields |
| `GET` | `/api/documents` | List indexed PDFs |
| `DELETE` | `/api/documents/{id}` | Delete a PDF and its vectors |
| `POST` | `/api/documents/{id}/reindex` | Rebuild vectors, optionally with new chunk settings |
| `POST` | `/api/search` | Embed a query and return Top-K source chunks |

The search response contains similarity score, chunk text, PDF name, page number, document ID, and chunk index.
