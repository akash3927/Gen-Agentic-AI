# Project 02 — Prompt Laboratory

A beginner-friendly Prompt Engineering laboratory built with FastAPI, Pydantic, the direct OpenAI Python SDK, and a simple browser UI.

## What it includes

- Prompt templates with `{variables}` and immutable versions
- Playground with system instructions, model controls, rendered prompt, latency, and tokens
- Side-by-side prompt comparison
- Zero-shot, few-shot, role, contextual, and structured prompt examples
- Pydantic structured output (`CandidateAnalysis`)
- Five-case evaluation dataset and batch runner
- Basic JSON, keyword, response length, and non-empty checks
- JSON experiment history

## Architecture

The static browser UI calls FastAPI endpoints. Routes coordinate focused services for template rendering, direct OpenAI calls, evaluation, and JSON persistence. JSON was chosen for this learning project because records stay human-readable and no database setup hides the lifecycle. It is intended for one local server process.

```text
Browser UI → FastAPI → Prompt service → OpenAI Responses API
                         ↓                    ↓
                    JSON prompts       metrics/evaluation
                                              ↓
                                       JSON history
```

## Run

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Put your API key in `.env`, then run:

```bash
python -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. API documentation is at <http://127.0.0.1:8000/docs>.

Some reasoning models do not support `temperature`; leave the field blank for those models.

## Test

```bash
python -m pytest -q
```

Tests do not make a real OpenAI request.

## Important files

- `app/main.py` — FastAPI entry point
- `app/api/routes.py` — playground, comparison, batch, structured output, and history endpoints
- `app/services/llm_service.py` — visible `client.responses.create(...)` and `responses.parse(...)` calls
- `app/services/prompt_service.py` — prompt versions and variable rendering
- `app/services/evaluation_service.py` — intentionally basic checks
- `app/storage/json_store.py` — small local JSON persistence layer
- `app/static/index.html` — dependency-free UI
- `prompts/prompts.json` — inspectable prompt technique examples
- `datasets/evaluation.json` — five evaluation cases
- `storage/experiments.json` — generated experiment records

## Production improvements

For production, replace JSON files with a transactional database, add authentication and authorization, encrypt sensitive inputs, validate model allowlists, add rate limits/retries/observability, run batch calls with controlled concurrency, and move long jobs to a queue.
