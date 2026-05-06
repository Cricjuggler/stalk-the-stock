"""Stalk the Stock — configuration: env, constants, and stock universe."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve .env relative to this file so cwd doesn't matter.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _candidate in (_PROJECT_ROOT / ".env", _PROJECT_ROOT.parent / ".env", Path.cwd() / ".env"):
    if _candidate.exists():
        load_dotenv(_candidate)
        break
else:
    load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-7")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

LLM_TIMEOUT_SECONDS = 8.0
LLM_MAX_TOKENS = 800

# Monthly token budget per user.  Set TOKEN_LIMIT_PER_USER in env / Render
# dashboard to override.  Defaults to 50 000 tokens (~50-75 AI requests).
TOKEN_LIMIT_PER_USER: int = int(os.getenv("TOKEN_LIMIT_PER_USER", "50000"))

STOCK_UNIVERSE = [
    # ENERGY / OIL
    {"ticker": "RELIANCE", "company_name": "Reliance Industries", "sector": "Energy", "index": "NIFTY50"},
    {"ticker": "ONGC", "company_name": "Oil & Natural Gas Corp", "sector": "Energy", "index": "NIFTY50"},
    {"ticker": "BPCL", "company_name": "Bharat Petroleum", "sector": "Energy", "index": "NIFTY50"},
    {"ticker": "IOC", "company_name": "Indian Oil Corp", "sector": "Energy", "index": "NIFTYNEXT50"},
    {"ticker": "GAIL", "company_name": "GAIL India", "sector": "Energy", "index": "NIFTYNEXT50"},

    # PRIVATE BANKS
    {"ticker": "HDFCBANK", "company_name": "HDFC Bank", "sector": "Banking", "index": "NIFTY50"},
    {"ticker": "ICICIBANK", "company_name": "ICICI Bank", "sector": "Banking", "index": "NIFTY50"},
    {"ticker": "KOTAKBANK", "company_name": "Kotak Mahindra Bank", "sector": "Banking", "index": "NIFTY50"},
    {"ticker": "AXISBANK", "company_name": "Axis Bank", "sector": "Banking", "index": "NIFTY50"},
    {"ticker": "INDUSINDBK", "company_name": "IndusInd Bank", "sector": "Banking", "index": "NIFTY50"},

    # PSU BANKS
    {"ticker": "SBIN", "company_name": "State Bank of India", "sector": "Banking", "index": "NIFTY50"},
    {"ticker": "BANKBARODA", "company_name": "Bank of Baroda", "sector": "Banking", "index": "NIFTYNEXT50"},
    {"ticker": "PNB", "company_name": "Punjab National Bank", "sector": "Banking", "index": "NIFTYNEXT50"},
    {"ticker": "CANBK", "company_name": "Canara Bank", "sector": "Banking", "index": "OTHER"},

    # NBFC / FINTECH
    {"ticker": "BAJFINANCE", "company_name": "Bajaj Finance", "sector": "NBFC", "index": "NIFTY50"},
    {"ticker": "BAJAJFINSV", "company_name": "Bajaj Finserv", "sector": "NBFC", "index": "NIFTY50"},
    {"ticker": "PAYTM", "company_name": "One 97 Communications (Paytm)", "sector": "NBFC", "index": "OTHER"},
    {"ticker": "MUTHOOTFIN", "company_name": "Muthoot Finance", "sector": "NBFC", "index": "NIFTYNEXT50"},

    # IT
    {"ticker": "TCS", "company_name": "Tata Consultancy Services", "sector": "IT", "index": "NIFTY50"},
    {"ticker": "INFY", "company_name": "Infosys", "sector": "IT", "index": "NIFTY50"},
    {"ticker": "WIPRO", "company_name": "Wipro", "sector": "IT", "index": "NIFTY50"},
    {"ticker": "HCLTECH", "company_name": "HCL Technologies", "sector": "IT", "index": "NIFTY50"},
    {"ticker": "TECHM", "company_name": "Tech Mahindra", "sector": "IT", "index": "NIFTY50"},
    {"ticker": "LTIM", "company_name": "LTIMindtree", "sector": "IT", "index": "NIFTYNEXT50"},
    {"ticker": "PERSISTENT", "company_name": "Persistent Systems", "sector": "IT", "index": "NIFTYMIDCAP"},

    # FMCG
    {"ticker": "ITC", "company_name": "ITC", "sector": "FMCG", "index": "NIFTY50"},
    {"ticker": "HINDUNILVR", "company_name": "Hindustan Unilever", "sector": "FMCG", "index": "NIFTY50"},
    {"ticker": "NESTLEIND", "company_name": "Nestle India", "sector": "FMCG", "index": "NIFTY50"},
    {"ticker": "BRITANNIA", "company_name": "Britannia Industries", "sector": "FMCG", "index": "NIFTY50"},
    {"ticker": "DABUR", "company_name": "Dabur India", "sector": "FMCG", "index": "NIFTYNEXT50"},
    {"ticker": "MARICO", "company_name": "Marico", "sector": "FMCG", "index": "NIFTYNEXT50"},

    # AUTO
    {"ticker": "MARUTI", "company_name": "Maruti Suzuki India", "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "TATAMOTORS", "company_name": "Tata Motors", "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "M&M", "company_name": "Mahindra & Mahindra", "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "BAJAJ-AUTO", "company_name": "Bajaj Auto", "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "HEROMOTOCO", "company_name": "Hero MotoCorp", "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "EICHERMOT", "company_name": "Eicher Motors", "sector": "Auto", "index": "NIFTY50"},

    # PHARMA
    {"ticker": "SUNPHARMA", "company_name": "Sun Pharmaceutical", "sector": "Pharma", "index": "NIFTY50"},
    {"ticker": "DRREDDY", "company_name": "Dr Reddy's Laboratories", "sector": "Pharma", "index": "NIFTY50"},
    {"ticker": "CIPLA", "company_name": "Cipla", "sector": "Pharma", "index": "NIFTY50"},
    {"ticker": "DIVISLAB", "company_name": "Divi's Laboratories", "sector": "Pharma", "index": "NIFTY50"},
    {"ticker": "AUROPHARMA", "company_name": "Aurobindo Pharma", "sector": "Pharma", "index": "NIFTYNEXT50"},

    # METALS
    {"ticker": "TATASTEEL", "company_name": "Tata Steel", "sector": "Metals", "index": "NIFTY50"},
    {"ticker": "HINDALCO", "company_name": "Hindalco Industries", "sector": "Metals", "index": "NIFTY50"},
    {"ticker": "JSWSTEEL", "company_name": "JSW Steel", "sector": "Metals", "index": "NIFTY50"},
    {"ticker": "VEDL", "company_name": "Vedanta", "sector": "Metals", "index": "NIFTYNEXT50"},
    {"ticker": "COALINDIA", "company_name": "Coal India", "sector": "Metals", "index": "NIFTY50"},

    # INFRA / CAPITAL GOODS
    {"ticker": "LT", "company_name": "Larsen & Toubro", "sector": "Infra", "index": "NIFTY50"},
    {"ticker": "ADANIPORTS", "company_name": "Adani Ports & SEZ", "sector": "Infra", "index": "NIFTY50"},
    {"ticker": "ADANIENT", "company_name": "Adani Enterprises", "sector": "Infra", "index": "NIFTY50"},
    {"ticker": "SIEMENS", "company_name": "Siemens India", "sector": "Infra", "index": "NIFTYNEXT50"},
    {"ticker": "ABB", "company_name": "ABB India", "sector": "Infra", "index": "NIFTYNEXT50"},

    # TELECOM
    {"ticker": "BHARTIARTL", "company_name": "Bharti Airtel", "sector": "Telecom", "index": "NIFTY50"},
    {"ticker": "IDEA", "company_name": "Vodafone Idea", "sector": "Telecom", "index": "OTHER"},

    # CONSUMER / RETAIL
    {"ticker": "TITAN", "company_name": "Titan Company", "sector": "Consumer", "index": "NIFTY50"},
    {"ticker": "ASIANPAINT", "company_name": "Asian Paints", "sector": "Consumer", "index": "NIFTY50"},
    {"ticker": "PIDILITIND", "company_name": "Pidilite Industries", "sector": "Consumer", "index": "NIFTYNEXT50"},
    {"ticker": "TATACONSUM", "company_name": "Tata Consumer Products", "sector": "Consumer", "index": "NIFTY50"},

    # NEW-AGE TECH
    {"ticker": "ZOMATO", "company_name": "Zomato", "sector": "New-Age Tech", "index": "NIFTYNEXT50"},
    {"ticker": "NYKAA", "company_name": "FSN E-Commerce (Nykaa)", "sector": "New-Age Tech", "index": "OTHER"},
    {"ticker": "POLICYBZR", "company_name": "PB Fintech (Policybazaar)", "sector": "New-Age Tech", "index": "OTHER"},
    {"ticker": "DELHIVERY", "company_name": "Delhivery", "sector": "New-Age Tech", "index": "OTHER"},

    # REALTY
    {"ticker": "DLF", "company_name": "DLF", "sector": "Realty", "index": "NIFTYNEXT50"},
    {"ticker": "GODREJPROP", "company_name": "Godrej Properties", "sector": "Realty", "index": "NIFTYNEXT50"},
    {"ticker": "OBEROIRLTY", "company_name": "Oberoi Realty", "sector": "Realty", "index": "OTHER"},

    # CEMENT (extra coverage)
    {"ticker": "ULTRACEMCO", "company_name": "UltraTech Cement", "sector": "Cement", "index": "NIFTY50"},
    {"ticker": "GRASIM", "company_name": "Grasim Industries", "sector": "Cement", "index": "NIFTY50"},
    {"ticker": "SHREECEM", "company_name": "Shree Cement", "sector": "Cement", "index": "NIFTYNEXT50"},
    {"ticker": "AMBUJACEM", "company_name": "Ambuja Cements", "sector": "Cement", "index": "NIFTYNEXT50"},

    # POWER / UTILITIES
    {"ticker": "NTPC", "company_name": "NTPC", "sector": "Power", "index": "NIFTY50"},
    {"ticker": "POWERGRID", "company_name": "Power Grid Corp", "sector": "Power", "index": "NIFTY50"},
    {"ticker": "TATAPOWER", "company_name": "Tata Power", "sector": "Power", "index": "NIFTYNEXT50"},
    {"ticker": "ADANIGREEN", "company_name": "Adani Green Energy", "sector": "Power", "index": "NIFTYNEXT50"},

    # CHEMICALS
    {"ticker": "UPL", "company_name": "UPL Limited", "sector": "Chemicals", "index": "NIFTY50"},
    {"ticker": "SRF", "company_name": "SRF Limited", "sector": "Chemicals", "index": "NIFTYNEXT50"},
    {"ticker": "PIIND", "company_name": "PI Industries", "sector": "Chemicals", "index": "NIFTYNEXT50"},

    # HEALTHCARE / DIAGNOSTICS
    {"ticker": "APOLLOHOSP", "company_name": "Apollo Hospitals", "sector": "Healthcare", "index": "NIFTY50"},
    {"ticker": "MAXHEALTH", "company_name": "Max Healthcare", "sector": "Healthcare", "index": "OTHER"},

    # INSURANCE
    {"ticker": "SBILIFE", "company_name": "SBI Life Insurance", "sector": "Insurance", "index": "NIFTY50"},
    {"ticker": "HDFCLIFE", "company_name": "HDFC Life Insurance", "sector": "Insurance", "index": "NIFTY50"},
    {"ticker": "ICICIGI", "company_name": "ICICI Lombard General Insurance", "sector": "Insurance", "index": "NIFTYNEXT50"},

    # INDEX
    {"ticker": "^NSEI", "company_name": "Nifty 50 Index", "sector": "Index", "index": "INDEX"},
]


def get_stock_meta(ticker: str) -> dict | None:
    t = ticker.upper().strip()
    if t.endswith(".NS"):
        t = t[:-3]
    for s in STOCK_UNIVERSE:
        if s["ticker"].upper() == t:
            return s
    return None
