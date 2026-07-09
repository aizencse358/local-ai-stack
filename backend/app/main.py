import json
import os
import time

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.chunking import chunk_text
from app.extract import extract_text
from app.observability import configure_logging, logger
from app.ollama_client import embed, list_models, stream_chat
from app.rerank import rerank
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

configure_logging()

app = FastAPI(title="Local AI Stack Backend")

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(
        "event=request method=%s path=%s status=%d duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/models", response_model=list[str])
async def get_models() -> list[str]:
    return await list_models()


@app.post("/api/documents", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)) -> IngestResponse:
    start = time.perf_counter()

    raw = await file.read()
    try:
        text = extract_text(file.filename, raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Document is empty after chunking")

    embeddings = await embed(chunks)
    document_id = add_document(file.filename, chunks, embeddings)

    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(
        "event=document_ingested filename=%s chunk_count=%d duration_ms=%s",
        file.filename,
        len(chunks),
        duration_ms,
    )

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
    start = time.perf_counter()
    ttft_ms = None
    token_count = 0

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
        candidates = query(query_embedding, top_k=10)
        hits = await rerank(user_query, candidates, top_k=4)
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
            token = payload.get("token", "")
            assistant_text += token
            if token:
                token_count += 1
                if ttft_ms is None:
                    ttft_ms = round((time.perf_counter() - start) * 1000, 1)
        yield chunk

    add_message(session_id, "assistant", assistant_text, sources=hits or None)

    total_ms = round((time.perf_counter() - start) * 1000, 1)
    top_score = round(hits[0]["score"], 3) if hits else None
    logger.info(
        "event=chat_completed session_id=%s model=%s rag=%s hit_count=%d top_score=%s "
        "ttft_ms=%s total_ms=%s tokens=%d",
        session_id,
        request.model or "default",
        request.rag,
        len(hits),
        top_score,
        ttft_ms,
        total_ms,
        token_count,
    )


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
