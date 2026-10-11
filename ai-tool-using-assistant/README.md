# Project 05 — AI Tool-Using Assistant

## What this project does

Answer chat messages and call validated Python tools for weather, arithmetic, orders, time, and local tasks.

## What you will learn

- Function schemas, Pydantic argument validation, and matching results with call IDs.
- Concurrent independent reads, sequential writes, and bounded tool rounds.
- React conversation state, backend-only credentials, tool traces, and SQLite persistence.

## Suggested reading order

Start with `frontend/src/main.jsx`, then read `backend/app/main.py`, `chat.py`, and `tools.py` in that order. Short comments near key decisions explain why the implementation uses that approach.

A direct FastAPI + React application with OpenAI function calling and ordinary Python functions. No LangChain, LangGraph, Agent SDK, background planner, or autonomous agent.

## Run locally

Use Python 3.11+ and Node 20.19+ (or Node 22.12+).

```bash
cd ai-tool-using-assistant/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Set OPENAI_API_KEY in .env. Optionally change OPENAI_MODEL.
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd ai-tool-using-assistant/frontend
npm ci
npm run dev
```

Open http://localhost:5173. The browser sends requests through Vite's `/api` proxy; the API key stays on the server. API documentation: http://localhost:8000/docs. The backend can start without a key, but chat returns an actionable 503 until configured.

## What to try

- “Explain a Python dictionary.” → ordinary answer, no tool necessary.
- “What is the weather in Pune?” → live external weather.
- “What time is it in Asia/Kolkata?” → local clock.
- “Calculate (1499 + 799) \* 0.9 and show orders for Asha.” → independent reads.
- “Find order ORD-1001, then calculate its total after a 10% discount.” → dependent sequential rounds.
- “Create a task titled Review Project 05 with note Run the tests.” → validated SQLite write.
- “List my tasks.” → persistent local tasks.
- “Calculate 1 / 0.” → visible tool error returned to the model.

## Visible lifecycle

`user → React → FastAPI → model → proposed call → Pydantic validation → Python execution → tool result → model → final answer`

`app/tools.py` defines the allowlisted registry, Pydantic schemas, tool functions and dispatcher. `app/chat.py` passes those schemas to the Responses API, preserves model output items, and returns each result using its `call_id`. `app/main.py` validates chat requests and manages the async SDK client. The React UI displays arguments, lifecycle stages, results, errors and round numbers after the full response completes; it does not stream execution events.

There are at most three tool rounds, eight calls per round, and one final synthesis request with tools disabled. Independent read calls within one round use `asyncio.gather`; writes execute one at a time after reads. Calls in later rounds can depend on earlier results. This bounded exchange supports sequential tool calling without autonomous goal planning or background continuation.

## Tools and safeguards

| Tool            | Data            | Validation / behavior                                                                 |
| --------------- | --------------- | ------------------------------------------------------------------------------------- |
| `calculate`     | Local           | AST allowlist, length/node/numeric limits; no eval, imports, powers or arbitrary code |
| `get_weather`   | Live Open-Meteo | Bounded city text, fixed HTTPS endpoints, geocoding then current forecast             |
| `current_time`  | Local           | Validated IANA timezone                                                               |
| `search_orders` | Mock orders     | Bounded query; mock records explicitly labeled                                        |
| `create_task`   | SQLite          | Nonempty bounded title, bounded note, no extra fields, parameterized INSERT           |
| `list_tasks`    | SQLite          | No arguments, most recent 100 tasks                                                   |

Every call starts as a proposal. Server-side strict Pydantic validation runs before any function executes, including writes. Invalid, unknown and failed calls become structured tool results; one failed read does not abort the batch. Each tool has an eight-second budget, HTTP requests have five-second timeouts, and model requests have a 45-second budget with SDK retries disabled. Writes commit synchronously without detached background work.

The model is instructed to create tasks only on explicit user requests. This is a local learning application: validation constrains the operation, but it is not an authorization or user confirmation system. There is no authentication, per-user storage, or production deployment hardening. Anyone with backend access can use the shared task database. Keep it on localhost. SQLite stores tasks across restarts; chat history lives in the current browser state and only the most recent 29 messages are submitted. Do not put secrets in messages. Submitted messages and tool results are sent to OpenAI with `store=False`.

Open-Meteo requires network access; unavailable cities, HTTP errors and timeouts appear as tool failures. Current weather is model-based weather data. Ambiguous names use the first geocoding result, with resolved city/country shown in the result. Attribution: [Open-Meteo](https://open-meteo.com/), [weather API documentation](https://open-meteo.com/en/docs). Function-call implementation follows [official OpenAI documentation](https://developers.openai.com/api/docs/guides/function-calling).

## Tests

```bash
cd ai-tool-using-assistant/backend
source .venv/bin/activate
python -m pytest -q
```

Tests use scripted model responses and mocked HTTP, without an API key or network. They verify schema exposure, routing, validation before execution, safe arithmetic, SQLite persistence, no-tool replies, tool failure results, parallel reads, sequential writes, dependent rounds, round limits, weather handling, and HTTP validation. They verify the application protocol, not probabilistic live-model selection accuracy. Use the prompts above for a live smoke test with your own key.

```bash
cd ai-tool-using-assistant/frontend
npm run build
```

Project 06 can introduce agentic planning separately.
