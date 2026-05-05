"""NSE equity master list — cached in-process, refreshed once per day.

Fetches the full equity list from NSE and lets any part of the stack
search across all ~2 000 EQ-series stocks rather than just the curated 82.
Falls back gracefully if the NSE server is unreachable.
"""
from __future__ import annotations

import csv
import io
import logging
import time
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

NSE_EQUITY_CSV_URL = (
    "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
)

_master: list[dict[str, str]] = []
_last_loaded: float = 0.0
_TTL_SECONDS: float = 86_400.0  # refresh every 24 h


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_master() -> list[dict[str, str]]:
    """Download and parse the NSE equity master CSV.

    The CSV has at minimum: SYMBOL, NAME OF COMPANY, SERIES
    We keep only EQ-series rows.
    """
    req = urllib.request.Request(
        NSE_EQUITY_CSV_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,text/csv,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://www.nseindia.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        # utf-8-sig strips the BOM that NSE sometimes prepends
        raw = resp.read().decode("utf-8-sig", errors="replace")

    result: list[dict[str, str]] = []
    reader = csv.DictReader(io.StringIO(raw))
    for row in reader:
        # Normalise: strip leading/trailing whitespace from all keys and values
        cleaned: dict[str, str] = {
            k.strip(): (v.strip() if isinstance(v, str) else "")
            for k, v in row.items()
        }
        sym = cleaned.get("SYMBOL", "")
        name = cleaned.get("NAME OF COMPANY", "")
        series = cleaned.get("SERIES", "")
        if not sym or not name:
            continue
        # Keep equity series only (skip BE, BT, SM, etc.)
        if series and series.upper() != "EQ":
            continue
        result.append({"ticker": sym.upper(), "company_name": name})

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_master() -> None:
    """Pre-load the NSE master at startup.  Swallows all errors so a bad
    network day never prevents the app from starting."""
    global _master, _last_loaded
    try:
        _master = _fetch_master()
        _last_loaded = time.time()
        logger.info("NSE equity master loaded: %d EQ equities", len(_master))
    except Exception as exc:
        logger.warning("NSE equity master fetch failed at startup: %s", exc)


def _ensure_loaded() -> None:
    """Lazy-load / refresh the master if stale."""
    global _master, _last_loaded
    now = time.time()
    if not _master or (now - _last_loaded) > _TTL_SECONDS:
        try:
            _master = _fetch_master()
            _last_loaded = now
            logger.info(
                "NSE equity master refreshed: %d equities", len(_master)
            )
        except Exception as exc:
            logger.warning(
                "NSE equity master refresh failed: %s — stale cache has %d items",
                exc,
                len(_master),
            )


def search_nse(
    query: str,
    exclude_tickers: set[str],
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Search the NSE master for tickers/names matching *query*.

    Args:
        query: The search string (must be ≥ 2 chars; checked by caller).
        exclude_tickers: Tickers already shown from the curated universe.
        limit: Maximum number of results to return.

    Returns:
        List of dicts: {ticker, company_name, sector=None, curated=False}.
    """
    if not query or len(query.strip()) < 2:
        return []

    _ensure_loaded()

    q = query.lower().strip()
    results: list[dict[str, Any]] = []

    for item in _master:
        if item["ticker"] in exclude_tickers:
            continue
        if q in item["ticker"].lower() or q in item["company_name"].lower():
            results.append(
                {
                    "ticker": item["ticker"],
                    "company_name": item["company_name"],
                    "sector": None,
                    "curated": False,
                }
            )
        if len(results) >= limit:
            break

    return results
