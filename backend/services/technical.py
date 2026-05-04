"""Technical indicators: MAs, VWAP, Bollinger, RSI, trend, volume, ranges."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd


def _last_float(s: pd.Series) -> float | None:
    if s is None or s.empty:
        return None
    v = s.iloc[-1]
    if pd.isna(v):
        return None
    return float(v)


def calculate_moving_averages(df: pd.DataFrame) -> dict[str, float | None]:
    close = df["Close"]
    ma_1w = _last_float(close.rolling(5).mean())
    ma_30d = _last_float(close.rolling(21).mean())
    ma_52w = _last_float(close.rolling(252).mean()) if len(close) >= 252 else _last_float(close.rolling(len(close)).mean())
    ema_200_series = close.ewm(span=200, adjust=False).mean()
    ema_200 = _last_float(ema_200_series)
    return {
        "ma_1w": ma_1w,
        "ma_30d": ma_30d,
        "ma_52w": ma_52w,
        "ema_200": ema_200,
    }


def calculate_vwap_30d(df: pd.DataFrame) -> float | None:
    tail = df.tail(30)
    vol_sum = float(tail["Volume"].sum())
    if vol_sum <= 0:
        return None
    pv = (tail["Close"] * tail["Volume"]).sum()
    return float(pv / vol_sum)


def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: int = 2) -> dict[str, float | None]:
    close = df["Close"]
    middle = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return {
        "upper_band": _last_float(upper),
        "middle_band": _last_float(middle),
        "lower_band": _last_float(lower),
    }


def check_trend_hierarchy(current_price: float, mas: dict) -> dict[str, Any]:
    above_1w = mas.get("ma_1w") is not None and current_price > mas["ma_1w"]
    above_30d = mas.get("ma_30d") is not None and current_price > mas["ma_30d"]
    above_52w = mas.get("ma_52w") is not None and current_price > mas["ma_52w"]
    score = int(above_1w) + int(above_30d) + int(above_52w)
    return {
        "price_above_1w": above_1w,
        "price_above_30d": above_30d,
        "price_above_52w": above_52w,
        "full_uptrend": above_1w and above_30d and above_52w,
        "full_downtrend": (not above_1w) and (not above_30d) and (not above_52w),
        "trend_score": score,
    }


def check_volume_spike(yesterday_vol: float, avg_vol_30d: float) -> dict[str, Any]:
    if not avg_vol_30d or avg_vol_30d <= 0:
        return {
            "is_spike": False,
            "volume_ratio": 0.0,
            "conviction_flag": "Normal Volume",
        }
    ratio = yesterday_vol / avg_vol_30d
    is_spike = ratio > 2.0
    return {
        "is_spike": is_spike,
        "volume_ratio": round(ratio, 2),
        "conviction_flag": "High Conviction" if is_spike else "Normal Volume",
    }


def calculate_buy_range(vwap_30d: float | None, ema_200: float | None) -> dict[str, Any]:
    candidates = [v for v in (vwap_30d, ema_200) if v is not None and v > 0]
    if not candidates:
        return {"lower": None, "upper": None, "label": "Buy Zone (VWAP/EMA200 Support)"}
    lo = min(candidates) * 0.98
    hi = max(candidates) * 1.02
    return {
        "lower": round(lo, 2),
        "upper": round(hi, 2),
        "label": "Buy Zone (VWAP/EMA200 Support)",
    }


def calculate_sell_range(upper_bollinger: float | None, high_52w: float | None, current_price: float) -> dict[str, Any]:
    levels = [v for v in (upper_bollinger, high_52w) if v is not None and v > 0]
    above = [v for v in levels if v > current_price]

    if len(above) >= 2:
        lo = min(above)
        hi = max(above)
    elif len(above) == 1:
        lo = above[0]
        hi = above[0] * 1.05
    elif levels:
        # Fallback: project sell zone above current price
        base = max(levels)
        lo = max(base, current_price) * 1.05
        hi = lo * 1.05
    else:
        return {"lower": None, "upper": None, "label": "Sell Zone (Bollinger Upper / 52W High)"}

    return {
        "lower": round(float(lo), 2),
        "upper": round(float(hi), 2),
        "label": "Sell Zone (Bollinger Upper / 52W High)",
    }


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> float | None:
    close = df["Close"]
    if len(close) < period + 1:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    val = _last_float(rsi)
    if val is None:
        return None
    return round(float(val), 2)


def _pct(curr: float, prev: float | None) -> float | None:
    if prev is None or prev == 0:
        return None
    return round(((curr - prev) / prev) * 100, 2)


def calculate_price_change(df: pd.DataFrame) -> dict[str, float | None]:
    close = df["Close"]
    curr = float(close.iloc[-1])

    prev_1d = float(close.iloc[-2]) if len(close) >= 2 else None
    prev_1w = float(close.iloc[-6]) if len(close) >= 6 else None
    prev_1m = float(close.iloc[-22]) if len(close) >= 22 else None

    change_ytd = None
    try:
        year = datetime.utcnow().year
        df_year = df[df.index.year == year] if hasattr(df.index, "year") else None
        if df_year is None or df_year.empty:
            idx_year = pd.to_datetime(df.index).year if not hasattr(df.index, "year") else df.index.year
            mask = idx_year == year
            df_year = df[mask]
        if df_year is not None and not df_year.empty:
            ytd_open = float(df_year["Close"].iloc[0])
            change_ytd = _pct(curr, ytd_open)
    except Exception:
        change_ytd = None

    return {
        "change_1d": _pct(curr, prev_1d),
        "change_1w": _pct(curr, prev_1w),
        "change_1m": _pct(curr, prev_1m),
        "change_ytd": change_ytd,
    }
