import json
import os
import sqlite3
import uuid

DB_PATH = os.getenv("SQLITE_DB_PATH", "./chat_history.db")

_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row
_conn.execute("PRAGMA foreign_keys = ON")
_conn.executescript(
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        sources TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
    """
)
_conn.commit()


def _make_title(first_message: str) -> str:
    text = first_message.strip()
    return text[:60] + "…" if len(text) > 60 else text


def get_or_create_session(session_id: str | None, first_message: str) -> str:
    if session_id:
        row = _conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row:
            return session_id

    new_id = str(uuid.uuid4())
    _conn.execute(
        "INSERT INTO sessions (id, title) VALUES (?, ?)",
        (new_id, _make_title(first_message)),
    )
    _conn.commit()
    return new_id


def add_message(
    session_id: str, role: str, content: str, sources: list[dict] | None = None
) -> None:
    _conn.execute(
        "INSERT INTO messages (session_id, role, content, sources) VALUES (?, ?, ?, ?)",
        (session_id, role, content, json.dumps(sources) if sources else None),
    )
    _conn.commit()


def list_sessions() -> list[dict]:
    rows = _conn.execute(
        "SELECT id, title, created_at FROM sessions ORDER BY created_at DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def get_session(session_id: str) -> dict | None:
    session_row = _conn.execute(
        "SELECT id, title, created_at FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    if not session_row:
        return None

    message_rows = _conn.execute(
        "SELECT role, content, sources FROM messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,),
    ).fetchall()

    messages = [
        {
            "role": row["role"],
            "content": row["content"],
            "sources": json.loads(row["sources"]) if row["sources"] else None,
        }
        for row in message_rows
    ]

    return {**dict(session_row), "messages": messages}


def delete_session(session_id: str) -> None:
    _conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    _conn.commit()
