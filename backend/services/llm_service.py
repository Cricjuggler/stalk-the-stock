"""Anthropic Claude integration for stalk. — why-card + chat."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import anthropic

import config
from services.rating_engine import generate_fallback_why_card

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic | None:
    global _client
    if not config.ANTHROPIC_API_KEY:
        return None
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


SYSTEM_PROMPT = (
    "You are stalky, the AI analyst behind stalk. — an Indian stock market platform for a Gen Z audience. "
    "You analyze stocks with the rigor of a SEBI-registered research analyst — factual, "
    "data-driven, cautious — but the bullet text itself can be slightly casual and direct. "
    "Never give direct buy or sell advice. Always frame output as 'signals suggest' or "
    "'data indicates'. Use Indian financial terminology and ₹ for prices. "
    "Return ONLY valid JSON with no markdown fences, no preamble. "
    "Keys required: why_bullets (array of exactly 3 strings), analyst_note (string), "
    "confidence (string: High/Medium/Low)."
)

CHAT_SYSTEM_PROMPT = (
    "You are stalky, the AI chat assistant for stalk. — an Indian stock market platform with a Gen Z personality. "
    "Be playful, lowercase-friendly, use occasional emojis, but always stay factual and data-driven. "
    "You analyze stocks with the rigor of a SEBI-registered research analyst. "
    "Never give direct buy or sell advice. Frame output as 'signals suggest' or "
    "'data indicates'. Use Indian financial terminology and ₹ for prices. "
    "When the user asks about a specific stock, reference analysis_context if provided. "
    "Otherwise answer from general knowledge of Indian markets. "
    "Keep responses concise (3-6 sentences) unless the user asks for depth. "
    "You can use casual phrasing like 'tbh', 'rn', 'lowkey', 'no cap' sparingly — never sacrifice accuracy for vibe."
)


def _build_user_prompt(
    ticker: str,
    company_name: str,
    status: dict,
    trend: dict,
    fundamentals: dict,
    volume: dict,
    buy_range: dict,
    sell_range: dict,
    current_price: float,
    rsi: float | None,
    price_changes: dict,
    mas: dict,
) -> str:
    fd = fundamentals.get("details", {})
    return f"""Analyze {company_name} ({ticker}) with the following computed data:

STATUS: {status.get("status")}
CURRENT PRICE: ₹{current_price}
RSI: {rsi if rsi is not None else "N/A"}

TREND DATA:
- Price vs 1W avg (₹{mas.get("ma_1w")}): {trend.get("price_above_1w")}
- Price vs 30D avg (₹{mas.get("ma_30d")}): {trend.get("price_above_30d")}
- Price vs 52W avg (₹{mas.get("ma_52w")}): {trend.get("price_above_52w")}
- Trend Score: {trend.get("trend_score")}/3

PRICE CHANGES:
- 1D: {price_changes.get("change_1d")}% | 1W: {price_changes.get("change_1w")}% | 1M: {price_changes.get("change_1m")}% | YTD: {price_changes.get("change_ytd")}%

VOLUME:
- Yesterday vs 30D avg: {volume.get("volume_ratio")}x ({volume.get("conviction_flag")})

FUNDAMENTALS:
- ROE: {fd.get("roe_status")} | Debt/Equity: {fd.get("debt_status")} | Earnings Growth: {fd.get("earnings_growth")}
- Fundamental Score: {fundamentals.get("fundamental_score")}/3
- Red Flags: {fundamentals.get("red_flags")}

BUY ZONE: ₹{buy_range.get("lower")} – ₹{buy_range.get("upper")}
SELL ZONE: ₹{sell_range.get("lower")} – ₹{sell_range.get("upper")}

