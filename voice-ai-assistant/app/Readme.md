# AI Voice Assistant

## What this project does

Record speech, convert it to text, generate a reply, and play synthesized audio. Text chat uses the same backend.

## What you will learn

- Browser microphone recording and uploading audio with FormData.
- FastAPI request models and separate speech-to-text, LLM, and text-to-speech services.
- Streaming text deltas and returning audio bytes to the browser.

## Suggested reading order

Start with `static/index.html`, follow `routes/chat.py`, then read `services/stt.py`, `services/llm.py`, and `services/tts.py`. Short comments near key decisions explain why the implementation uses that approach.

A small FastAPI app with text chat, microphone transcription, and spoken replies.

## Run locally

From the `voice-ai-assistant` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r app/requirement.txt
```

Add your API key to `app/.env`:

```text
OPENAI_API_KEY=your_key_here
```

Start the server:

```bash
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Microphone access works on localhost in modern browsers.
