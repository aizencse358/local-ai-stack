import asyncio

import app.rerank as rerank_module
from app.rerank import rerank

CANDIDATES = [
    {"filename": "a.txt", "text": "about cats", "score": 0.5},
    {"filename": "b.txt", "text": "about dogs", "score": 0.4},
    {"filename": "c.txt", "text": "about birds", "score": 0.3},
    {"filename": "d.txt", "text": "about fish", "score": 0.2},
]


def _fake_complete(response_text):
    async def _complete(prompt, model=None):
        return response_text

    return _complete


def test_valid_reordering(monkeypatch):
    monkeypatch.setattr(rerank_module, "complete", _fake_complete("[2, 0, 3, 1]"))

    result = asyncio.run(rerank("query", CANDIDATES, top_k=4))

    assert [c["filename"] for c in result] == ["c.txt", "a.txt", "d.txt", "b.txt"]


def test_truncates_to_top_k(monkeypatch):
    monkeypatch.setattr(rerank_module, "complete", _fake_complete("[2, 0, 3, 1]"))

    result = asyncio.run(rerank("query", CANDIDATES, top_k=2))

    assert [c["filename"] for c in result] == ["c.txt", "a.txt"]


def test_tolerates_markdown_fences_and_stray_text(monkeypatch):
    monkeypatch.setattr(
        rerank_module, "complete", _fake_complete("Sure, here you go:\n```json\n[1, 0, 2, 3]\n```")
    )

    result = asyncio.run(rerank("query", CANDIDATES, top_k=4))

    assert [c["filename"] for c in result] == ["b.txt", "a.txt", "c.txt", "d.txt"]


def test_falls_back_to_original_order_on_malformed_response(monkeypatch):
    monkeypatch.setattr(rerank_module, "complete", _fake_complete("not json at all"))

    result = asyncio.run(rerank("query", CANDIDATES, top_k=4))

    assert [c["filename"] for c in result] == ["a.txt", "b.txt", "c.txt", "d.txt"]


def test_falls_back_when_complete_raises(monkeypatch):
    async def _raise(prompt, model=None):
        raise RuntimeError("network error")

    monkeypatch.setattr(rerank_module, "complete", _raise)

    result = asyncio.run(rerank("query", CANDIDATES, top_k=3))

    assert [c["filename"] for c in result] == ["a.txt", "b.txt", "c.txt"]


def test_omitted_indices_appended_before_truncation(monkeypatch):
    monkeypatch.setattr(rerank_module, "complete", _fake_complete("[3]"))

    result = asyncio.run(rerank("query", CANDIDATES, top_k=4))

    assert [c["filename"] for c in result] == ["d.txt", "a.txt", "b.txt", "c.txt"]


def test_empty_candidates_returns_empty_without_calling_complete(monkeypatch):
    called = False

    async def _complete(prompt, model=None):
        nonlocal called
        called = True
        return "[]"

    monkeypatch.setattr(rerank_module, "complete", _complete)

    result = asyncio.run(rerank("query", [], top_k=4))

    assert result == []
    assert called is False
