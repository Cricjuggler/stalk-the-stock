"""SQLite user store — stdlib only, no ORM."""
from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
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
    """Create the users table if it does not exist."""
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
