import importlib
import json
from collections.abc import AsyncIterator

import pytest
from starlette.testclient import TestClient


@pytest.fixture
def tmp_env(monkeypatch, tmp_path):
    """Point sessions/vectorstore at fresh, isolated storage and reload
    the modules (including main, which binds their functions at import
    time) so each test starts from a clean slate."""
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))

    import app.sessions as sessions
    import app.vectorstore as vectorstore
    import app.main as main

    importlib.reload(sessions)
    importlib.reload(vectorstore)
    importlib.reload(main)

    yield main


@pytest.fixture
def client(tmp_env):
    return TestClient(tmp_env.app)


@pytest.fixture
def fake_embed():
    async def _fake_embed(texts: list[str], model: str | None = None) -> list[list[float]]:
        return [[1.0, 0.0, 0.0] for _ in texts]

    return _fake_embed


@pytest.fixture
def fake_stream_chat():
    async def _fake_stream_chat(messages, model=None) -> AsyncIterator[str]:
        yield f"data: {json.dumps({'token': 'Hello'})}\n\n"
        yield f"data: {json.dumps({'token': ' there'})}\n\n"
        yield "data: [DONE]\n\n"

    return _fake_stream_chat
