"""Stock router: /analyze, /chat, /search, /universe."""
from __future__ import annotations

import logging
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

import config
import database
from config import STOCK_UNIVERSE, get_stock_meta
from models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
)
from routers.auth import get_optional_user
from services import data_fetcher, technical, fundamental, rating_engine, llm_service, nse_master

router = APIRouter()
logger = logging.getLogger(__name__)


def _check_and_enforce_limit(user_id: int) -> None:
    """Raise HTTP 429 if the user has exceeded their monthly token budget."""
    used = database.get_month_tokens(user_id)
    if used >= config.TOKEN_LIMIT_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="usage_limit_exceeded",
        )


def _detect_ticker_in_message(message: str) -> str | None:
    msg = message.upper()
    # Prefer longer tickers first to avoid partial collisions (e.g., "M&M" vs "M")
    candidates = sorted(STOCK_UNIVERSE, key=lambda s: -len(s["ticker"]))
    for s in candidates:
        t = s["ticker"]
        if t == "^NSEI":
            continue
        if t in msg:
            return t
    # Try by company name first word
    msg_low = message.lower()
    for s in candidates:
        first = s["company_name"].split()[0].lower()
        if len(first) >= 4 and first in msg_low:
            return s["ticker"]
    return None


async def _build_analysis(ticker: str, user_id: int | None = None) -> dict:
    """Run the full pipeline and return a dict matching AnalyzeResponse shape."""
    meta = get_stock_meta(ticker)

    try:
        price_data = data_fetcher.fetch_stock_data(ticker)
    except ValueError as e:
        msg = str(e).lower()
        if "no price" in msg or "missing column" in msg or "all close" in msg:
            raise HTTPException(
                status_code=404,
                detail="Ticker not found. Try NSE symbol e.g., RELIANCE, INFY",
            ) from e
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch market data. Try again in a moment.",
        ) from e
    except Exception as e:
        logger.exception("fetch_stock_data unexpected error for %s", ticker)
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch market data. Try again in a moment.",
        ) from e

    fund_data = data_fetcher.fetch_fundamentals(ticker)

    df = price_data["ohlcv_df"]
    current_price = price_data["current_price"]

    mas = technical.calculate_moving_averages(df)
    vwap_30 = technical.calculate_vwap_30d(df)
    bb = technical.calculate_bollinger_bands(df)
    trend = technical.check_trend_hierarchy(current_price, mas)
    volume = technical.check_volume_spike(price_data["yesterday_volume"], price_data["avg_volume_30d"])
    rsi = technical.calculate_rsi(df)
    price_changes = technical.calculate_price_change(df)

    fund_eval = fundamental.evaluate_fundamentals(fund_data)
    status = rating_engine.compute_form_status(trend, volume, fund_eval, current_price, mas)

    buy_range = technical.calculate_buy_range(vwap_30, mas.get("ema_200"))
    sell_range = technical.calculate_sell_range(bb.get("upper_band"), price_data.get("high_52w"), current_price)

    why_card, why_tokens = await llm_service.generate_why_card(
        ticker=price_data["ticker_display"],
        company_name=fund_data.get("company_name") or (meta["company_name"] if meta else ticker),
        status=status,
        trend=trend,
        fundamentals=fund_eval,
        volume=volume,
        buy_range=buy_range,
        sell_range=sell_range,
        current_price=current_price,
        rsi=rsi,
        price_changes=price_changes,
        mas=mas,
    )
    if user_id is not None and why_tokens > 0:
        database.add_tokens(user_id, why_tokens)

    warnings: list[str] = []
    if not price_data.get("data_fresh"):
        warnings.append(
            f"Data may be delayed. Latest price from {price_data.get('last_data_date')}. Verify on NSE website."
        )
    if fund_data.get("data_quality_warning"):
        warnings.append("Fundamental data is incomplete for this ticker.")
    if fund_data.get("pledging_data_unavailable"):
        warnings.append("Promoter pledging data unavailable via yfinance — manual check required.")

    company_name = fund_data.get("company_name") or (meta["company_name"] if meta else ticker)
    sector = fund_data.get("sector") or (meta["sector"] if meta else None)

    # Stash extras the why-card / chat layers may want without leaking the dataframe
    trend_with_volume_flag = dict(trend)
    trend_with_volume_flag["conviction_flag"] = volume.get("conviction_flag")

    return {
        "ticker": ticker.upper(),
        "is_curated": meta is not None,
        "company_name": company_name,
        "sector": sector,
        "current_price": round(current_price, 2),
        "high_52w": round(price_data["high_52w"], 2),
        "low_52w": round(price_data["low_52w"], 2),
        "price_changes": price_changes,
        "rsi": rsi,
        "status": status,
        "trend": {
            **trend,
            "ma_1w": mas.get("ma_1w"),
            "ma_30d": mas.get("ma_30d"),
            "ma_52w": mas.get("ma_52w"),
            "ema_200": mas.get("ema_200"),
            "volume_ratio": volume.get("volume_ratio"),
            "conviction_flag": volume.get("conviction_flag"),
            "is_volume_spike": volume.get("is_spike"),
        },
        "fundamentals_summary": fund_eval,
        "buy_range": buy_range,
        "sell_range": sell_range,
        "why_card": why_card,
        "data_warnings": warnings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_stock(
    request: AnalyzeRequest,
    user: Optional[dict] = Depends(get_optional_user),
):
    user_id: int | None = int(user["sub"]) if user else None
    if user_id is not None:
        _check_and_enforce_limit(user_id)
    return await _build_analysis(request.ticker, user_id=user_id)


@router.get("/search")
async def search_stocks(q: str = Query(..., min_length=1)):
    # Curated universe results (instant, in-memory)
    curated = data_fetcher.search_stocks(q)
    for s in curated:
        s["curated"] = True

    # NSE master results — excludes everything already in the curated universe
    all_curated_tickers: set[str] = {s["ticker"] for s in STOCK_UNIVERSE}
    nse_results = nse_master.search_nse(q, all_curated_tickers)

    return {"query": q, "results": curated + nse_results}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: Optional[dict] = Depends(get_optional_user),
):
    user_id: int | None = int(user["sub"]) if user else None
    if user_id is not None:
        _check_and_enforce_limit(user_id)

    analysis_context: dict | None = None
    detected: str | None = None

    if request.context_ticker:
        try:
            # Don't double-count tokens for the context fetch here — the
            # context analysis was already paid for when /analyze was called.
            analysis_context = await _build_analysis(request.context_ticker)
            detected = analysis_context["ticker"]
        except HTTPException:
            analysis_context = None

    if analysis_context is None:
        guess = _detect_ticker_in_message(request.message)
        if guess:
            detected = guess

    response_text, chat_tokens = await llm_service.process_chat(
        user_message=request.message,
        analysis_context=analysis_context,
        conversation_history=request.conversation_history or [],
    )
    if user_id is not None and chat_tokens > 0:
        database.add_tokens(user_id, chat_tokens)

    return ChatResponse(response=response_text, ticker_detected=detected)


@router.get("/universe")
async def get_stock_universe():
    sectors: "OrderedDict[str, list[dict]]" = OrderedDict()
    for s in STOCK_UNIVERSE:
        sectors.setdefault(s["sector"], []).append(s)
    return {
        "total": len(STOCK_UNIVERSE),
        "sectors": sectors,
        "stocks": STOCK_UNIVERSE,
    }
