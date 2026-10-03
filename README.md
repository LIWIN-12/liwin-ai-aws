# Liwin AI

Liwin AI is a personal portfolio assistant. It answers questions about J. K. Liwin Jose from Markdown files in `knowledge/`, using Gemini embeddings, ChromaDB retrieval, conversational memory, and a FastAPI-served web chat.

## What it does

1. `python -m backend.ingest` reads the Markdown knowledge base, splits it into bounded chunks, and stores 768-dimensional Gemini embeddings in ChromaDB.
2. `/chat` embeds the visitor's question, retrieves the relevant chunks, includes the current session's recent history, and generates a response.
3. Gemini is the default generation provider. OpenRouter and Groq are optional, ordered fallbacks that must be enabled deliberately.

The public web UI is served by FastAPI at `/`. `frontend/streamlit_app.py` is an optional client for local development; it is not the production UI.

## Requirements

- Python 3.11 or newer
- A Gemini API key with access to `gemini-embedding-001` and the configured generation model
- Internet access while indexing and answering questions

## One-time setup

Windows PowerShell:

```powershell
cd C:\Users\LIWIN\Documents\about_me\liwin-ai
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `.env`. Do not commit this file. The default generation model is `gemini-3.8-flash`; if your Gemini account does not support it, set `GEMINI_GENERATION_MODEL` to a model that is available to your key and verify it before deployment.

Build the local vector index once:

```powershell
python -m backend.ingest
```

This command keeps the existing collection until a new staging collection has been fully embedded and verified. Re-run it after changing any Markdown file in `knowledge/`.

## Daily run

```powershell
cd C:\Users\LIWIN\Documents\about_me\liwin-ai
.\venv\Scripts\Activate.ps1
uvicorn backend.app:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Confirm the service and index state with:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

`knowledge_base` should be `ready` and `document_count` should be greater than zero.

## Configuration

Copy `.env.example` and change only what your deployment needs.

| Variable | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Required for embeddings and default text generation. |
| `GEMINI_EMBEDDING_MODEL` | Defaults to `gemini-embedding-001`. |
| `GEMINI_EMBEDDING_DIMENSIONS` | Defaults to `768`; do not change without rebuilding the index. |
| `GEMINI_GENERATION_MODEL` | Default Gemini text model. |
| `LLM_PROVIDERS` | Ordered, comma-separated providers. Defaults to `gemini,openrouter,groq`. |
| `OPENROUTER_API_KEY`, `GROQ_API_KEY` | Required only when their provider is named in `LLM_PROVIDERS`. |
| `CHROMA_PATH`, `MEMORY_DB_PATH` | Persistent storage locations. |
| `ALLOWED_ORIGINS` | Comma-separated origins for a separately hosted frontend. |
| `MEMORY_RETENTION_DAYS` | Automatic SQLite history retention; defaults to 30 days. |
| `MAX_CONTEXT_CHARACTERS` | Maximum retrieved reference text passed to the model; defaults to 8,000 for responsive answers. |

Using `LLM_PROVIDERS=gemini,openrouter,groq` sends the assembled portfolio prompt to each fallback provider when earlier providers fail. Enable that only if it is acceptable for your deployment.

## Testing and checks

The test suite has no live API dependency:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q backend
node --check frontend\js\app.js
```

For a live retrieval check after indexing:

```powershell
python -c "from backend.rag import search; print(len(search('Tell me about Smart Focus')))"
```

## Docker

Build and run with persistent local directories mounted for both ChromaDB and chat memory:

```powershell
docker build -t liwin-ai .
docker run --rm -p 7860:7860 `
  --env-file .env `
  -e CHROMA_PATH=/data/chroma_db `
  -e MEMORY_DB_PATH=/data/liwin_memory.db `
  -v "${PWD}\runtime-data:/data" `
  liwin-ai
```

On first boot, the container creates an empty index only when none exists. It does not reindex changed knowledge files automatically; run `python -m backend.ingest` as a deliberate maintenance operation.

## Render deployment

`backend/render.yaml` expects a persistent disk mounted at `/var/data`. It bootstraps an empty index on first start, after the `GEMINI_API_KEY` secret is available. Set the API key in Render's secret environment settings, then deploy a single web instance.

The built-in request limiter and SQLite memory are process-local. For multiple instances or public traffic at scale, use an upstream rate limiter and a shared, managed database/vector store before scaling out.

## Privacy and security notes

- The chat stores recent anonymous session messages in SQLite. Starting a new conversation asks the server to delete the prior session; remaining history is purged after the configured retention period.
- Do not place private information in the Markdown knowledge base unless every configured generation provider is approved to receive it.
- The API sets browser security headers, accepts only bounded question and session inputs, and uses same-origin requests by default.
- Keep `.env`, `chroma_db/`, and `liwin_memory.db` out of source control.

## Project layout

```text
backend/        FastAPI app, RAG, indexing, LLM providers, and memory
frontend/       Static production UI and optional Streamlit client
knowledge/      Source Markdown for the portfolio assistant
tests/          Offline unit and API integration tests
```
