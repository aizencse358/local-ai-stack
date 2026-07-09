import asyncio
import json

import httpx


def _patch_async_client(monkeypatch, module, handler):
    """Make module.httpx.AsyncClient(...) build a client wired to a
    MockTransport, regardless of the kwargs the real code passes."""
    real_async_client = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs.pop("timeout", None)
        return real_async_client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(module.httpx, "AsyncClient", fake_async_client)


def test_embed_returns_vectors_and_sends_expected_payload(monkeypatch):
    import app.ollama_client as ollama_client

    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    _patch_async_client(monkeypatch, ollama_client, handler)

    result = asyncio.run(ollama_client.embed(["a", "b"]))

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    assert captured["url"].endswith("/api/embed")
    assert captured["body"] == {"model": ollama_client.EMBED_MODEL, "input": ["a", "b"]}


def test_stream_chat_yields_sse_tokens_then_done(monkeypatch):
    import app.ollama_client as ollama_client
    from app.schemas import ChatMessage

    ndjson = (
        json.dumps({"message": {"content": "Hi"}}) + "\n"
        + json.dumps({"message": {"content": " there"}}) + "\n"
        + json.dumps({"done": True}) + "\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=ndjson.encode())

    _patch_async_client(monkeypatch, ollama_client, handler)

    async def collect():
        chunks = []
        async for chunk in ollama_client.stream_chat([ChatMessage(role="user", content="hi")]):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(collect())

    assert chunks == [
        f"data: {json.dumps({'token': 'Hi'})}\n\n",
        f"data: {json.dumps({'token': ' there'})}\n\n",
        "data: [DONE]\n\n",
    ]


def test_complete_returns_full_text_and_sends_non_streaming_payload(monkeypatch):
    import app.ollama_client as ollama_client

    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"message": {"content": "the answer"}})

    _patch_async_client(monkeypatch, ollama_client, handler)

    result = asyncio.run(ollama_client.complete("rank these"))

    assert result == "the answer"
    assert captured["body"]["stream"] is False
    assert captured["body"]["messages"] == [{"role": "user", "content": "rank these"}]
    assert captured["body"]["model"] == ollama_client.DEFAULT_MODEL
