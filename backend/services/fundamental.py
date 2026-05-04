"""Fundamental scoring + red flag detection."""
from __future__ import annotations

from typing import Any


def evaluate_fundamentals(fund_data: dict) -> dict[str, Any]:
    roe = fund_data.get("roe")
    de = fund_data.get("debt_to_equity")
    growth = fund_data.get("profit_cagr_3y")

    score = 0

    # Debt/Equity: +1 if known and < 1. Unknown = no penalty, no credit.
    if de is not None and de < 1:
        score += 1
        debt_status = "Low(<1)"
    elif de is not None:
        debt_status = "High"
    else:
        debt_status = "Unknown"

    # ROE: +1 if known and > 15%
    if roe is not None and roe > 15:
        score += 1
        roe_status = "Strong(>15%)"
    elif roe is not None:
        roe_status = "Weak"
    else:
        roe_status = "Unknown"

    # Earnings growth proxy
    if growth is not None and growth > 0:
        score += 1
        earnings_growth = "Positive"
    elif growth is not None:
        earnings_growth = "Negative"
    else:
        earnings_growth = "Unknown"

    red_flags: list[str] = []
    if fund_data.get("pledging_data_unavailable"):
        red_flags.append("Pledging data unavailable — manual check required")
    if fund_data.get("auditor_resignation"):
        red_flags.append("Auditor Resignation detected")

    has_critical_red_flag = bool(fund_data.get("auditor_resignation"))

    return {
        "fundamental_score": score,
        "max_score": 3,
        "is_strong": score >= 2,
        "red_flags": red_flags,
        "has_critical_red_flag": has_critical_red_flag,
        "details": {
            "roe_status": roe_status,
            "debt_status": debt_status,
            "earnings_growth": earnings_growth,
            "pe_ratio": fund_data.get("pe_ratio"),
            "pb_ratio": fund_data.get("pb_ratio"),
            "roe_value": roe,
            "debt_to_equity_value": de,
        },
    }
