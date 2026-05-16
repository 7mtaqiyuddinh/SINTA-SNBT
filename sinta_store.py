"""Offline SQLite storage for SINTA."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).with_name("sinta_offline.db")
MAX_STATE_HISTORY_MESSAGES = 20
MAX_MESSAGE_CHARS = 4000
MAX_STATE_TEXT_CHARS = 12000
EMPTY_JSON = "{}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate_text(value: Any, limit: int) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def _compact_state_value(value: Any) -> Any:
    if isinstance(value, str):
        return _truncate_text(value, MAX_STATE_TEXT_CHARS)
    if isinstance(value, dict):
        return {str(k): _compact_state_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_compact_state_value(item) for item in value[:50]]
    return value


def _compact_chat_history(history: Any) -> list[dict[str, Any]]:
    if not isinstance(history, list):
        return []

    compact: list[dict[str, Any]] = []
    for item in history[-MAX_STATE_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue
        compact.append(
            {
                "role": item.get("role", "user"),
                "content": _truncate_text(item.get("content", ""), MAX_MESSAGE_CHARS),
            }
        )
    return compact


def compact_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict):
        return {}

    keys = [
        "current_question",
        "question_options",
        "correct_answer",
        "question_explanation",
        "user_answer",
        "is_correct",
        "feedback",
        "score_delta",
        "recommendations",
        "weak_topics",
        "subject",
        "difficulty",
        "current_time",
        "total_correct",
        "total_wrong",
        "questions_asked",
        "intent",
        "model_metadata",
    ]
    compact = {key: _compact_state_value(state.get(key)) for key in keys if key in state}
    compact["chat_history"] = _compact_chat_history(state.get("chat_history", []))
    return compact


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                state_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agent TEXT,
                sources_json TEXT NOT NULL DEFAULT '[]',
                model_metadata_json TEXT NOT NULL DEFAULT '{}',
                web_used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                user_answer TEXT,
                correct_answer TEXT,
                is_correct INTEGER,
                explanation TEXT,
                subject TEXT,
                difficulty TEXT,
                raw_response TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
            """
        )
        _ensure_column(conn, "messages", "model_metadata_json", "model_metadata_json TEXT NOT NULL DEFAULT '{}'")
        conn.commit()


