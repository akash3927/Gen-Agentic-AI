# Production RAG Assistant — Project 04

## What this project does

Answer questions using uploaded PDFs and show the retrieved evidence supporting each answer.

## What you will learn

- The difference between semantic search and retrieval-augmented generation.
- Query rewriting, similarity thresholds, reranking, and bounded source context.
- Grounded prompts, insufficient-evidence fallback, and frontend source displays.

## Suggested reading order

Follow `frontend/src/App.jsx` through `frontend/src/api.js` and `backend/app/api.py`, then read `backend/app/services/rag_service.py`. Short comments near key decisions explain why the implementation uses that approach.

A complete, framework-free retrieval-augmented generation application. Upload PDFs, retrieve relevant page-level chunks from ChromaDB, and generate grounded answers with inspectable sources. LangChain and LangGraph are deliberately not used.

## Visible RAG pipeline

```text
question
  → simple query rewrite
  → OpenAI query embedding
  → Chroma cosine retrieval + optional document filter
  → similarity threshold
  → vector/lexical reranking
  → bounded context construction
  → OpenAI Responses API
  → grounded answer + source chunks
```

When no chunk passes the configured threshold, the backend returns `I don't know based on the indexed documents.` and does not call the language model.

## Run the backend

Python 3.11+ is recommended.

```bash
cd production-rag-assistant/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example .env
# Add your OPENAI_API_KEY to .env
uvicorn app.main:app --reload
```

The API is at `http://localhost:8000`, with interactive documentation at `http://localhost:8000/docs`.

The default `gpt-5.4-mini` answer model and `text-embedding-3-small` embedding model can both be changed in `.env`. PDF files, registry metadata, and Chroma vectors are stored under `backend/data/` when the backend is launched from its directory.

## Run the frontend

```bash
cd production-rag-assistant/frontend
cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`.

## Run tests

```bash
cd production-rag-assistant/backend
source .venv/bin/activate
pytest
```

Tests use deterministic local embeddings, an in-memory Chroma database, and a fake language model. No test spends OpenAI credits.

## Retrieval controls

- **Top K:** maximum sources sent to the model and returned to the UI.
- **Similarity threshold:** chunks below this cosine similarity are discarded.
- **Document selection:** optional Chroma metadata filter by document ID.
- **Query rewrite:** a transparent deterministic cleanup before embedding.
- **Reranking:** 85% vector similarity plus 15% query-term overlap.

## API

| Method   | Endpoint                      | Purpose                                         |
| -------- | ----------------------------- | ----------------------------------------------- |
| `POST`   | `/api/documents`              | Upload and index a PDF                          |
| `GET`    | `/api/documents`              | List indexed PDFs                               |
| `DELETE` | `/api/documents/{id}`         | Delete a PDF and its vectors                    |
| `POST`   | `/api/documents/{id}/reindex` | Rebuild document chunks and vectors             |
| `POST`   | `/api/ask`                    | Retrieve context and generate a grounded answer |

Project 05 can build tool calling on top of this explicit RAG foundation.
