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
    # ── ENERGY / OIL & GAS (14) ─────────────────────────────────────────────
    {"ticker": "RELIANCE",  "company_name": "Reliance Industries",           "sector": "Energy", "index": "NIFTY50"},
    {"ticker": "ONGC",      "company_name": "Oil & Natural Gas Corp",        "sector": "Energy", "index": "NIFTY50"},
    {"ticker": "BPCL",      "company_name": "Bharat Petroleum",              "sector": "Energy", "index": "NIFTY50"},
    {"ticker": "IOC",       "company_name": "Indian Oil Corp",               "sector": "Energy", "index": "NIFTYNEXT50"},
    {"ticker": "GAIL",      "company_name": "GAIL India",                    "sector": "Energy", "index": "NIFTYNEXT50"},
    {"ticker": "HINDPETRO", "company_name": "Hindustan Petroleum Corp",      "sector": "Energy", "index": "NIFTYNEXT50"},
    {"ticker": "OIL",       "company_name": "Oil India",                     "sector": "Energy", "index": "NIFTYNEXT50"},
    {"ticker": "PETRONET",  "company_name": "Petronet LNG",                  "sector": "Energy", "index": "NIFTYNEXT50"},
    {"ticker": "IGL",       "company_name": "Indraprastha Gas",              "sector": "Energy", "index": "NIFTYNEXT50"},
    {"ticker": "MGL",       "company_name": "Mahanagar Gas",                 "sector": "Energy", "index": "OTHER"},
    {"ticker": "ATGL",      "company_name": "Adani Total Gas",               "sector": "Energy", "index": "NIFTYNEXT50"},
    {"ticker": "GUJGASLTD", "company_name": "Gujarat Gas",                   "sector": "Energy", "index": "OTHER"},
    {"ticker": "GSPL",      "company_name": "Gujarat State Petronet",        "sector": "Energy", "index": "OTHER"},
    {"ticker": "AEGISCHEM", "company_name": "Aegis Logistics",               "sector": "Energy", "index": "OTHER"},

    # ── PRIVATE BANKS (11) ──────────────────────────────────────────────────
    {"ticker": "HDFCBANK",   "company_name": "HDFC Bank",               "sector": "Banking", "index": "NIFTY50"},
    {"ticker": "ICICIBANK",  "company_name": "ICICI Bank",              "sector": "Banking", "index": "NIFTY50"},
    {"ticker": "KOTAKBANK",  "company_name": "Kotak Mahindra Bank",     "sector": "Banking", "index": "NIFTY50"},
    {"ticker": "AXISBANK",   "company_name": "Axis Bank",               "sector": "Banking", "index": "NIFTY50"},
    {"ticker": "INDUSINDBK", "company_name": "IndusInd Bank",           "sector": "Banking", "index": "NIFTY50"},
    {"ticker": "FEDERALBNK", "company_name": "Federal Bank",            "sector": "Banking", "index": "NIFTYNEXT50"},
    {"ticker": "IDFCFIRSTB", "company_name": "IDFC First Bank",         "sector": "Banking", "index": "NIFTYNEXT50"},
    {"ticker": "RBLBANK",    "company_name": "RBL Bank",                "sector": "Banking", "index": "OTHER"},
    {"ticker": "BANDHANBNK", "company_name": "Bandhan Bank",            "sector": "Banking", "index": "NIFTYNEXT50"},
    {"ticker": "AUBANK",     "company_name": "AU Small Finance Bank",   "sector": "Banking", "index": "NIFTYNEXT50"},
    {"ticker": "YESBANK",    "company_name": "Yes Bank",                "sector": "Banking", "index": "NIFTYNEXT50"},

    # ── PSU BANKS (8) ───────────────────────────────────────────────────────
    {"ticker": "SBIN",      "company_name": "State Bank of India",     "sector": "Banking", "index": "NIFTY50"},
    {"ticker": "BANKBARODA","company_name": "Bank of Baroda",          "sector": "Banking", "index": "NIFTYNEXT50"},
    {"ticker": "PNB",       "company_name": "Punjab National Bank",    "sector": "Banking", "index": "NIFTYNEXT50"},
    {"ticker": "CANBK",     "company_name": "Canara Bank",             "sector": "Banking", "index": "OTHER"},
    {"ticker": "UNIONBANK", "company_name": "Union Bank of India",     "sector": "Banking", "index": "OTHER"},
    {"ticker": "INDIANB",   "company_name": "Indian Bank",             "sector": "Banking", "index": "OTHER"},
    {"ticker": "BANKINDIA", "company_name": "Bank of India",           "sector": "Banking", "index": "OTHER"},
    {"ticker": "MAHABANK",  "company_name": "Bank of Maharashtra",     "sector": "Banking", "index": "OTHER"},

    # ── NBFC / FINTECH (10) ─────────────────────────────────────────────────
    {"ticker": "BAJFINANCE",  "company_name": "Bajaj Finance",                          "sector": "NBFC", "index": "NIFTY50"},
    {"ticker": "BAJAJFINSV",  "company_name": "Bajaj Finserv",                          "sector": "NBFC", "index": "NIFTY50"},
    {"ticker": "SHRIRAMFIN",  "company_name": "Shriram Finance",                        "sector": "NBFC", "index": "NIFTY50"},
    {"ticker": "CHOLAFIN",    "company_name": "Cholamandalam Investment & Finance",     "sector": "NBFC", "index": "NIFTYNEXT50"},
    {"ticker": "MUTHOOTFIN",  "company_name": "Muthoot Finance",                        "sector": "NBFC", "index": "NIFTYNEXT50"},
    {"ticker": "LICHSGFIN",   "company_name": "LIC Housing Finance",                   "sector": "NBFC", "index": "NIFTYNEXT50"},
    {"ticker": "M&MFIN",      "company_name": "Mahindra & Mahindra Financial Services", "sector": "NBFC", "index": "NIFTYNEXT50"},
    {"ticker": "MANAPPURAM",  "company_name": "Manappuram Finance",                     "sector": "NBFC", "index": "NIFTYNEXT50"},
    {"ticker": "PAYTM",       "company_name": "One 97 Communications (Paytm)",          "sector": "NBFC", "index": "OTHER"},
    {"ticker": "SUNDARMFIN",  "company_name": "Sundaram Finance",                       "sector": "NBFC", "index": "OTHER"},

    # ── IT (17) ─────────────────────────────────────────────────────────────
    {"ticker": "TCS",        "company_name": "Tata Consultancy Services",        "sector": "IT", "index": "NIFTY50"},
    {"ticker": "INFY",       "company_name": "Infosys",                          "sector": "IT", "index": "NIFTY50"},
    {"ticker": "WIPRO",      "company_name": "Wipro",                            "sector": "IT", "index": "NIFTY50"},
    {"ticker": "HCLTECH",    "company_name": "HCL Technologies",                 "sector": "IT", "index": "NIFTY50"},
    {"ticker": "TECHM",      "company_name": "Tech Mahindra",                    "sector": "IT", "index": "NIFTY50"},
    {"ticker": "LTIM",       "company_name": "LTIMindtree",                      "sector": "IT", "index": "NIFTYNEXT50"},
    {"ticker": "PERSISTENT", "company_name": "Persistent Systems",              "sector": "IT", "index": "NIFTYNEXT50"},
    {"ticker": "MPHASIS",    "company_name": "Mphasis",                          "sector": "IT", "index": "NIFTYNEXT50"},
    {"ticker": "COFORGE",    "company_name": "Coforge",                          "sector": "IT", "index": "NIFTYNEXT50"},
    {"ticker": "OFSS",       "company_name": "Oracle Financial Services Software","sector": "IT", "index": "NIFTYNEXT50"},
    {"ticker": "TATAELXSI",  "company_name": "Tata Elxsi",                       "sector": "IT", "index": "NIFTYNEXT50"},
    {"ticker": "KPITTECH",   "company_name": "KPIT Technologies",                "sector": "IT", "index": "OTHER"},
    {"ticker": "BIRLASOFT",  "company_name": "Birlasoft",                         "sector": "IT", "index": "OTHER"},
    {"ticker": "CYIENT",     "company_name": "Cyient",                            "sector": "IT", "index": "OTHER"},
    {"ticker": "MASTEK",     "company_name": "Mastek",                            "sector": "IT", "index": "OTHER"},
    {"ticker": "FSL",        "company_name": "Firstsource Solutions",             "sector": "IT", "index": "OTHER"},
    {"ticker": "HEXAWARE",   "company_name": "Hexaware Technologies",             "sector": "IT", "index": "OTHER"},

    # ── FMCG (13) ───────────────────────────────────────────────────────────
    {"ticker": "ITC",        "company_name": "ITC",                          "sector": "FMCG", "index": "NIFTY50"},
    {"ticker": "HINDUNILVR", "company_name": "Hindustan Unilever",           "sector": "FMCG", "index": "NIFTY50"},
    {"ticker": "NESTLEIND",  "company_name": "Nestle India",                 "sector": "FMCG", "index": "NIFTY50"},
    {"ticker": "BRITANNIA",  "company_name": "Britannia Industries",         "sector": "FMCG", "index": "NIFTY50"},
    {"ticker": "DABUR",      "company_name": "Dabur India",                  "sector": "FMCG", "index": "NIFTYNEXT50"},
    {"ticker": "MARICO",     "company_name": "Marico",                       "sector": "FMCG", "index": "NIFTYNEXT50"},
    {"ticker": "COLPAL",     "company_name": "Colgate-Palmolive India",      "sector": "FMCG", "index": "NIFTYNEXT50"},
    {"ticker": "GODREJCP",   "company_name": "Godrej Consumer Products",     "sector": "FMCG", "index": "NIFTYNEXT50"},
    {"ticker": "VBL",        "company_name": "Varun Beverages",              "sector": "FMCG", "index": "NIFTYNEXT50"},
    {"ticker": "UBL",        "company_name": "United Breweries",             "sector": "FMCG", "index": "OTHER"},
    {"ticker": "EMAMILTD",   "company_name": "Emami",                        "sector": "FMCG", "index": "OTHER"},
    {"ticker": "JYOTHYLAB",  "company_name": "Jyothy Labs",                  "sector": "FMCG", "index": "OTHER"},
    {"ticker": "RADICO",     "company_name": "Radico Khaitan",               "sector": "FMCG", "index": "OTHER"},

    # ── AUTO & AUTO ANCILLARIES (14) ────────────────────────────────────────
    {"ticker": "MARUTI",     "company_name": "Maruti Suzuki India",                   "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "TATAMOTORS", "company_name": "Tata Motors",                           "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "M&M",        "company_name": "Mahindra & Mahindra",                   "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "BAJAJ-AUTO", "company_name": "Bajaj Auto",                            "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "HEROMOTOCO", "company_name": "Hero MotoCorp",                         "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "EICHERMOT",  "company_name": "Eicher Motors",                         "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "MOTHERSON",  "company_name": "Samvardhana Motherson International",   "sector": "Auto", "index": "NIFTY50"},
    {"ticker": "ASHOKLEY",   "company_name": "Ashok Leyland",                         "sector": "Auto", "index": "NIFTYNEXT50"},
    {"ticker": "TVSMOTOR",   "company_name": "TVS Motor Company",                     "sector": "Auto", "index": "NIFTYNEXT50"},
    {"ticker": "BALKRISIND", "company_name": "Balkrishna Industries",                 "sector": "Auto", "index": "NIFTYNEXT50"},
    {"ticker": "EXIDEIND",   "company_name": "Exide Industries",                      "sector": "Auto", "index": "NIFTYNEXT50"},
    {"ticker": "BOSCHLTD",   "company_name": "Bosch India",                           "sector": "Auto", "index": "OTHER"},
    {"ticker": "MRF",        "company_name": "MRF",                                   "sector": "Auto", "index": "OTHER"},
    {"ticker": "CEATLTD",    "company_name": "CEAT",                                  "sector": "Auto", "index": "OTHER"},

    # ── PHARMA (15) ─────────────────────────────────────────────────────────
    {"ticker": "SUNPHARMA",  "company_name": "Sun Pharmaceutical",          "sector": "Pharma", "index": "NIFTY50"},
    {"ticker": "DRREDDY",    "company_name": "Dr Reddy's Laboratories",     "sector": "Pharma", "index": "NIFTY50"},
    {"ticker": "CIPLA",      "company_name": "Cipla",                       "sector": "Pharma", "index": "NIFTY50"},
    {"ticker": "DIVISLAB",   "company_name": "Divi's Laboratories",         "sector": "Pharma", "index": "NIFTY50"},
    {"ticker": "AUROPHARMA", "company_name": "Aurobindo Pharma",            "sector": "Pharma", "index": "NIFTYNEXT50"},
    {"ticker": "LUPIN",      "company_name": "Lupin",                       "sector": "Pharma", "index": "NIFTYNEXT50"},
    {"ticker": "TORNTPHARM", "company_name": "Torrent Pharmaceuticals",     "sector": "Pharma", "index": "NIFTYNEXT50"},
    {"ticker": "ZYDUSLIFE",  "company_name": "Zydus Lifesciences",          "sector": "Pharma", "index": "NIFTYNEXT50"},
    {"ticker": "ALKEM",      "company_name": "Alkem Laboratories",          "sector": "Pharma", "index": "OTHER"},
    {"ticker": "GLENMARK",   "company_name": "Glenmark Pharmaceuticals",    "sector": "Pharma", "index": "OTHER"},
    {"ticker": "IPCALAB",    "company_name": "Ipca Laboratories",           "sector": "Pharma", "index": "OTHER"},
    {"ticker": "LAURUSLABS", "company_name": "Laurus Labs",                 "sector": "Pharma", "index": "OTHER"},
    {"ticker": "ABBOTINDIA", "company_name": "Abbott India",                "sector": "Pharma", "index": "OTHER"},
    {"ticker": "GRANULES",   "company_name": "Granules India",              "sector": "Pharma", "index": "OTHER"},
    {"ticker": "PFIZER",     "company_name": "Pfizer India",                "sector": "Pharma", "index": "OTHER"},

    # ── METALS & MINING (12) ────────────────────────────────────────────────
    {"ticker": "TATASTEEL",  "company_name": "Tata Steel",                  "sector": "Metals", "index": "NIFTY50"},
    {"ticker": "HINDALCO",   "company_name": "Hindalco Industries",         "sector": "Metals", "index": "NIFTY50"},
    {"ticker": "JSWSTEEL",   "company_name": "JSW Steel",                   "sector": "Metals", "index": "NIFTY50"},
    {"ticker": "COALINDIA",  "company_name": "Coal India",                  "sector": "Metals", "index": "NIFTY50"},
    {"ticker": "VEDL",       "company_name": "Vedanta",                     "sector": "Metals", "index": "NIFTYNEXT50"},
    {"ticker": "NMDC",       "company_name": "NMDC",                        "sector": "Metals", "index": "NIFTYNEXT50"},
    {"ticker": "SAIL",       "company_name": "Steel Authority of India",    "sector": "Metals", "index": "NIFTYNEXT50"},
    {"ticker": "APLAPOLLO",  "company_name": "APL Apollo Tubes",            "sector": "Metals", "index": "OTHER"},
    {"ticker": "NATIONALUM", "company_name": "National Aluminium Company",  "sector": "Metals", "index": "OTHER"},
    {"ticker": "HINDCOPPER", "company_name": "Hindustan Copper",            "sector": "Metals", "index": "OTHER"},
    {"ticker": "WELCORP",    "company_name": "Welspun Corp",                "sector": "Metals", "index": "OTHER"},
    {"ticker": "MOIL",       "company_name": "MOIL",                        "sector": "Metals", "index": "OTHER"},

    # ── INFRA / CAPITAL GOODS (14) ──────────────────────────────────────────
    {"ticker": "LT",         "company_name": "Larsen & Toubro",      "sector": "Infra", "index": "NIFTY50"},
    {"ticker": "ADANIPORTS", "company_name": "Adani Ports & SEZ",    "sector": "Infra", "index": "NIFTY50"},
    {"ticker": "ADANIENT",   "company_name": "Adani Enterprises",    "sector": "Infra", "index": "NIFTY50"},
    {"ticker": "SIEMENS",    "company_name": "Siemens India",        "sector": "Infra", "index": "NIFTYNEXT50"},
    {"ticker": "ABB",        "company_name": "ABB India",            "sector": "Infra", "index": "NIFTYNEXT50"},
    {"ticker": "BHEL",       "company_name": "Bharat Heavy Electricals", "sector": "Infra", "index": "NIFTYNEXT50"},
    {"ticker": "HAVELLS",    "company_name": "Havells India",        "sector": "Infra", "index": "NIFTYNEXT50"},
    {"ticker": "POLYCAB",    "company_name": "Polycab India",        "sector": "Infra", "index": "NIFTYNEXT50"},
    {"ticker": "CUMMINSIND", "company_name": "Cummins India",        "sector": "Infra", "index": "NIFTYNEXT50"},
    {"ticker": "THERMAX",    "company_name": "Thermax",              "sector": "Infra", "index": "OTHER"},
    {"ticker": "VOLTAS",     "company_name": "Voltas",               "sector": "Infra", "index": "OTHER"},
    {"ticker": "TIINDIA",    "company_name": "Tube Investments of India", "sector": "Infra", "index": "OTHER"},
    {"ticker": "GRINDWELL",  "company_name": "Grindwell Norton",     "sector": "Infra", "index": "OTHER"},
    {"ticker": "SCHAEFFLER", "company_name": "Schaeffler India",     "sector": "Infra", "index": "OTHER"},

    # ── DEFENCE (6) ─────────────────────────────────────────────────────────
    {"ticker": "HAL",        "company_name": "Hindustan Aeronautics",         "sector": "Defence", "index": "NIFTY50"},
    {"ticker": "BEL",        "company_name": "Bharat Electronics",            "sector": "Defence", "index": "NIFTY50"},
    {"ticker": "COCHINSHIP", "company_name": "Cochin Shipyard",               "sector": "Defence", "index": "OTHER"},
    {"ticker": "GRSE",       "company_name": "Garden Reach Shipbuilders",     "sector": "Defence", "index": "OTHER"},
    {"ticker": "MAZDOCK",    "company_name": "Mazagon Dock Shipbuilders",     "sector": "Defence", "index": "OTHER"},
    {"ticker": "MIDHANI",    "company_name": "Mishra Dhatu Nigam",            "sector": "Defence", "index": "OTHER"},

    # ── TELECOM (5) ─────────────────────────────────────────────────────────
    {"ticker": "BHARTIARTL", "company_name": "Bharti Airtel",             "sector": "Telecom", "index": "NIFTY50"},
    {"ticker": "INDUSTOWER", "company_name": "Indus Towers",              "sector": "Telecom", "index": "NIFTYNEXT50"},
    {"ticker": "TATACOMM",   "company_name": "Tata Communications",       "sector": "Telecom", "index": "NIFTYNEXT50"},
    {"ticker": "HFCL",       "company_name": "HFCL",                      "sector": "Telecom", "index": "OTHER"},
    {"ticker": "IDEA",       "company_name": "Vodafone Idea",             "sector": "Telecom", "index": "OTHER"},

    # ── CONSUMER / RETAIL (14) ──────────────────────────────────────────────
    {"ticker": "TITAN",      "company_name": "Titan Company",                  "sector": "Consumer", "index": "NIFTY50"},
    {"ticker": "ASIANPAINT", "company_name": "Asian Paints",                   "sector": "Consumer", "index": "NIFTY50"},
    {"ticker": "TATACONSUM", "company_name": "Tata Consumer Products",         "sector": "Consumer", "index": "NIFTY50"},
    {"ticker": "DMART",      "company_name": "Avenue Supermarts (DMart)",      "sector": "Consumer", "index": "NIFTY50"},
    {"ticker": "PIDILITIND", "company_name": "Pidilite Industries",            "sector": "Consumer", "index": "NIFTYNEXT50"},
    {"ticker": "BERGEPAINT", "company_name": "Berger Paints India",            "sector": "Consumer", "index": "NIFTYNEXT50"},
    {"ticker": "JUBLFOOD",   "company_name": "Jubilant FoodWorks",             "sector": "Consumer", "index": "NIFTYNEXT50"},
    {"ticker": "NAUKRI",     "company_name": "Info Edge India",                "sector": "Consumer", "index": "NIFTYNEXT50"},
    {"ticker": "KALYANKJIL", "company_name": "Kalyan Jewellers India",         "sector": "Consumer", "index": "OTHER"},
    {"ticker": "BATAINDIA",  "company_name": "Bata India",                     "sector": "Consumer", "index": "OTHER"},
    {"ticker": "INDIAMART",  "company_name": "IndiaMART InterMESH",            "sector": "Consumer", "index": "OTHER"},
    {"ticker": "ABFRL",      "company_name": "Aditya Birla Fashion & Retail",  "sector": "Consumer", "index": "OTHER"},
    {"ticker": "SENCO",      "company_name": "Senco Gold",                     "sector": "Consumer", "index": "OTHER"},
    {"ticker": "RAJESHEXPO", "company_name": "Rajesh Exports",                 "sector": "Consumer", "index": "OTHER"},

    # ── NEW-AGE TECH (10) ───────────────────────────────────────────────────
    {"ticker": "ZOMATO",     "company_name": "Zomato",                              "sector": "New-Age Tech", "index": "NIFTY50"},
    {"ticker": "IRCTC",      "company_name": "IRCTC",                               "sector": "New-Age Tech", "index": "NIFTYNEXT50"},
    {"ticker": "NYKAA",      "company_name": "FSN E-Commerce (Nykaa)",              "sector": "New-Age Tech", "index": "OTHER"},
    {"ticker": "POLICYBZR",  "company_name": "PB Fintech (Policybazaar)",           "sector": "New-Age Tech", "index": "OTHER"},
    {"ticker": "DELHIVERY",  "company_name": "Delhivery",                           "sector": "New-Age Tech", "index": "OTHER"},
    {"ticker": "IXIGO",      "company_name": "Le Travenues Technology (Ixigo)",     "sector": "New-Age Tech", "index": "OTHER"},
    {"ticker": "SWIGGY",     "company_name": "Swiggy",                              "sector": "New-Age Tech", "index": "OTHER"},
    {"ticker": "BRAINBEES",  "company_name": "Brainbees Solutions (FirstCry)",      "sector": "New-Age Tech", "index": "OTHER"},
    {"ticker": "MAPMYINDIA", "company_name": "C.E. Info Systems (MapmyIndia)",      "sector": "New-Age Tech", "index": "OTHER"},
    {"ticker": "CARTRADE",   "company_name": "CarTrade Tech",                       "sector": "New-Age Tech", "index": "OTHER"},

    # ── REALTY (8) ──────────────────────────────────────────────────────────
    {"ticker": "DLF",        "company_name": "DLF",                           "sector": "Realty", "index": "NIFTYNEXT50"},
    {"ticker": "GODREJPROP", "company_name": "Godrej Properties",             "sector": "Realty", "index": "NIFTYNEXT50"},
    {"ticker": "MACROTECH",  "company_name": "Macrotech Developers (Lodha)", "sector": "Realty", "index": "NIFTYNEXT50"},
    {"ticker": "OBEROIRLTY", "company_name": "Oberoi Realty",                "sector": "Realty", "index": "OTHER"},
    {"ticker": "BRIGADE",    "company_name": "Brigade Enterprises",          "sector": "Realty", "index": "OTHER"},
    {"ticker": "PRESTIGE",   "company_name": "Prestige Estates Projects",    "sector": "Realty", "index": "OTHER"},
    {"ticker": "SOBHA",      "company_name": "Sobha",                        "sector": "Realty", "index": "OTHER"},
    {"ticker": "SUNTECK",    "company_name": "Sunteck Realty",               "sector": "Realty", "index": "OTHER"},

    # ── CEMENT (9) ──────────────────────────────────────────────────────────
    {"ticker": "ULTRACEMCO", "company_name": "UltraTech Cement",        "sector": "Cement", "index": "NIFTY50"},
    {"ticker": "GRASIM",     "company_name": "Grasim Industries",       "sector": "Cement", "index": "NIFTY50"},
    {"ticker": "SHREECEM",   "company_name": "Shree Cement",            "sector": "Cement", "index": "NIFTYNEXT50"},
    {"ticker": "AMBUJACEM",  "company_name": "Ambuja Cements",          "sector": "Cement", "index": "NIFTYNEXT50"},
    {"ticker": "DALBHARAT",  "company_name": "Dalmia Bharat Cement",    "sector": "Cement", "index": "NIFTYNEXT50"},
    {"ticker": "JKCEMENT",   "company_name": "JK Cement",               "sector": "Cement", "index": "OTHER"},
    {"ticker": "RAMCOCEM",   "company_name": "Ramco Cements",           "sector": "Cement", "index": "OTHER"},
    {"ticker": "JKLAKSHMI",  "company_name": "JK Lakshmi Cement",       "sector": "Cement", "index": "OTHER"},
    {"ticker": "STARCEMENT", "company_name": "Star Cement",             "sector": "Cement", "index": "OTHER"},

    # ── POWER & UTILITIES (10) ──────────────────────────────────────────────
    {"ticker": "NTPC",       "company_name": "NTPC",                 "sector": "Power", "index": "NIFTY50"},
    {"ticker": "POWERGRID",  "company_name": "Power Grid Corp",      "sector": "Power", "index": "NIFTY50"},
    {"ticker": "TATAPOWER",  "company_name": "Tata Power",           "sector": "Power", "index": "NIFTYNEXT50"},
    {"ticker": "ADANIGREEN", "company_name": "Adani Green Energy",   "sector": "Power", "index": "NIFTYNEXT50"},
    {"ticker": "JSPL",       "company_name": "Jindal Steel & Power", "sector": "Power", "index": "NIFTYNEXT50"},
    {"ticker": "NHPC",       "company_name": "NHPC",                 "sector": "Power", "index": "NIFTYNEXT50"},
    {"ticker": "TORNTPOWER", "company_name": "Torrent Power",        "sector": "Power", "index": "OTHER"},
    {"ticker": "CESC",       "company_name": "CESC",                 "sector": "Power", "index": "OTHER"},
    {"ticker": "SJVN",       "company_name": "SJVN",                 "sector": "Power", "index": "OTHER"},
    {"ticker": "RPOWER",     "company_name": "Reliance Power",       "sector": "Power", "index": "OTHER"},

    # ── CHEMICALS (13) ──────────────────────────────────────────────────────
    {"ticker": "UPL",        "company_name": "UPL Limited",                      "sector": "Chemicals", "index": "NIFTY50"},
    {"ticker": "SRF",        "company_name": "SRF Limited",                      "sector": "Chemicals", "index": "NIFTYNEXT50"},
    {"ticker": "PIIND",      "company_name": "PI Industries",                    "sector": "Chemicals", "index": "NIFTYNEXT50"},
    {"ticker": "TATACHEM",   "company_name": "Tata Chemicals",                   "sector": "Chemicals", "index": "NIFTYNEXT50"},
    {"ticker": "DEEPAKNTR",  "company_name": "Deepak Nitrite",                   "sector": "Chemicals", "index": "OTHER"},
    {"ticker": "AARTI",      "company_name": "Aarti Industries",                 "sector": "Chemicals", "index": "OTHER"},
    {"ticker": "NAVINFLUOR", "company_name": "Navin Fluorine International",     "sector": "Chemicals", "index": "OTHER"},
    {"ticker": "VINATI",     "company_name": "Vinati Organics",                  "sector": "Chemicals", "index": "OTHER"},
    {"ticker": "GALAXYSURF", "company_name": "Galaxy Surfactants",               "sector": "Chemicals", "index": "OTHER"},
    {"ticker": "CLEAN",      "company_name": "Clean Science and Technology",     "sector": "Chemicals", "index": "OTHER"},
    {"ticker": "ALKYLAMINE", "company_name": "Alkyl Amines Chemicals",           "sector": "Chemicals", "index": "OTHER"},
    {"ticker": "FINEORG",    "company_name": "Fine Organics Industries",         "sector": "Chemicals", "index": "OTHER"},
    {"ticker": "SUDARSCHEM", "company_name": "Sudarshan Chemical Industries",    "sector": "Chemicals", "index": "OTHER"},

    # ── HEALTHCARE / DIAGNOSTICS (10) ───────────────────────────────────────
    {"ticker": "APOLLOHOSP", "company_name": "Apollo Hospitals",           "sector": "Healthcare", "index": "NIFTY50"},
    {"ticker": "MAXHEALTH",  "company_name": "Max Healthcare",             "sector": "Healthcare", "index": "NIFTYNEXT50"},
    {"ticker": "FORTIS",     "company_name": "Fortis Healthcare",          "sector": "Healthcare", "index": "OTHER"},
    {"ticker": "METROPOLIS", "company_name": "Metropolis Healthcare",      "sector": "Healthcare", "index": "OTHER"},
    {"ticker": "LALPATHLAB", "company_name": "Dr Lal PathLabs",            "sector": "Healthcare", "index": "OTHER"},
    {"ticker": "NH",         "company_name": "Narayana Hrudayalaya",       "sector": "Healthcare", "index": "OTHER"},
    {"ticker": "MEDANTA",    "company_name": "Global Health (Medanta)",    "sector": "Healthcare", "index": "OTHER"},
    {"ticker": "RAINBOW",    "company_name": "Rainbow Children's Medicare","sector": "Healthcare", "index": "OTHER"},
    {"ticker": "THYROCARE",  "company_name": "Thyrocare Technologies",     "sector": "Healthcare", "index": "OTHER"},
    {"ticker": "KRSNAA",     "company_name": "Krsnaa Diagnostics",         "sector": "Healthcare", "index": "OTHER"},

    # ── INSURANCE (7) ───────────────────────────────────────────────────────
    {"ticker": "SBILIFE",    "company_name": "SBI Life Insurance",                    "sector": "Insurance", "index": "NIFTY50"},
    {"ticker": "HDFCLIFE",   "company_name": "HDFC Life Insurance",                   "sector": "Insurance", "index": "NIFTY50"},
    {"ticker": "LICI",       "company_name": "Life Insurance Corporation of India",   "sector": "Insurance", "index": "NIFTY50"},
    {"ticker": "ICICIGI",    "company_name": "ICICI Lombard General Insurance",       "sector": "Insurance", "index": "NIFTYNEXT50"},
    {"ticker": "STARHEALTH", "company_name": "Star Health and Allied Insurance",      "sector": "Insurance", "index": "OTHER"},
    {"ticker": "GICRE",      "company_name": "General Insurance Corp of India",      "sector": "Insurance", "index": "OTHER"},
    {"ticker": "NIACL",      "company_name": "New India Assurance",                  "sector": "Insurance", "index": "OTHER"},

    # ── CONSUMER DURABLES (8) ───────────────────────────────────────────────
    {"ticker": "DIXON",      "company_name": "Dixon Technologies",                       "sector": "Consumer Durables", "index": "NIFTYNEXT50"},
    {"ticker": "AMBER",      "company_name": "Amber Enterprises India",                  "sector": "Consumer Durables", "index": "OTHER"},
    {"ticker": "BLUESTAR",   "company_name": "Blue Star",                                "sector": "Consumer Durables", "index": "OTHER"},
    {"ticker": "CROMPTON",   "company_name": "Crompton Greaves Consumer Electricals",    "sector": "Consumer Durables", "index": "OTHER"},
    {"ticker": "VGUARD",     "company_name": "V-Guard Industries",                       "sector": "Consumer Durables", "index": "OTHER"},
    {"ticker": "BAJAJELE",   "company_name": "Bajaj Electricals",                        "sector": "Consumer Durables", "index": "OTHER"},
    {"ticker": "WHIRLPOOL",  "company_name": "Whirlpool of India",                       "sector": "Consumer Durables", "index": "OTHER"},
    {"ticker": "SYMPHONY",   "company_name": "Symphony",                                 "sector": "Consumer Durables", "index": "OTHER"},

    # ── TEXTILES (5) ────────────────────────────────────────────────────────
    {"ticker": "PAGEIND",    "company_name": "Page Industries (Jockey)", "sector": "Textiles", "index": "NIFTYNEXT50"},
    {"ticker": "WELSPUNIND", "company_name": "Welspun India",            "sector": "Textiles", "index": "OTHER"},
    {"ticker": "RAYMOND",    "company_name": "Raymond",                  "sector": "Textiles", "index": "OTHER"},
    {"ticker": "TRIDENT",    "company_name": "Trident",                  "sector": "Textiles", "index": "OTHER"},
    {"ticker": "VARDHMAN",   "company_name": "Vardhman Textiles",        "sector": "Textiles", "index": "OTHER"},

    # ── MEDIA & ENTERTAINMENT (4) ───────────────────────────────────────────
    {"ticker": "SUNTV",      "company_name": "Sun TV Network",                    "sector": "Media", "index": "NIFTYNEXT50"},
    {"ticker": "ZEEL",       "company_name": "Zee Entertainment Enterprises",     "sector": "Media", "index": "OTHER"},
    {"ticker": "PVRINOX",    "company_name": "PVR INOX",                          "sector": "Media", "index": "OTHER"},
    {"ticker": "NAZARA",     "company_name": "Nazara Technologies",               "sector": "Media", "index": "OTHER"},

    # ── LOGISTICS (5) ───────────────────────────────────────────────────────
    {"ticker": "CONCOR",     "company_name": "Container Corp of India", "sector": "Logistics", "index": "NIFTYNEXT50"},
    {"ticker": "BLUEDART",   "company_name": "Blue Dart Express",       "sector": "Logistics", "index": "OTHER"},
    {"ticker": "VRLLOG",     "company_name": "VRL Logistics",           "sector": "Logistics", "index": "OTHER"},
    {"ticker": "MAHLOG",     "company_name": "Mahindra Logistics",      "sector": "Logistics", "index": "OTHER"},
    {"ticker": "GESHIP",     "company_name": "Great Eastern Shipping",  "sector": "Logistics", "index": "OTHER"},

    # ── FERTILISERS & AGROCHEMICALS (5) ─────────────────────────────────────
    {"ticker": "COROMANDEL", "company_name": "Coromandel International",            "sector": "Fertilisers", "index": "NIFTYNEXT50"},
    {"ticker": "CHAMBLFERT", "company_name": "Chambal Fertilisers & Chemicals",     "sector": "Fertilisers", "index": "OTHER"},
    {"ticker": "DEEPAKFERT", "company_name": "Deepak Fertilisers",                  "sector": "Fertilisers", "index": "OTHER"},
    {"ticker": "GNFC",       "company_name": "Gujarat Narmada Valley Fertilizers",  "sector": "Fertilisers", "index": "OTHER"},
    {"ticker": "NFL",        "company_name": "National Fertilizers",                "sector": "Fertilisers", "index": "OTHER"},

    # ── AVIATION (2) ────────────────────────────────────────────────────────
    {"ticker": "INTERGLOBE", "company_name": "InterGlobe Aviation (IndiGo)", "sector": "Aviation", "index": "NIFTYNEXT50"},
    {"ticker": "SPICEJET",   "company_name": "SpiceJet",                     "sector": "Aviation", "index": "OTHER"},

    # ── INDEX ────────────────────────────────────────────────────────────────
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
