"""Pydantic models for request/response shapes."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    ticker: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context_ticker: str | None = None
    conversation_history: list[dict] | None = []


class StockSearchRequest(BaseModel):
    query: str


class AnalyzeResponse(BaseModel):
    ticker: str
    company_name: str
    sector: str | None = None
    is_curated: bool = True
    current_price: float
    high_52w: float | None = None
    low_52w: float | None = None
    price_changes: dict
    rsi: float | None = None
    status: dict
    trend: dict
    fundamentals_summary: dict
    buy_range: dict
    sell_range: dict
    why_card: dict
    data_warnings: list[str] = []
    timestamp: str


class ChatResponse(BaseModel):
    response: str
    ticker_detected: str | None = None


class SearchResult(BaseModel):
    ticker: str
    company_name: str
    sector: str
