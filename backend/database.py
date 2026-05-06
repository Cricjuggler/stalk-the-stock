"""Postgres user store — psycopg2, no ORM. Function names match the previous SQLite module."""
from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime
from typing import Any

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as PgConnection


# ─────────────────────────────────────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────────────────────────────────────

def _get_dsn() -> str:
    """Return the Postgres DSN. Neon gives this as a single connection string."""
    dsn = os.getenv("DATABASE_URL", "").strip()
    if not dsn:
        raise RuntimeError(
            "DATABASE_URL is not set. Provide a Postgres connection string "
            "(e.g. from Neon) in your environment."
        )
    # Neon connection strings sometimes use the postgres:// prefix; psycopg2
    # accepts both, but normalise to postgresql:// for clarity.
    if dsn.startswith("postgres://"):
        dsn = "postgresql://" + dsn[len("postgres://") :]
    return dsn


def _connect() -> PgConnection:
    """Open a fresh connection. The caller is responsible for closing it
    (use a `with` block — psycopg2 commits on exit, rolls back on exception).
    """
    conn = psycopg2.connect(_get_dsn())
    return conn


def _dict_cursor(conn: PgConnection):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ─────────────────────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create all tables if they do not exist."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id       SERIAL PRIMARY KEY,
                    email    TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    pw_hash  TEXT NOT NULL,
                    created  TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            # Case-insensitive uniqueness on email + username
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_idx "
                "ON users (LOWER(email))"
            )
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS users_username_lower_idx "
                "ON users (LOWER(username))"
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS saved_stocks (
                    id       SERIAL PRIMARY KEY,
                    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    ticker   TEXT NOT NULL,
                    saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id, ticker)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS token_usage (
                    id       SERIAL PRIMARY KEY,
                    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    period   TEXT NOT NULL,
                    tokens   INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(user_id, period)
                )
                """
            )
        conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Password hashing (unchanged from SQLite version)
# ─────────────────────────────────────────────────────────────────────────────

_ITERATIONS = 260_000
_HASH_NAME = "sha256"
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Return ``salt_hex:key_hex`` using pbkdf2_hmac sha256."""
    salt = secrets.token_bytes(_SALT_BYTES)
    key = hashlib.pbkdf2_hmac(_HASH_NAME, password.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, key_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(key_hex)
        actual = hashlib.pbkdf2_hmac(_HASH_NAME, password.encode(), salt, _ITERATIONS)
        return secrets.compare_digest(actual, expected)
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# User queries — case-insensitive lookups via LOWER()
# ─────────────────────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> dict | None:
    with _connect() as conn:
        with _dict_cursor(conn) as cur:
            cur.execute(
                "SELECT * FROM users WHERE LOWER(email) = LOWER(%s)",
                (email,),
            )
            return cur.fetchone()


def get_user_by_username(username: str) -> dict | None:
    with _connect() as conn:
        with _dict_cursor(conn) as cur:
            cur.execute(
                "SELECT * FROM users WHERE LOWER(username) = LOWER(%s)",
                (username,),
            )
            return cur.fetchone()


def create_user(email: str, username: str, password: str) -> dict:
    """Insert a new user and return the created row as a dict."""
    pw_hash = hash_password(password)
    with _connect() as conn:
        with _dict_cursor(conn) as cur:
            cur.execute(
                """
                INSERT INTO users (email, username, pw_hash)
                VALUES (%s, %s, %s)
                RETURNING *
                """,
                (email, username, pw_hash),
            )
            row = cur.fetchone()
        conn.commit()
    return row


# ─────────────────────────────────────────────────────────────────────────────
# Saved stocks
# ─────────────────────────────────────────────────────────────────────────────

def get_saved_tickers(user_id: int) -> list[str]:
    """Return list of tickers saved by this user, newest first."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ticker FROM saved_stocks WHERE user_id = %s ORDER BY saved_at DESC",
                (user_id,),
            )
            rows = cur.fetchall()
    return [r[0] for r in rows]


def add_saved_stock(user_id: int, ticker: str) -> bool:
    """Save a ticker for a user. Returns True if newly added, False if duplicate."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO saved_stocks (user_id, ticker)
                VALUES (%s, %s)
                ON CONFLICT (user_id, ticker) DO NOTHING
                """,
                (user_id, ticker.upper()),
            )
            inserted = cur.rowcount > 0
        conn.commit()
    return inserted


def remove_saved_stock(user_id: int, ticker: str) -> bool:
    """Remove a saved ticker. Returns True if it existed and was deleted."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM saved_stocks WHERE user_id = %s AND ticker = %s",
                (user_id, ticker.upper()),
            )
            removed = cur.rowcount > 0
        conn.commit()
    return removed


# ─────────────────────────────────────────────────────────────────────────────
# Token usage
# ─────────────────────────────────────────────────────────────────────────────

def _current_period() -> str:
    """Return the current billing period as 'YYYY-MM'."""
    return datetime.utcnow().strftime("%Y-%m")


def get_month_tokens(user_id: int) -> int:
    """Return tokens consumed by this user in the current calendar month."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT tokens FROM token_usage WHERE user_id = %s AND period = %s",
                (user_id, _current_period()),
            )
            row = cur.fetchone()
    return row[0] if row else 0


def add_tokens(user_id: int, n: int) -> int:
    """Add *n* tokens to the user's monthly counter. Returns the new total.

    Uses an UPSERT so it's safe to call from concurrent requests.
    """
    if n <= 0:
        return get_month_tokens(user_id)
    period = _current_period()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO token_usage (user_id, period, tokens)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, period)
                DO UPDATE SET tokens = token_usage.tokens + EXCLUDED.tokens
                RETURNING tokens
                """,
                (user_id, period, n),
            )
            row = cur.fetchone()
        conn.commit()
    return row[0] if row else n
