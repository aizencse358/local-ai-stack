import json
import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.chunking import chunk_text
from app.ollama_client import embed, stream_chat
from app.schemas import (
    ChatMessage,
    ChatRequest,
    DocumentInfo,
    IngestResponse,
    SessionDetail,
    SessionInfo,
)
from app.sessions import (
    add_message,
    delete_session,
    get_or_create_session,
    get_session,
    list_sessions,
)
from app.vectorstore import add_document, delete_document, list_documents, query

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


@app.post("/api/documents", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)) -> IngestResponse:
    raw = (await file.read()).decode("utf-8", errors="ignore")
    chunks = chunk_text(raw)
    if not chunks:
        raise HTTPException(status_code=400, detail="Document is empty after chunking")

    embeddings = await embed(chunks)
    document_id = add_document(file.filename, chunks, embeddings)
    return IngestResponse(document_id=document_id, filename=file.filename, chunk_count=len(chunks))


@app.get("/api/documents", response_model=list[DocumentInfo])
async def get_documents() -> list[DocumentInfo]:
    return [DocumentInfo(**doc) for doc in list_documents()]


@app.delete("/api/documents/{document_id}", status_code=204)
async def remove_document(document_id: str) -> None:
    delete_document(document_id)


@app.get("/api/sessions", response_model=list[SessionInfo])
async def get_sessions() -> list[SessionInfo]:
    return [SessionInfo(**s) for s in list_sessions()]


@app.get("/api/sessions/{session_id}", response_model=SessionDetail)
async def get_session_detail(session_id: str) -> SessionDetail:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDetail(**session)


@app.delete("/api/sessions/{session_id}", status_code=204)
async def remove_session(session_id: str) -> None:
    delete_session(session_id)


async def _chat_stream(request: ChatRequest):
    messages = list(request.messages)

    session_id = get_or_create_session(request.session_id, request.messages[-1].content)
    add_message(session_id, "user", request.messages[-1].content)
    yield f"data: {json.dumps({'session_id': session_id})}\n\n"

    system_parts = []
    if request.system:
        system_parts.append(request.system)

    hits = []
    if request.rag and request.messages:
        user_query = request.messages[-1].content
        query_embedding = (await embed([user_query]))[0]
        hits = query(query_embedding, top_k=4)
        if hits:
            yield f"data: {json.dumps({'sources': hits})}\n\n"
            excerpt_text = "\n\n".join(f"[{hit['filename']}]\n{hit['text']}" for hit in hits)
            system_parts.append(
                "Use the following retrieved excerpts to answer the user's question. "
                "If the answer isn't in the excerpts, say so instead of guessing.\n\n"
                f"---\n{excerpt_text}\n---"
            )

    if request.context:
        system_parts.append(
            "Use the following document to answer the user's questions. "
            "If the answer isn't in the document, say so instead of guessing.\n\n"
            f"---\n{request.context}\n---"
        )

    if system_parts:
        messages.insert(0, ChatMessage(role="system", content="\n\n".join(system_parts)))

    assistant_text = ""
    async for chunk in stream_chat(messages, model=request.model):
        if chunk.startswith("data: ") and chunk.strip() != "data: [DONE]":
            payload = json.loads(chunk[len("data: ") :])
            assistant_text += payload.get("token", "")
        yield chunk

    add_message(session_id, "assistant", assistant_text, sources=hits or None)


@app.post("/api/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _chat_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
