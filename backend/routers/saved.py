"""Saved-stocks endpoints — requires a valid JWT."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

import database
from routers.auth import get_current_user

router = APIRouter()


class SaveRequest(BaseModel):
    ticker: str


def _uid(current_user: dict) -> int:
    """Extract integer user ID from the JWT payload (stored as 'sub' string)."""
    return int(current_user["sub"])


@router.get("")
def list_saved(current_user: dict = Depends(get_current_user)):
    """Return all tickers saved by the authenticated user."""
    tickers = database.get_saved_tickers(_uid(current_user))
    return {"tickers": tickers}


@router.post("")
def save_stock(req: SaveRequest, current_user: dict = Depends(get_current_user)):
    """Add a ticker to the user's saved list (idempotent)."""
    ticker = req.ticker.strip().upper()
    newly_added = database.add_saved_stock(_uid(current_user), ticker)
    return {"saved": True, "ticker": ticker, "newly_added": newly_added}


@router.delete("/{ticker}")
def unsave_stock(ticker: str, current_user: dict = Depends(get_current_user)):
    """Remove a ticker from the user's saved list."""
    ticker = ticker.strip().upper()
    removed = database.remove_saved_stock(_uid(current_user), ticker)
    return {"saved": False, "ticker": ticker, "removed": removed}
