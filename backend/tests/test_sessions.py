def test_get_or_create_session_creates_new_session_with_title(tmp_env):
    import app.sessions as sessions

    session_id = sessions.get_or_create_session(None, "Hello world")

    all_sessions = sessions.list_sessions()
    assert len(all_sessions) == 1
    assert all_sessions[0]["id"] == session_id
    assert all_sessions[0]["title"] == "Hello world"


def test_title_truncated_with_ellipsis_over_60_chars(tmp_env):
    import app.sessions as sessions

    long_message = "x" * 80
    session_id = sessions.get_or_create_session(None, long_message)

    session = sessions.get_session(session_id)
    assert session["title"] == "x" * 60 + "…"


def test_get_or_create_session_reuses_existing_id(tmp_env):
    import app.sessions as sessions

    first_id = sessions.get_or_create_session(None, "first message")
    second_id = sessions.get_or_create_session(first_id, "follow up")

    assert second_id == first_id
    assert len(sessions.list_sessions()) == 1


def test_get_or_create_session_with_unknown_id_creates_new_row(tmp_env):
    import app.sessions as sessions

    new_id = sessions.get_or_create_session("does-not-exist", "hello")

    assert new_id != "does-not-exist"
    assert len(sessions.list_sessions()) == 1


def test_add_message_and_get_session_round_trip(tmp_env):
    import app.sessions as sessions

    session_id = sessions.get_or_create_session(None, "hello")
    sessions.add_message(session_id, "user", "hello")
    sessions.add_message(
        session_id,
        "assistant",
        "hi there",
        sources=[{"filename": "doc.txt", "text": "excerpt", "score": 0.9}],
    )

    session = sessions.get_session(session_id)

    assert session["messages"] == [
        {"role": "user", "content": "hello", "sources": None},
        {
            "role": "assistant",
            "content": "hi there",
            "sources": [{"filename": "doc.txt", "text": "excerpt", "score": 0.9}],
        },
    ]


def test_get_session_returns_none_for_unknown_id(tmp_env):
    import app.sessions as sessions

    assert sessions.get_session("does-not-exist") is None


def test_delete_session_cascades_to_messages(tmp_env):
    import app.sessions as sessions

    session_id = sessions.get_or_create_session(None, "hello")
    sessions.add_message(session_id, "user", "hello")

    sessions.delete_session(session_id)

    assert sessions.get_session(session_id) is None
    assert sessions.list_sessions() == []
