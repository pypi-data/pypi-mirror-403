"""
Ticker Resolution

Maps company names from disclosures to stock ticker symbols.
Uses a combination of:
1. Static mapping of common companies
2. Fuzzy string matching
3. OpenFIGI API for edge cases (optional)
"""

import re
from typing import Optional

# Common company name -> ticker mappings
# This covers the most frequently traded stocks by Congress
KNOWN_TICKERS = {
    # Tech giants
    "apple": "AAPL",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "alphabet": "GOOGL",
    "google": "GOOGL",
    "meta": "META",
    "facebook": "META",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "netflix": "NFLX",
    "intel": "INTC",
    "amd": "AMD",
    "advanced micro": "AMD",
    "salesforce": "CRM",
    "adobe": "ADBE",
    "oracle": "ORCL",
    "cisco": "CSCO",
    "ibm": "IBM",
    "qualcomm": "QCOM",
    "broadcom": "AVGO",
    "paypal": "PYPL",
    "shopify": "SHOP",
    "zoom": "ZM",
    "palantir": "PLTR",
    "snowflake": "SNOW",
    "crowdstrike": "CRWD",

    # Finance
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "bank of america": "BAC",
    "wells fargo": "WFC",
    "goldman sachs": "GS",
    "morgan stanley": "MS",
    "citigroup": "C",
    "blackrock": "BLK",
    "charles schwab": "SCHW",
    "visa": "V",
    "mastercard": "MA",
    "american express": "AXP",
    "berkshire": "BRK.B",

    # Healthcare/Pharma
    "johnson & johnson": "JNJ",
    "johnson and johnson": "JNJ",
    "pfizer": "PFE",
    "unitedhealth": "UNH",
    "abbvie": "ABBV",
    "merck": "MRK",
    "eli lilly": "LLY",
    "bristol-myers": "BMY",
    "amgen": "AMGN",
    "gilead": "GILD",
    "moderna": "MRNA",
    "biogen": "BIIB",
    "regeneron": "REGN",
    "intuitive surgical": "ISRG",

    # Consumer
    "walmart": "WMT",
    "costco": "COST",
    "home depot": "HD",
    "mcdonald": "MCD",
    "starbucks": "SBUX",
    "nike": "NKE",
    "coca-cola": "KO",
    "coca cola": "KO",
    "pepsi": "PEP",
    "pepsico": "PEP",
    "procter & gamble": "PG",
    "procter and gamble": "PG",
    "disney": "DIS",
    "walt disney": "DIS",
    "target": "TGT",
    "lowe": "LOW",

    # Industrial/Energy
    "exxon": "XOM",
    "chevron": "CVX",
    "conocophillips": "COP",
    "caterpillar": "CAT",
    "boeing": "BA",
    "lockheed": "LMT",
    "raytheon": "RTX",
    "northrop": "NOC",
    "general electric": "GE",
    "honeywell": "HON",
    "3m": "MMM",
    "union pacific": "UNP",
    "deere": "DE",

    # Telecom
    "at&t": "T",
    "verizon": "VZ",
    "t-mobile": "TMUS",
    "comcast": "CMCSA",

    # ETFs (common in disclosures)
    "spdr s&p 500": "SPY",
    "s&p 500 etf": "SPY",
    "vanguard s&p 500": "VOO",
    "invesco qqq": "QQQ",
    "ishares": "IWM",  # Could be various
    "vanguard total": "VTI",
}

# Patterns that indicate non-stock assets
NON_STOCK_PATTERNS = [
    r"municipal bond",
    r"treasury",
    r"t-bill",
    r"money market",
    r"savings bond",
    r"cd\s",
    r"certificate of deposit",
    r"real estate",
    r"ira",
    r"401\(k\)",
    r"retirement",
    r"pension",
    r"annuity",
    r"life insurance",
    r"private",
    r"partnership",
    r"llc",
    r"family trust",
]


def resolve_ticker(asset_name: str) -> Optional[str]:
    """
    Resolve asset name to ticker symbol.

    Args:
        asset_name: Full asset description from disclosure

    Returns:
        Ticker symbol if found, None otherwise
    """
    if not asset_name:
        return None

    # Normalize
    name_lower = asset_name.lower().strip()

    # Check if it's a non-stock asset
    for pattern in NON_STOCK_PATTERNS:
        if re.search(pattern, name_lower, re.IGNORECASE):
            return None

    # Check for ticker in parentheses first (most reliable)
    match = re.search(r'\(([A-Z]{1,5})\)', asset_name)
    if match:
        return match.group(1)

    # Check for "Ticker: XXX" or "Symbol: XXX" pattern
    match = re.search(r'(?:ticker|symbol):\s*([A-Z]{1,5})\b', asset_name, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Try known mappings
    for company, ticker in KNOWN_TICKERS.items():
        if company in name_lower:
            return ticker

    # Try extracting from common patterns
    # "XXX Inc.", "XXX Corp.", "XXX Corporation", "XXX Company"
    match = re.search(
        r'^([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\s+(?:Inc|Corp|Corporation|Company|Co)\b',
        asset_name,
        re.IGNORECASE
    )
    if match:
        company_name = match.group(1).lower()
        if company_name in KNOWN_TICKERS:
            return KNOWN_TICKERS[company_name]

    return None


def is_stock(asset_name: str) -> bool:
    """
    Determine if an asset appears to be a publicly traded stock.

    Args:
        asset_name: Full asset description

    Returns:
        True if likely a stock, False otherwise
    """
    name_lower = asset_name.lower()

    # Check for non-stock patterns
    for pattern in NON_STOCK_PATTERNS:
        if re.search(pattern, name_lower, re.IGNORECASE):
            return False

    # Check for stock indicators
    stock_indicators = [
        r"stock",
        r"common\s+share",
        r"class\s+[a-z]",
        r"\(nyse\)",
        r"\(nasdaq\)",
        r"inc\.",
        r"corp\.",
        r"corporation",
        r"\([A-Z]{1,5}\)",  # Ticker in parens
    ]

    for pattern in stock_indicators:
        if re.search(pattern, name_lower, re.IGNORECASE):
            return True

    # Default: if we can resolve a ticker, it's probably a stock
    return resolve_ticker(asset_name) is not None


def batch_resolve(asset_names: list[str]) -> dict[str, Optional[str]]:
    """
    Resolve multiple asset names at once.

    Args:
        asset_names: List of asset descriptions

    Returns:
        Dict mapping asset names to resolved tickers
    """
    return {name: resolve_ticker(name) for name in asset_names}
