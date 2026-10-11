from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.routes.chat import router as chat_router

app = FastAPI(title="AI Voice Assistant")

app.include_router(chat_router)


@app.get("/")
def root():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
