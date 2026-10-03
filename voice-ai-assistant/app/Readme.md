# AI Voice Assistant

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
