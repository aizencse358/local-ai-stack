import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.ollama_client import stream_chat
from app.schemas import ChatMessage, ChatRequest

app = FastAPI(title="Local AI Stack Backend")

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    messages = list(request.messages)

    system_parts = []
    if request.system:
        system_parts.append(request.system)
    if request.context:
        system_parts.append(
            "Use the following document to answer the user's questions. "
            "If the answer isn't in the document, say so instead of guessing.\n\n"
            f"---\n{request.context}\n---"
        )
    if system_parts:
        messages.insert(0, ChatMessage(role="system", content="\n\n".join(system_parts)))

    return StreamingResponse(
        stream_chat(messages, model=request.model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
