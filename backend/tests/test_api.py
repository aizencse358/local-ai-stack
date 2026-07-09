import json


def parse_sse(text: str) -> list[dict | str]:
    events = []
    for frame in text.strip().split("\n\n"):
        if not frame.startswith("data: "):
            continue
        payload = frame[len("data: ") :]
        events.append(payload if payload == "[DONE]" else json.loads(payload))
    return events


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_document_ingest_list_delete(client, tmp_env, monkeypatch, fake_embed):
    monkeypatch.setattr(tmp_env, "embed", fake_embed)

    response = client.post(
        "/api/documents", files={"file": ("notes.txt", b"hello world " * 200, "text/plain")}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "notes.txt"
    assert body["chunk_count"] > 0

    listing = client.get("/api/documents").json()
    assert len(listing) == 1
    assert listing[0]["filename"] == "notes.txt"

    delete_response = client.delete(f"/api/documents/{body['document_id']}")
    assert delete_response.status_code == 204
    assert client.get("/api/documents").json() == []


def test_document_ingest_rejects_empty_file(client, tmp_env, monkeypatch, fake_embed):
    monkeypatch.setattr(tmp_env, "embed", fake_embed)

    response = client.post(
        "/api/documents", files={"file": ("empty.txt", b"   ", "text/plain")}
    )
    assert response.status_code == 400


def test_chat_creates_session_and_streams_tokens(client, tmp_env, monkeypatch, fake_stream_chat):
    monkeypatch.setattr(tmp_env, "stream_chat", fake_stream_chat)

    response = client.post(
        "/api/chat", json={"messages": [{"role": "user", "content": "Hello there"}]}
    )
    assert response.status_code == 200

    events = parse_sse(response.text)
    assert "session_id" in events[0]
    session_id = events[0]["session_id"]
    assert events[1:] == [{"token": "Hello"}, {"token": " there"}, "[DONE]"]

    sessions = client.get("/api/sessions").json()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_id
    assert sessions[0]["title"] == "Hello there"


def test_chat_follow_up_reuses_session(client, tmp_env, monkeypatch, fake_stream_chat):
    monkeypatch.setattr(tmp_env, "stream_chat", fake_stream_chat)

    first = client.post(
        "/api/chat", json={"messages": [{"role": "user", "content": "First message"}]}
    )
    session_id = parse_sse(first.text)[0]["session_id"]

    second = client.post(
        "/api/chat",
        json={
            "messages": [
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "Hello there"},
                {"role": "user", "content": "Follow up"},
            ],
            "session_id": session_id,
        },
    )
    assert parse_sse(second.text)[0]["session_id"] == session_id

    sessions = client.get("/api/sessions").json()
    assert len(sessions) == 1

    detail = client.get(f"/api/sessions/{session_id}").json()
    assert [m["role"] for m in detail["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]


def test_chat_with_rag_streams_and_persists_sources(
    client, tmp_env, monkeypatch, fake_embed, fake_stream_chat
):
    monkeypatch.setattr(tmp_env, "embed", fake_embed)
    monkeypatch.setattr(tmp_env, "stream_chat", fake_stream_chat)
    canned_hits = [{"filename": "doc.txt", "text": "relevant excerpt", "score": 0.87}]
    monkeypatch.setattr(tmp_env, "query", lambda embedding, top_k=4: canned_hits)

    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "What does the doc say?"}], "rag": True},
    )

    events = parse_sse(response.text)
    session_id = events[0]["session_id"]
    assert events[1]["sources"] == canned_hits

    detail = client.get(f"/api/sessions/{session_id}").json()
    assistant_message = detail["messages"][1]
    assert assistant_message["sources"] == canned_hits


def test_get_session_404_for_unknown_id(client):
    response = client.get("/api/sessions/does-not-exist")
    assert response.status_code == 404


def test_delete_session(client, tmp_env, monkeypatch, fake_stream_chat):
    monkeypatch.setattr(tmp_env, "stream_chat", fake_stream_chat)

    response = client.post(
        "/api/chat", json={"messages": [{"role": "user", "content": "hello"}]}
    )
    session_id = parse_sse(response.text)[0]["session_id"]

    delete_response = client.delete(f"/api/sessions/{session_id}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/sessions/{session_id}").status_code == 404
