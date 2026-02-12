"""SQLite database wrapper for the chat application."""

import sqlite3
import threading
from datetime import datetime, timedelta, timezone

from shared.constants import DEFAULT_CHANNEL, SESSION_EXPIRY_HOURS


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self):
        with self._lock:
            conn = self._get_conn()
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS users (
                        id            INTEGER PRIMARY KEY AUTOINCREMENT,
                        username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                        password_hash TEXT    NOT NULL,
                        created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
                    );

                    CREATE TABLE IF NOT EXISTS channels (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        name        TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                        description TEXT    DEFAULT '',
                        created_by  INTEGER REFERENCES users(id),
                        created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
                    );

                    CREATE TABLE IF NOT EXISTS messages (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id  INTEGER NOT NULL REFERENCES channels(id),
                        user_id     INTEGER NOT NULL REFERENCES users(id),
                        content     TEXT    NOT NULL,
                        msg_type    TEXT    NOT NULL DEFAULT 'message',
                        created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
                    );

                    CREATE INDEX IF NOT EXISTS idx_messages_channel_time
                        ON messages(channel_id, created_at);

                    CREATE TABLE IF NOT EXISTS sessions (
                        token       TEXT    PRIMARY KEY,
                        user_id     INTEGER NOT NULL REFERENCES users(id),
                        created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                        expires_at  TEXT    NOT NULL
                    );
                """)
                # Seed default channel
                conn.execute(
                    "INSERT OR IGNORE INTO channels (name, description) VALUES (?, ?)",
                    (DEFAULT_CHANNEL, "General discussion"),
                )
                conn.commit()
            finally:
                conn.close()

    # --- Users ---

    def create_user(self, username: str, password_hash: str) -> bool:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
            finally:
                conn.close()

    def get_user_by_username(self, username: str) -> dict | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT id, username, password_hash, created_at FROM users WHERE username = ? COLLATE NOCASE",
                (username,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # --- Channels ---

    def create_channel(self, name: str, description: str, created_by: int) -> int | None:
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.execute(
                    "INSERT INTO channels (name, description, created_by) VALUES (?, ?, ?)",
                    (name, description, created_by),
                )
                conn.commit()
                return cur.lastrowid
            except sqlite3.IntegrityError:
                return None
            finally:
                conn.close()

    def get_channel_by_name(self, name: str) -> dict | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT id, name, description, created_by, created_at FROM channels WHERE name = ? COLLATE NOCASE",
                (name,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_channels(self) -> list[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT id, name, description FROM channels ORDER BY name"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # --- Messages ---

    def save_message(self, channel_id: int, user_id: int, content: str, msg_type: str = "message") -> int:
        with self._lock:
            conn = self._get_conn()
            try:
                cur = conn.execute(
                    "INSERT INTO messages (channel_id, user_id, content, msg_type) VALUES (?, ?, ?, ?)",
                    (channel_id, user_id, content, msg_type),
                )
                conn.commit()
                return cur.lastrowid
            finally:
                conn.close()

    def get_message_history(self, channel_id: int, limit: int = 50) -> list[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT m.id, m.content, m.msg_type, m.created_at, u.username
                   FROM messages m
                   JOIN users u ON m.user_id = u.id
                   WHERE m.channel_id = ?
                   ORDER BY m.created_at DESC
                   LIMIT ?""",
                (channel_id, limit),
            ).fetchall()
            # Return in chronological order
            return [dict(r) for r in reversed(rows)]
        finally:
            conn.close()

    # --- Sessions ---

    def create_session(self, token: str, user_id: int):
        expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_EXPIRY_HOURS)
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
                    (token, user_id, expires.isoformat()),
                )
                conn.commit()
            finally:
                conn.close()

    def validate_session(self, token: str) -> int | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT user_id, expires_at FROM sessions WHERE token = ?",
                (token,),
            ).fetchone()
            if not row:
                return None
            expires = datetime.fromisoformat(row["expires_at"])
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires:
                return None
            return row["user_id"]
        finally:
            conn.close()
