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


async def _chat_stream(request: ChatRequest):
    messages = list(request.messages)

    system_parts = []
    if request.system:
        system_parts.append(request.system)

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

    async for chunk in stream_chat(messages, model=request.model):
        yield chunk


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
