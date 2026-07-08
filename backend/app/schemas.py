from typing import Literal, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: Optional[str] = None
    system: Optional[str] = None
    context: Optional[str] = None
    rag: Optional[bool] = False


class RetrievedChunk(BaseModel):
    filename: str
    text: str
    score: float


class DocumentInfo(BaseModel):
    id: str
    filename: str
    chunk_count: int


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
