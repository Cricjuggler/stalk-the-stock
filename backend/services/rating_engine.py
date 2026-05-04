"""Rating engine: form status + rule-based fallback why-card."""
from __future__ import annotations

from typing import Any


STATUS_META = {
    "In-Form": {"emoji": "🔥", "color": "green"},
    "On-Track": {"emoji": "✅", "color": "blue"},
    "Off-Track": {"emoji": "⚠️", "color": "amber"},
    "Out-of-Form": {"emoji": "❄️", "color": "red"},
}


def compute_form_status(
    trend: dict,
    volume: dict,
    fundamentals: dict,
    current_price: float,
    mas: dict,
) -> dict[str, Any]:
    """Determine FormCheck status with priority-ordered rules."""
    trend_score = trend.get("trend_score", 0)
    fund_score = fundamentals.get("fundamental_score", 0)
    has_critical = fundamentals.get("has_critical_red_flag", False)

    if has_critical:
        status = "Out-of-Form"
    elif trend_score == 3 and fund_score >= 2:
        status = "In-Form"
    elif fund_score >= 2 and trend_score in (1, 2):
        status = "On-Track"
    elif fund_score < 2 and trend_score in (1, 2):
        status = "Off-Track"
    elif trend_score == 0:
        status = "Out-of-Form"
    else:
        # Edge cases (e.g., trend_score=3 but fund_score<2)
        if trend_score == 3:
            status = "On-Track"
        else:
            status = "Off-Track"

    meta = STATUS_META[status]
    return {
        "status": status,
        "emoji": meta["emoji"],
        "color": meta["color"],
        "high_conviction": volume.get("is_spike", False),
    }


def _fmt_inr(v: float | None) -> str:
    if v is None:
        return "N/A"
    return f"₹{v:,.2f}"


def generate_fallback_why_card(
    ticker: str,
    status: dict,
    trend: dict,
    fundamentals: dict,
    volume: dict,
    buy_range: dict,
    sell_range: dict,
    current_price: float,
    mas: dict,
) -> dict[str, Any]:
    """Rule-based why-card used when LLM is unavailable or times out."""
    bullets: list[str] = []

    ma_30d = mas.get("ma_30d")
    if ma_30d is not None:
        rel = "above" if current_price > ma_30d else "below"
        signal = "momentum is intact" if current_price > ma_30d else "near-term weakness is visible"
        bullets.append(
            f"Price ({_fmt_inr(current_price)}) is {rel} the 30D average ({_fmt_inr(ma_30d)}), indicating {signal}."
        )
    else:
        bullets.append(
            f"Price stands at {_fmt_inr(current_price)}; insufficient history for full trend hierarchy."
        )

    fd = fundamentals.get("details", {})
    bullets.append(
        f"Fundamentals score {fundamentals.get('fundamental_score', 0)}/3: ROE is "
        f"{fd.get('roe_status', 'Unknown')}, Debt-to-Equity is {fd.get('debt_status', 'Unknown')}, "
        f"earnings growth is {fd.get('earnings_growth', 'Unknown')}."
    )

    ratio = volume.get("volume_ratio", 0.0)
    flag = volume.get("conviction_flag", "Normal Volume")
    if ratio:
        bullets.append(
            f"Volume is {ratio:.2f}x the 30D average — {flag.lower()} signal accompanying the price action."
        )
    else:
        bullets.append("Volume data unavailable for the latest session.")

    status_label = status.get("status", "Off-Track")
    note_map = {
        "In-Form": "Trend hierarchy is intact and fundamentals are healthy. Signals suggest accumulation interest, though not a buy recommendation.",
        "On-Track": "Fundamentals are sound but trend strength is partial. Data indicates the setup is constructive but not yet confirmed.",
        "Off-Track": "Fundamentals are below threshold while trend is mixed. Signals suggest caution and a reassessment of conviction.",
        "Out-of-Form": "Trend is broken or a critical red flag exists. Data indicates capital preservation is the priority here.",
    }
    analyst_note = note_map.get(status_label, "Mixed signals — review the underlying components before acting.")

    confidence = "Medium"
    fund_score = fundamentals.get("fundamental_score", 0)
    trend_score = trend.get("trend_score", 0)
    if fund_score >= 2 and trend_score >= 2:
        confidence = "High"
    elif fund_score == 0 or trend_score == 0:
        confidence = "Low"

    return {
        "why_bullets": bullets,
        "analyst_note": analyst_note,
        "confidence": confidence,
        "source": "rule-based",
    }
