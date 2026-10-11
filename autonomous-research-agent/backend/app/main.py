from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .agent import DemoPlanner, OpenAIPlanner, run, stop
from .models import Start, State

load_dotenv()
runs: dict[str, State] = {}
jobs: dict[str, asyncio.Task] = {}
planners = {}


@asynccontextmanager
async def lifespan(app):
    yield
    tasks = list(jobs.values())
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(title="Autonomous Research Agent", lifespan=lifespan)


def get(run_id):
    if run_id not in runs:
        raise HTTPException(404, "Research run not found")
    return runs[run_id]


def launch(state, approved=None):
    async def work():
        try:
            # A wall-clock deadline applies to each active segment, excluding human wait.
            await asyncio.wait_for(run(state, planners[state.id], approved), 300)
        except asyncio.TimeoutError:
            stop(state, "Run segment timed out")

    jobs[state.id] = asyncio.create_task(work())


@app.post("/api/runs", status_code=201)
async def start(request: Start):
    if len(runs) >= 100:
        raise HTTPException(429, "Run capacity reached; restart the local server")
    try:
        planner = DemoPlanner() if request.demo else OpenAIPlanner()
    except Exception:
        raise HTTPException(503, "Set OPENAI_API_KEY in backend/.env or use demo mode")
    state = State(**request.model_dump())
    runs[state.id], planners[state.id] = state, planner
    launch(state)
    return state.model_dump()


@app.get("/api/runs/{run_id}")
async def read(run_id: str):
    return get(run_id).model_dump()


class Approval(BaseModel):
    approved: bool


@app.post("/api/runs/{run_id}/approval")
async def approve(run_id: str, request: Approval):
    state = get(run_id)
    if state.status != "awaiting_approval" or not jobs[run_id].done():
        raise HTTPException(409, "Run is not ready for approval")
    state.status = (
        "running"  # Claim synchronously to prevent duplicate approvals/writes.
    )
    launch(state, request.approved)
    return state.model_dump()


@app.post("/api/runs/{run_id}/stop")
async def cancel(run_id: str):
    state = get(run_id)
    if state.status in ("completed", "failed", "stopped"):
        return state.model_dump()
    jobs[run_id].cancel()
    await asyncio.gather(jobs[run_id], return_exceptions=True)
    state.pending = None
    stop(state, "Stopped by user")
    return state.model_dump()