Generate 3 specific bullet points explaining this rating. Each bullet must cite
actual numbers from the data above. Then provide one analyst_note and a confidence level."""


def _parse_json_response(text: str) -> dict | None:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Try extracting first {...} block
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                result = json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return None
        else:
            return None
    if not isinstance(result, dict):
        return None
    if "why_bullets" not in result or "analyst_note" not in result or "confidence" not in result:
        return None
    bullets = result.get("why_bullets")
    if not isinstance(bullets, list) or len(bullets) == 0:
        return None
    return result


async def generate_why_card(
    ticker: str,
    company_name: str,
    status: dict,
    trend: dict,
    fundamentals: dict,
    volume: dict,
    buy_range: dict,
    sell_range: dict,
    current_price: float,
    rsi: float | None,
    price_changes: dict,
    mas: dict,
) -> dict[str, Any]:
    """Call Claude for an analyst-style why card; fall back to rule-based on any failure."""
    fallback = generate_fallback_why_card(
        ticker, status, trend, fundamentals, volume, buy_range, sell_range, current_price, mas
    )

    client = _get_client()
    if client is None:
        logger.info("ANTHROPIC_API_KEY missing — using rule-based why-card.")
        return fallback

    user_prompt = _build_user_prompt(
        ticker, company_name, status, trend, fundamentals, volume,
        buy_range, sell_range, current_price, rsi, price_changes, mas,
    )

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.messages.create,
                model=config.CLAUDE_MODEL,
                max_tokens=config.LLM_MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            ),
            timeout=config.LLM_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("Claude why-card timed out for %s", ticker)
        fallback["source"] = "rule-based-fallback"
        return fallback
    except Exception as e:
        logger.exception("Claude why-card error for %s: %s", ticker, e)
        fallback["source"] = "rule-based-fallback"
        return fallback

    try:
        text = response.content[0].text
    except Exception:
        fallback["source"] = "rule-based-fallback"
        return fallback

    parsed = _parse_json_response(text)
    if parsed is None:
        logger.warning("Claude returned unparseable JSON for %s; using fallback.", ticker)
        fallback["source"] = "rule-based-fallback"
        return fallback

    parsed["source"] = "claude"
    # Ensure exactly 3 bullets
    if len(parsed["why_bullets"]) > 3:
        parsed["why_bullets"] = parsed["why_bullets"][:3]
    elif len(parsed["why_bullets"]) < 3:
        parsed["why_bullets"] = parsed["why_bullets"] + fallback["why_bullets"][len(parsed["why_bullets"]) :]
    return parsed


async def process_chat(
    user_message: str,
    analysis_context: dict | None,
    conversation_history: list[dict] | None,
) -> str:
    """Multi-turn chat with optional analysis context for the in-focus stock."""
    client = _get_client()
    if client is None:
        return (
            "chat needs an ANTHROPIC_API_KEY in your .env to work 🔑 — "
            "but you can still stalk stocks from the watchlist on the left ✨"
        )

    system = CHAT_SYSTEM_PROMPT
    if analysis_context:
        # Compact context summary appended to the system prompt
        ctx = (
            f"\n\nCURRENT ANALYSIS CONTEXT:\n"
            f"Ticker: {analysis_context.get('ticker')}\n"
            f"Company: {analysis_context.get('company_name')}\n"
            f"Status: {analysis_context.get('status', {}).get('status')}\n"
            f"Current Price: ₹{analysis_context.get('current_price')}\n"
            f"Trend Score: {analysis_context.get('trend', {}).get('trend_score')}/3\n"
            f"Fundamental Score: {analysis_context.get('fundamentals_summary', {}).get('fundamental_score')}/3\n"
            f"RSI: {analysis_context.get('rsi')}\n"
            f"Buy Zone: ₹{analysis_context.get('buy_range', {}).get('lower')}–₹{analysis_context.get('buy_range', {}).get('upper')}\n"
            f"Sell Zone: ₹{analysis_context.get('sell_range', {}).get('lower')}–₹{analysis_context.get('sell_range', {}).get('upper')}\n"
        )
        system = system + ctx

    messages: list[dict] = []
    for m in (conversation_history or [])[-10:]:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.messages.create,
                model=config.CLAUDE_MODEL,
                max_tokens=600,
                system=system,
                messages=messages,
            ),
            timeout=15.0,
        )
        return response.content[0].text.strip()
    except asyncio.TimeoutError:
        return "I'm taking too long to respond. Please try a simpler question or try again in a moment."
    except Exception as e:
        logger.exception("Claude chat error: %s", e)
        return "Something went wrong while processing that. Please try again."
