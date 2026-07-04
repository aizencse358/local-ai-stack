import json
import os
from collections.abc import AsyncIterator
from typing import Optional

import httpx

from app.schemas import ChatMessage

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


async def stream_chat(
    messages: list[ChatMessage], model: Optional[str] = None
) -> AsyncIterator[str]:
    """Stream a chat completion from Ollama as SSE-formatted chunks."""
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [m.model_dump() for m in messages],
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST", f"{OLLAMA_URL}/api/chat", json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                chunk = json.loads(line)

                if chunk.get("done"):
                    yield "data: [DONE]\n\n"
                    break

                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"
