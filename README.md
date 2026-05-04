# FormCheck — Intelligent Indian Stock Assistant

FormCheck is a full-stack web app that analyzes NSE-listed Indian stocks using technical signals, fundamental scoring, and a SEBI-style analyst persona powered by Anthropic Claude. It produces a "form status" rating (In-Form / On-Track / Off-Track / Out-of-Form) along with buy/sell zones and an analyst-style "why this rating?" card.

## Setup

```bash
# 1. Clone and enter the project
cd formcheck

# 2. Configure your environment
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY (optional — falls back to rule-based without it)

# 3. Run
bash run.sh        # macOS / Linux
# or on Windows:
run.bat
```

The app boots at `http://localhost:8000`. The frontend is served from the same FastAPI process — no separate dev server needed.

### Manual install

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## How to use

**Stock browser (left panel)** — search by name or ticker, filter by sector or NIFTY50, click any stock to analyze it.

**Chat (right panel)** — ask follow-up questions about the currently-loaded stock, or ask anything about Indian markets.

### Example queries
- `Check HDFCBANK`
- `Why is Zomato Off-Track?`
- `Explain In-Form status`
- `Compare HDFCBANK and ICICIBANK`
- `What does the Buy Zone mean?`

## Known limitations

- **Promoter pledging data unavailable** via yfinance (would need a paid BSE/NSE filings feed)
- Prices are **end-of-day**, not real-time intraday
- 3-year profit CAGR is estimated via the `earningsGrowth` proxy from yfinance
- Some mid-cap and small-cap tickers may have incomplete fundamental fields
- Auditor-resignation flag defaults to false unless overridden manually (no filings feed)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (vanilla HTML/CSS/JS)                         │
│   ├── Stock browser (search, filter, sectors)           │
│   ├── Analysis card (price, status, ranges, why-card)   │
│   └── Chat interface (multi-turn with Claude)           │
└────────────────────────┬────────────────────────────────┘
                         │  HTTP /api/*
┌────────────────────────▼────────────────────────────────┐
│  FastAPI backend                                        │
│   ├── /analyze   →  full pipeline                       │
│   ├── /chat      →  Claude multi-turn + context         │
│   ├── /search    →  universe search                     │
│   └── /universe  →  grouped stock list                  │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
data_      technical  fundamental rating_   llm_
fetcher    (MA,VWAP,  (ROE,D/E,   engine    service
(yfinance) Bollinger, growth,    (status   (Claude
            RSI)      red flags) priority)  + fallback)
```

## Pipeline (per /analyze call)

1. yfinance pull — 2y OHLCV + `.info` fundamentals
2. Compute MAs (5/21/252 SMA + EMA-200), VWAP-30, Bollinger(20,2), RSI-14, price changes
3. Trend hierarchy (price vs 1W/30D/52W) → trend_score 0–3
4. Volume spike check (yesterday vs 30D avg)
5. Fundamental score (Debt/Equity, ROE, earnings growth) + red flags
6. Form status priority: critical-flag → In-Form → On-Track → Off-Track → Out-of-Form
7. Buy zone = VWAP/EMA-200 band; Sell zone = Bollinger upper / 52W high
8. Why-card via Claude (8s timeout) → falls back to rule-based on miss

## Roadmap (Phase 2)

- Promoter pledging via BSE/NSE filings API
- Real-time intraday prices via NSE WebSocket
- Sector rotation heatmap
- Saved watchlists per user
- Backtest the form-status signal against forward returns

## Disclaimer

FormCheck is **not SEBI-registered research** and is intended for educational use only. Nothing in this app constitutes investment advice.
