# Local AI Integration Stack — Streaming Chat UI

A foundational project for learning how local LLMs, a backend server, and a
frontend UI wire together end-to-end.

## Stack

- **Ollama** — local LLM runtime
- **FastAPI** — backend middleware (prompts, streaming, context)
- **React + TypeScript (Vite)** — frontend chat UI (token-by-token rendering)

## Milestone 1: Streaming Chat UI

React sends a message to FastAPI, FastAPI forwards it to Ollama and streams
the response back over Server-Sent Events (SSE), and React renders tokens
as they arrive.

| Waiting for a response | Streamed response |
| --- | --- |
| ![Typing indicator](docs/screenshots/typing-indicator.png) | ![Chat response](docs/screenshots/chat-response.png) |

## Running with Docker

```bash
docker compose up --build
```

Then pull a model into the running Ollama container:

```bash
docker compose exec ollama ollama pull llama3.2
```

Backend will be available at `http://localhost:8000`, with a health check at
`GET /api/health` and streaming chat at `POST /api/chat`.

## Running the backend locally (without Docker)

Uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
cd backend
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

Requires Ollama running locally on `localhost:11434` with a model pulled
(`ollama pull llama3.2`).

## Running the frontend locally

Requires Node 18+.

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend will be available at `http://localhost:5173` and expects the
backend at `http://localhost:8000` (configurable via `VITE_BACKEND_URL`).

## `POST /api/chat`

```json
{
  "messages": [{ "role": "user", "content": "hello" }],
  "system": "optional system prompt",
  "model": "llama3.2"
}
```

Response is `text/event-stream`, each event a JSON payload:
`data: {"token": "..."}\n\n`, terminated by `data: [DONE]\n\n`.

## Roadmap

- [x] Streaming Chat UI
- [x] System prompt field (persona/instructions)
- [ ] Paste document content into system prompt (basic Knowledge Q&A)
- [ ] Proper RAG with chunking + embeddings (`nomic-embed-text` + ChromaDB/FAISS)
