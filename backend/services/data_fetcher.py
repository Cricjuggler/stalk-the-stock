"""Data fetcher: yfinance-backed price + fundamentals + universe search."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from config import STOCK_UNIVERSE

logger = logging.getLogger(__name__)


def _normalize_ticker(ticker: str) -> str:
    t = ticker.upper().strip()
    if t.startswith("^"):  # index symbol
        return t
    if t.endswith(".NS"):
        return t
    return f"{t}.NS"


def fetch_stock_data(ticker: str) -> dict[str, Any]:
    """Fetch ~300 trading days of OHLCV plus derived snapshot fields."""
    display = _normalize_ticker(ticker)
    try:
        tk = yf.Ticker(display)
        df = tk.history(period="2y", auto_adjust=False)
    except Exception as e:
        logger.exception("yfinance history failed for %s", display)
        raise ValueError(f"Unable to fetch market data for {ticker}: {e}") from e

    if df is None or df.empty:
        raise ValueError(f"No price data returned for {ticker}")

    # Keep last ~300 trading days
    if len(df) > 300:
        df = df.tail(300).copy()
    else:
        df = df.copy()

    df.columns = [str(c) for c in df.columns]
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column {col} in price data for {ticker}")

    df = df.dropna(subset=["Close"])
    if df.empty:
        raise ValueError(f"All close prices null for {ticker}")

    current_price = float(df["Close"].iloc[-1])
    yesterday_volume = float(df["Volume"].iloc[-1]) if not pd.isna(df["Volume"].iloc[-1]) else 0.0
    avg_volume_30d = float(df["Volume"].tail(30).mean()) if len(df) >= 1 else 0.0

    # 52w window = last ~252 trading days
    win = df.tail(252) if len(df) >= 252 else df
    high_52w = float(win["High"].max())
    low_52w = float(win["Low"].min())

    last_idx = df.index[-1]
    if hasattr(last_idx, "to_pydatetime"):
        last_dt = last_idx.to_pydatetime()
    else:
        last_dt = datetime.fromisoformat(str(last_idx))
    # Strip tz for comparison
    if last_dt.tzinfo is not None:
        last_dt = last_dt.replace(tzinfo=None)
    data_fresh = (datetime.utcnow() - last_dt) <= timedelta(days=5)

    return {
        "ohlcv_df": df,
        "current_price": current_price,
        "yesterday_volume": yesterday_volume,
        "avg_volume_30d": avg_volume_30d,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "ticker_display": display,
        "data_fresh": data_fresh,
        "last_data_date": last_dt.date().isoformat(),
    }


def _safe_get(info: dict, key: str) -> Any:
    v = info.get(key)
    if v is None:
        return None
    try:
        if isinstance(v, float) and (v != v):  # NaN check
            return None
    except Exception:
        pass
    return v


def fetch_fundamentals(ticker: str) -> dict[str, Any]:
    display = _normalize_ticker(ticker)
    info: dict = {}
    try:
        tk = yf.Ticker(display)
        info = tk.info or {}
    except Exception as e:
        logger.warning("yfinance info failed for %s: %s", display, e)
        info = {}

    roe_raw = _safe_get(info, "returnOnEquity")
    roe = float(roe_raw) * 100 if roe_raw is not None else None

    de_raw = _safe_get(info, "debtToEquity")
    # yfinance returns this scaled (e.g. 75 = 0.75); keep as-is and let evaluator interpret in <1 / >1 terms.
    if de_raw is not None:
        de_val = float(de_raw)
        # yfinance frequently returns a percentage form (e.g., 75 means 0.75). Normalize to ratio.
        if de_val > 5:
            de_val = de_val / 100.0
    else:
        de_val = None

    earnings_growth = _safe_get(info, "earningsGrowth")
    profit_cagr_3y = float(earnings_growth) if earnings_growth is not None else None

    out = {
        "roe": roe,
        "debt_to_equity": de_val,
        "profit_cagr_3y": profit_cagr_3y,
        "profit_cagr_estimated": True,
        "promoter_pledging": None,
        "pledging_data_unavailable": True,
        "auditor_resignation": False,
        "filing_data_unavailable": True,
        "company_name": _safe_get(info, "longName") or _safe_get(info, "shortName"),
        "sector": _safe_get(info, "sector"),
        "market_cap": _safe_get(info, "marketCap"),
        "pe_ratio": _safe_get(info, "trailingPE"),
        "pb_ratio": _safe_get(info, "priceToBook"),
        "dividend_yield": _safe_get(info, "dividendYield"),
    }

    missing = sum(
        1 for k in ("roe", "debt_to_equity", "profit_cagr_3y", "pe_ratio", "pb_ratio")
        if out.get(k) is None
    )
    out["data_quality_warning"] = missing > 2
    return out


def search_stocks(query: str) -> list[dict]:
    if not query:
        return []
    q = query.lower().strip()
    matches: list[dict] = []
    for s in STOCK_UNIVERSE:
        if q in s["ticker"].lower() or q in s["company_name"].lower():
            matches.append(
                {
                    "ticker": s["ticker"],
                    "company_name": s["company_name"],
                    "sector": s["sector"],
                }
            )
        if len(matches) >= 10:
            break
    return matches
