"""Auth router — signup / login / me endpoints using PyJWT + SQLite."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator

import database

router = APIRouter(tags=["auth"])

_SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme-set-in-env")
_ALGORITHM = "HS256"
_TOKEN_EXPIRE_DAYS = 30


# ---------- JWT helpers ----------

def _make_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.now(tz=timezone.utc) + timedelta(days=_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises 401 HTTPException on any failure."""
    try:
        return jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token expired — please log in again",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )


def get_current_user(authorization: str = Header(None)) -> dict:
    """FastAPI dependency — parses Bearer <token> and returns payload dict."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or malformed Authorization header",
        )
    token = authorization.removeprefix("Bearer ").strip()
    return decode_token(token)


# ---------- Schemas ----------

class SignupBody(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("username must be at least 2 characters")
        if len(v) > 32:
            raise ValueError("username must be 32 characters or fewer")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("password must be at least 6 characters")
        return v


class LoginBody(BaseModel):
    email: EmailStr
    password: str


# ---------- Routes ----------

@router.post("/signup")
def signup(body: SignupBody):
    """Register a new user. Returns JWT token + username."""
    if database.get_user_by_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already registered",
        )
    if database.get_user_by_username(body.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="username already taken",
        )
    user = database.create_user(body.email, body.username, body.password)
    token = _make_token(user["id"], user["username"])
    return {"token": token, "username": user["username"]}


@router.post("/login")
def login(body: LoginBody):
    """Authenticate with email + password. Returns JWT token + username."""
    user = database.get_user_by_email(body.email)
    if not user or not database.verify_password(body.password, user["pw_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect email or password",
        )
    token = _make_token(user["id"], user["username"])
    return {"token": token, "username": user["username"]}


@router.get("/me")
def me(payload: dict = Depends(get_current_user)):
    """Return basic info about the authenticated user."""
    return {"username": payload["username"], "id": int(payload["sub"])}
