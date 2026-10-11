# Project 06 — Autonomous Research Agent

## What this project does

Work toward a research goal through repeated decisions and tool observations, with visible plans and approval before saving notes.

## What you will learn

- How an agent loop differs from a single tool-calling exchange.
- State feedback, step/token limits, cancellation, and pause/resume approval.
- Research tools, collected sources, and React polling with effect cleanup.

## Suggested reading order

Start with `frontend/src/main.jsx`, follow `backend/app/main.py`, then trace `run()` in `backend/app/agent.py` and the tools in `tools.py`. Short comments near key decisions explain why the implementation uses that approach.

Python/FastAPI + Pydantic + OpenAI Python SDK, with React/Vite and simple CSS. No agent framework or multi-agent architecture.

## Run locally

Use Python 3.12+ and Node 20.19+ (or 22.12+).

```bash
cd autonomous-research-agent/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8006 --reload
```

In another terminal:

```bash
cd autonomous-research-agent/frontend
npm ci
npm run dev
```

Open the URL printed by Vite. Offline demo is selected by default: enter any goal, watch multiple iterations, approve or reject saving notes, and inspect the final illustrative report. Set maximum steps to 2 to see safe termination. Demo findings are explicitly fictional examples, not research about the entered goal.

For live research, configure `OPENAI_API_KEY`, `OPENAI_MODEL`, and `BRAVE_SEARCH_API_KEY` in `backend/.env`, then uncheck Offline demo. The model defaults to `gpt-4.1-mini`; choose an available Responses structured-output model. Search uses Brave's web search endpoint. Keys stay on the backend. Optional input/output dollar rates per million tokens enable a usage-based estimate; configure rates for your chosen model. No guessed pricing is displayed.

## Read the loop

Start with [`backend/app/agent.py`](backend/app/agent.py), especially `run()`:

1. Check step and token limits before calling the LLM.
2. Send goal, current plan, past steps, observations, available tools, and remaining steps to `OpenAIPlanner.decide()`.
3. Parse a Pydantic `Decision`: updated task plan, a public action summary, one tool and JSON arguments, or a final report.
4. Validate tool arguments against its Pydantic model.
5. Pause before `save_notes`. The exact proposed content is shown for human approval. Rejection is an observation; approval executes the saved decision without another LLM call.
6. Execute one tool. Record results or errors and collect source URLs.
7. Repeat: the next decision sees these observations and can change the plan.
8. Finish on a report, or stop on step/token limits, timeout, user stop, or model failure. A stopped run includes partial observations and sources.

This uses the SDK's Responses structured parsing to produce a decision; Python dispatches it. It deliberately does not delegate control to an agent SDK. See [official OpenAI function calling documentation](https://developers.openai.com/api/docs/guides/function-calling) for the underlying model/tool/observation cycle.

## Tools and reliability

- `web_search`: up to five Brave results with bounded snippets. Search snippets are labeled separately from pages read.
- `read_page`: public HTTPS HTML only, no automatic redirects, private/reserved DNS addresses blocked, 1 MB body limit, 10,000-character text cap. Standard-library HTML parser removes script/style/navigation text. Redirecting URLs must be replaced with a final canonical URL.
- `calculator`: bounded arithmetic AST; no `eval`, code execution, powers, or function calls.
- `save_notes`: approval required on every write. Appends to `backend/data/notes/<server-generated-run-id>.md` by default.

Tool arguments reject unexpected fields. Network tools have per-request and overall timeouts, and one retry for transient connection errors/429/selected 5xx responses. Writes and validation errors are not retried. OpenAI requests have a 30-second timeout and one SDK retry. Each active run segment has a 300-second deadline; human approval time is excluded. Every LLM decision counts toward the maximum, including malformed tool arguments. The last allowed tool finishes its execution, then the loop stops before another paid call.

Usage counters reflect successful model responses. A conservative next-call token reserve includes context bytes, decision schema, instructions, and output allowance; it may stop early. This is an application guard, not a provider billing cap. Failed provider requests may still incur usage unavailable to this app. Sources collected by tools are appended to every completed report. Model prose citations are prompted but not independently verified.

## API

- `POST /api/runs`: `{ "goal": "...", "max_steps": 12, "token_budget": 24000, "demo": false }`
- `GET /api/runs/{id}`: current plan, steps, observations, notes, sources, report, status, usage, pending approval.
- `POST /api/runs/{id}/approval`: `{ "approved": true }` or false; duplicate/stale approvals return 409.
- `POST /api/runs/{id}/stop`: cancel the active task safely.

The UI polls while running. API documentation is at `http://127.0.0.1:8006/docs`.

## Tests

```bash
cd autonomous-research-agent/backend
source .venv/bin/activate
python -m pytest tests -q
```

Tests require no credentials or external network. They cover the loop, state feedback, successful completion, calculation, failures, invalid arguments, max steps, token guards, timeout, retry, private URL rejection, approval/rejection, demo mode, and API approval conflicts.

```bash
cd autonomous-research-agent/frontend
npm run build
```

## Local-demo boundaries

Runs are kept in memory and disappear on backend restart; approved note files persist. Run at most one backend worker. There is a 100-run capacity per process. This is a local learning app without authentication; bind to localhost. Public-URL validation is a basic guard, not a production SSRF boundary (DNS rebinding requires a controlled outbound proxy or pinned DNS transport). Web content is passed as untrusted evidence, but prompt injection remains possible. Live quality depends on provider availability, source quality, and model behavior. No live paid-provider run is part of the offline tests.
