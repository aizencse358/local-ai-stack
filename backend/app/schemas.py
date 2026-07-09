from typing import Literal, Optional

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    filename: str
    text: str
    score: float


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    sources: Optional[list[RetrievedChunk]] = None


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: Optional[str] = None
    system: Optional[str] = None
    context: Optional[str] = None
    rag: Optional[bool] = False
    session_id: Optional[str] = None


class DocumentInfo(BaseModel):
    id: str
    filename: str
    chunk_count: int


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int


class SessionInfo(BaseModel):
    id: str
    title: str
    created_at: str


class SessionDetail(BaseModel):
    id: str
    title: str
    created_at: str
    messages: list[ChatMessage]
