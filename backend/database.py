"""SQLite user store — stdlib only, no ORM."""
from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

# Resolve path relative to this file: backend/ -> project_root/data/users.db
_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "users.db"


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create all tables if they do not exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                email    TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                username TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                pw_hash  TEXT    NOT NULL,
                created  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_stocks (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                ticker   TEXT    NOT NULL,
                saved_at TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, ticker)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS token_usage (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                period   TEXT    NOT NULL,
                tokens   INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, period)
            )
            """
        )
        conn.commit()


# ---------- Password hashing ----------

_ITERATIONS = 260_000
_HASH_NAME = "sha256"
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Return ``salt_hex:key_hex`` using pbkdf2_hmac sha256."""
    salt = secrets.token_bytes(_SALT_BYTES)
    key = hashlib.pbkdf2_hmac(_HASH_NAME, password.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Return True if password matches stored_hash."""
    try:
        salt_hex, key_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(key_hex)
        actual = hashlib.pbkdf2_hmac(_HASH_NAME, password.encode(), salt, _ITERATIONS)
        return secrets.compare_digest(actual, expected)
    except Exception:
        return False


# ---------- User queries ----------

def get_user_by_email(email: str) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()


def get_user_by_username(username: str) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()


def create_user(email: str, username: str, password: str) -> sqlite3.Row:
    """Insert a new user and return the created row."""
    pw_hash = hash_password(password)
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, username, pw_hash) VALUES (?, ?, ?)",
            (email, username, pw_hash),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return row


# ---------- Saved stocks ----------

def get_saved_tickers(user_id: int) -> list[str]:
    """Return list of tickers saved by this user."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT ticker FROM saved_stocks WHERE user_id = ? ORDER BY saved_at DESC",
            (user_id,),
        ).fetchall()
    return [r["ticker"] for r in rows]


def add_saved_stock(user_id: int, ticker: str) -> bool:
    """Save a ticker for a user.  Returns True if newly added, False if duplicate."""
    with _connect() as conn:
        try:
            conn.execute(
                "INSERT INTO saved_stocks (user_id, ticker) VALUES (?, ?)",
                (user_id, ticker.upper()),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def remove_saved_stock(user_id: int, ticker: str) -> bool:
    """Remove a saved ticker.  Returns True if it existed and was deleted."""
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM saved_stocks WHERE user_id = ? AND ticker = ?",
            (user_id, ticker.upper()),
        )
        conn.commit()
    return cur.rowcount > 0


# ---------- Token usage ----------

def _current_period() -> str:
    """Return the current billing period as 'YYYY-MM'."""
    return datetime.utcnow().strftime("%Y-%m")


def get_month_tokens(user_id: int) -> int:
    """Return tokens consumed by this user in the current calendar month."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT tokens FROM token_usage WHERE user_id = ? AND period = ?",
            (user_id, _current_period()),
        ).fetchone()
    return row["tokens"] if row else 0


def add_tokens(user_id: int, n: int) -> int:
    """Add *n* tokens to the user's monthly counter.  Returns the new total.

    Uses an upsert so it's safe to call from concurrent requests.
    """
    if n <= 0:
        return get_month_tokens(user_id)
    period = _current_period()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO token_usage (user_id, period, tokens)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, period)
            DO UPDATE SET tokens = tokens + excluded.tokens
            """,
            (user_id, period, n),
        )
        conn.commit()
        row = conn.execute(
            "SELECT tokens FROM token_usage WHERE user_id = ? AND period = ?",
            (user_id, period),
        ).fetchone()
    return row["tokens"] if row else n
