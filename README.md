# GenAI + Agentic AI Projects

A practical learning roadmap built one project at a time.

## Projects

1. [AI Voice Assistant](voice-ai-assistant/app/Readme.md) — text chat, transcription, and speech with FastAPI and OpenAI.
2. [Prompt Laboratory](prompt-lab/README.md) — create, version, run, compare, and evaluate prompts with visible metrics and structured outputs.
3. [PDF Knowledge Assistant](pdf-knowledge-assistant/README.md)
4. [Production RAG Assistant](production-rag-assistant/README.md)
5. [AI Tool-Using Assistant](ai-tool-using-assistant/README.md) — validated Python tools, live weather, local tasks, and visible tool-call traces.
6. [Autonomous Research Agent](autonomous-research-agent/README.md) — visible agent loop, research tools, approval, and sourced reports.
7. [Customer Support AI](customer-support-ai/README.md) — LangChain LCEL, sourced Chroma retrieval, support tools, confirmation, and a responsive React chat interface.

## How to learn from these projects

Read each project's purpose and learning goals, then follow its suggested reading order from the browser to the API and services. Start with voice and prompt basics, continue through semantic search and RAG, then explore tool calling, agent loops, and LangChain support flows. Brief code comments explain decisions such as chunk overlap, stream buffering, and approval boundaries.

## Code formatting

Run these commands from the repository root. Prettier formats JavaScript, JSX, CSS, HTML (including embedded scripts), JSON, and Markdown; Black formats Python. Their shared settings are in `.prettierrc.json` and `pyproject.toml`.

```bash
npx --yes prettier@3.6.2 --write "**/*.{js,jsx,css,html,json,md}"
python -m pip install black==25.1.0
python -m black .
```

To check formatting without editing files:

```bash
npx --yes prettier@3.6.2 --check "**/*.{js,jsx,css,html,json,md}"
python -m black --check .
```

Run each project's existing tests and frontend build after changing behavior. Keep comments focused on why a decision matters instead of describing every line.
