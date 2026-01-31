"""Conversation session management with SQLite storage."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TypedDict


class Message(TypedDict):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str


class SessionManager:
    """Manages conversation history in SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create database and tables if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id INTEGER PRIMARY KEY,
                    messages TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    last_notified_version TEXT
                )
            """)
            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def get_history(self, user_id: int) -> list[Message]:
        """Get conversation history for a user."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT messages FROM sessions WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()

            if row:
                return json.loads(row[0])
            return []

    def add_message(self, user_id: int, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            # Get existing messages
            cursor = conn.execute(
                "SELECT messages FROM sessions WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()

            if row:
                messages = json.loads(row[0])
            else:
                messages = []

            # Add new message
            messages.append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": now,
                }
            )

            # Update or insert
            if row:
                conn.execute(
                    "UPDATE sessions SET messages = ?, updated_at = ? WHERE user_id = ?",
                    (json.dumps(messages), now, user_id),
                )
            else:
                conn.execute(
                    "INSERT INTO sessions (user_id, messages, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (user_id, json.dumps(messages), now, now),
                )
            conn.commit()

    def clear_session(self, user_id: int) -> None:
        """Clear conversation history for a user."""
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET messages = '[]', updated_at = ? WHERE user_id = ?",
                (now, user_id),
            )
            conn.commit()

    def get_session_info(self, user_id: int) -> dict:
        """Get session metadata."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT messages, created_at, updated_at FROM sessions WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()

            if row:
                messages = json.loads(row[0])
                return {
                    "message_count": len(messages),
                    "created_at": row[1],
                    "updated_at": row[2],
                }
            return {
                "message_count": 0,
                "created_at": None,
                "updated_at": None,
            }

    def get_last_notified_version(self, user_id: int) -> str | None:
        """Get the last version the user was notified about."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT last_notified_version FROM user_settings WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def set_last_notified_version(self, user_id: int, version: str) -> None:
        """Set the last version the user was notified about."""
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO user_settings (user_id, last_notified_version)
                   VALUES (?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET last_notified_version = ?""",
                (user_id, version, version),
            )
            conn.commit()
