import logging


def test_request_logs_method_path_status_and_duration(client, caplog):
    with caplog.at_level(logging.INFO):
        response = client.get("/api/health")

    assert response.status_code == 200
    record = next(r for r in caplog.records if "event=request" in r.getMessage())
    assert "method=GET" in record.getMessage()
    assert "path=/api/health" in record.getMessage()
    assert "status=200" in record.getMessage()
    assert "duration_ms=" in record.getMessage()


def test_chat_completed_log_without_rag(client, tmp_env, monkeypatch, fake_stream_chat, caplog):
    monkeypatch.setattr(tmp_env, "stream_chat", fake_stream_chat)

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/chat", json={"messages": [{"role": "user", "content": "hi"}]}
        )

    assert response.status_code == 200
    record = next(r for r in caplog.records if "event=chat_completed" in r.getMessage())
    assert "rag=False" in record.getMessage()
    assert "hit_count=0" in record.getMessage()
    assert "top_score=None" in record.getMessage()
    assert "tokens=2" in record.getMessage()
    assert "ttft_ms=" in record.getMessage()
    assert "total_ms=" in record.getMessage()


def test_chat_completed_log_with_rag(
    client, tmp_env, monkeypatch, fake_embed, fake_stream_chat, caplog
):
    monkeypatch.setattr(tmp_env, "embed", fake_embed)
    monkeypatch.setattr(tmp_env, "stream_chat", fake_stream_chat)
    canned_hits = [{"filename": "doc.txt", "text": "relevant excerpt", "score": 0.87}]
    monkeypatch.setattr(tmp_env, "query", lambda embedding, top_k=10: canned_hits)

    async def fake_rerank(query, candidates, top_k=4):
        return candidates[:top_k]

    monkeypatch.setattr(tmp_env, "rerank", fake_rerank)

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "What does the doc say?"}], "rag": True},
        )

    assert response.status_code == 200
    record = next(r for r in caplog.records if "event=chat_completed" in r.getMessage())
    assert "rag=True" in record.getMessage()
    assert "hit_count=1" in record.getMessage()
    assert "top_score=0.87" in record.getMessage()


def test_document_ingested_log(client, tmp_env, monkeypatch, fake_embed, caplog):
    monkeypatch.setattr(tmp_env, "embed", fake_embed)

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/documents", files={"file": ("notes.txt", b"hello world " * 200, "text/plain")}
        )

    assert response.status_code == 200
    record = next(r for r in caplog.records if "event=document_ingested" in r.getMessage())
    assert "filename=notes.txt" in record.getMessage()
    assert f"chunk_count={response.json()['chunk_count']}" in record.getMessage()
    assert "duration_ms=" in record.getMessage()
