import os
from contextlib import asynccontextmanager
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .chat import chat

load_dotenv()


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: list[Message] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def ends_with_user(self):
        if self.messages[-1].role != "user":
            raise ValueError("Last message must be from the user")
        return self


@asynccontextmanager
async def lifespan(app):
    app.state.client = (
        AsyncOpenAI(timeout=40, max_retries=0) if os.getenv("OPENAI_API_KEY") else None
    )
    yield
    if app.state.client:
        await app.state.client.close()


app = FastAPI(title="AI Tool-Using Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "configured": app.state.client is not None}


@app.post("/api/chat")
async def ask(request: ChatRequest):
    if app.state.client is None:
        raise HTTPException(
            503, "Set OPENAI_API_KEY in backend/.env and restart the backend"
        )
    try:
        return await chat(
            app.state.client,
            os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            request.messages,
        )
    except Exception:
        raise HTTPException(
            502,
            "Model request failed or timed out. Check server configuration and retry.",
        ) from None