def ensure_default_project() -> int:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT id FROM projects ORDER BY id LIMIT 1").fetchone()
        if row:
            return int(row["id"])
        now = utc_now()
        cur = conn.execute(
            "INSERT INTO projects (name, created_at, updated_at) VALUES (?, ?, ?)",
            ("Proyek Utama", now, now),
        )
        project_id = int(cur.lastrowid)
        conn.execute(
            """
            INSERT INTO conversations (project_id, title, state_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, "Sesi Baru", "{}", now, now),
        )
        conn.commit()
        return project_id


def list_projects() -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT p.id, p.name, p.created_at, p.updated_at,
                   COUNT(c.id) AS conversation_count
            FROM projects p
            LEFT JOIN conversations c ON c.project_id = p.id
            GROUP BY p.id
            ORDER BY p.updated_at DESC, p.id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def create_project(name: str) -> int:
    init_db()
    now = utc_now()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO projects (name, created_at, updated_at) VALUES (?, ?, ?)",
            (name.strip(), now, now),
        )
        if cur.lastrowid:
            project_id = int(cur.lastrowid)
        else:
            row = conn.execute("SELECT id FROM projects WHERE name = ?", (name.strip(),)).fetchone()
            project_id = int(row["id"])
        conn.commit()
        return project_id


def rename_project(project_id: int, name: str) -> None:
    init_db()
    new_name = name.strip() or "Proyek Utama"
    now = utc_now()
    with _connect() as conn:
        conn.execute(
            "UPDATE projects SET name = ?, updated_at = ? WHERE id = ?",
            (new_name, now, project_id),
        )
        conn.commit()


def delete_project(project_id: int) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()


def reset_database(create_backup: bool = True) -> dict[str, Any]:
    init_db()
    backup_path = None
    if create_backup and DB_PATH.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = DB_PATH.with_name(f"{DB_PATH.stem}_backup_{stamp}{DB_PATH.suffix}")
        shutil.copy2(DB_PATH, backup_path)

    with _connect() as conn:
        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.executescript(
            """
            DELETE FROM quiz_attempts;
            DELETE FROM messages;
            DELETE FROM conversations;
            DELETE FROM projects;
            DELETE FROM sqlite_sequence WHERE name IN (
                'projects', 'conversations', 'messages', 'quiz_attempts'
            );
            """
        )
        conn.commit()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("VACUUM;")

    project_id = ensure_default_project()
    conversations = list_conversations(project_id)
    return {
        "backup_path": str(backup_path) if backup_path else None,
        "project_id": project_id,
        "conversation_id": conversations[0]["id"] if conversations else None,
    }


def list_conversations(project_id: int) -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.project_id, c.title, c.state_json, c.created_at, c.updated_at,
                   COUNT(m.id) AS message_count
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            WHERE c.project_id = ?
            GROUP BY c.id
            ORDER BY c.updated_at DESC, c.id DESC
            """,
            (project_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def create_conversation(project_id: int, title: str = "Sesi Baru") -> int:
    init_db()
    now = utc_now()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO conversations (project_id, title, state_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, title.strip() or "Sesi Baru", "{}", now, now),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_conversation(conversation_id: int) -> dict[str, Any] | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        return dict(row) if row else None


def set_conversation_state(conversation_id: int, state: dict[str, Any]) -> None:
    init_db()
    now = utc_now()
    compact = compact_state(state)
    state_json = json.dumps(compact, ensure_ascii=False)
    with _connect() as conn:
        conn.execute(
            "UPDATE conversations SET state_json = ?, updated_at = ? WHERE id = ?",
            (state_json, now, conversation_id),
        )
        conn.commit()


def get_conversation_state(conversation_id: int) -> dict[str, Any]:
    convo = get_conversation(conversation_id)
    if not convo:
        return {}
    try:
        return compact_state(json.loads(convo.get("state_json") or "{}"))
    except Exception:
        return {}


def rename_conversation(conversation_id: int, title: str) -> None:
    init_db()
    now = utc_now()
    with _connect() as conn:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title.strip() or "Sesi Baru", now, conversation_id),
        )
        conn.commit()


def delete_conversation(conversation_id: int) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()


def append_message(
    conversation_id: int,
    role: str,
    content: str,
    agent: str | None = None,
    sources: list[str] | None = None,
    web_used: bool = False,
    model_metadata: dict[str, Any] | None = None,
) -> int:
    init_db()
    now = utc_now()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO messages (
                conversation_id, role, content, agent, sources_json,
                model_metadata_json, web_used, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                role,
                content,
                agent,
                json.dumps(sources or [], ensure_ascii=False),
                json.dumps(model_metadata or {}, ensure_ascii=False),
                1 if web_used else 0,
                now,
            ),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_messages(conversation_id: int) -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, conversation_id, role, content, agent, sources_json,
                   model_metadata_json, web_used, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()
        output = []
        for row in rows:
            item = dict(row)
            try:
                item["sources"] = json.loads(item.pop("sources_json") or "[]")
            except Exception:
                item["sources"] = []
            try:
                item["model_metadata"] = json.loads(item.pop("model_metadata_json") or EMPTY_JSON)
            except Exception:
                item["model_metadata"] = {}
            item["web_used"] = bool(item["web_used"])
            output.append(item)
        return output


def save_quiz_attempt(
    conversation_id: int,
    question: str,
    user_answer: str | None,
    correct_answer: str | None,
    is_correct: bool | None,
    explanation: str | None,
    subject: str | None,
    difficulty: str | None,
    raw_response: str | None,
) -> int:
    init_db()
    now = utc_now()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO quiz_attempts (
                conversation_id, question, user_answer, correct_answer, is_correct,
                explanation, subject, difficulty, raw_response, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                question,
                user_answer,
                correct_answer,
                1 if is_correct else 0 if is_correct is not None else None,
                explanation,
                subject,
                difficulty,
                raw_response,
                now,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_quiz_attempts(conversation_id: int) -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM quiz_attempts
            WHERE conversation_id = ?
            ORDER BY id DESC
            """,
            (conversation_id,),
        ).fetchall()
        return [dict(row) for row in rows]
