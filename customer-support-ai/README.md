# Project 07 — Customer Support AI

Northstar is a responsive support desk built with React, Vite, Tailwind, FastAPI, Pydantic and LangChain. No LangGraph is used.

## Run locally

Use **Python 3.11+** and **Node 20.19+**. From this directory:

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements-dev.txt
cp backend/.env.example backend/.env
cd backend
.venv/bin/uvicorn app.main:app --reload
```

In another terminal, from the repository root:

```bash
cd customer-support-ai/frontend
npm install
npm run dev
```

Open http://localhost:5173. API docs: http://localhost:8000/docs.

Without an API key, the app runs in **demo mode**: deterministic LCEL routing, hashed offline embeddings, real Chroma retrieval, canned policy answers and mock tools. Demo streaming is simulated word-by-word. Demo mode is not an LLM and its routing is intentionally simple. Add `OPENAI_API_KEY` to `backend/.env`, then restart for structured model routing, OpenAI embeddings and model token streaming. Policies are embedded on startup; OpenAI mode incurs API usage. Demo and live collections are separate.

Try “What is your refund policy?”, “Where is order 12345?”, “Cancel it”, “Refund order 67890”, and “Create a support ticket for a damaged item”. Order 12345 is processing; 67890 is delivered.

## Visible LangChain flows

`backend/app/engine.py` keeps the learning paths explicit:

- **Routing:** `ChatPromptTemplate → ChatOpenAI.with_structured_output(Route)` returns a validated Pydantic decision. Demo routing uses `RunnableLambda → Pydantic validation`.
- **Answering:** `ChatPromptTemplate → model → StrOutputParser`, consumed with `astream`.
- **RAG:** `Document → RecursiveCharacterTextSplitter → embeddings → Chroma → retriever.ainvoke → numbered context → answer chain`. Source events carry titles, document IDs and full retrieved chunks.
- **Tools:** `StructuredTool.from_function` with Pydantic argument schemas. Python dispatch is deliberately explicit rather than an autonomous agent loop.
- **Confirmation:** cancel/refund only create a proposal token. A separate endpoint validates conversation ownership, expires it after ten minutes, consumes the token once and checks current order eligibility before mutating mock data. Declining does not mutate the order.

Compared with Projects 03–06, LangChain wraps the manual prompt formatting, model calls, text parsing, chunking, vector-store access and tool argument validation. Ordinary Python still owns request routing, session state and approval boundaries, so each abstraction remains inspectable.

The API streams newline-delimited JSON: `route`, `sources`, `tool`, `confirmation`, `delta`, `done`, or `error`. Frontend services parse chunks without assuming network chunk boundaries equal event boundaries.

## Tests

```bash
cd backend
.venv/bin/python -m pytest -q
cd ../frontend
npm test
npm run build
```

Backend tests run without keys: LCEL, structured routing, retrieval/citations, tool schemas, history/follow-ups, invalid orders, API streaming and confirmation ownership/replay/eligibility. Frontend tests cover composer/loading states, sources, tool status, drawer navigation, API errors and split/interrupted streams.

For viewport QA check 1440px, 768px and 390px: desktop sidebar, tablet/mobile drawer, full-width message flow and accessible fixed composer. The dialog uses native modal focus containment, explicit labels, Escape decline and keyboard focus cycling. Enter sends; Shift+Enter adds a line.

## Learning-project boundaries

Orders, tickets, conversations and pending confirmations are in memory and reset when the backend restarts. Chroma persists to `backend/data/chroma`. Conversation history stays in the UI during the current tab session. Run one backend worker. This demo assumes one mock customer and has no authentication; add authenticated customer ownership, durable storage, rate limiting and an external commerce integration before deploying. Retrieved documents are trusted bundled policies. Demo embeddings use lexical overlap, not semantic understanding; live retrieval uses OpenAI embeddings. Live API behavior requires a configured key and is not exercised by offline tests.

## Verified locally

8 backend tests and 6 frontend tests pass; the production frontend builds. Browser checks at 1440px, 768px and 390px verified sourced policy answers, confirmed mock cancellation, mobile drawer navigation, no document horizontal overflow and an accessible composer. OpenAI calls were not run.
