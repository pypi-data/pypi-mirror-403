"""
Data models for congressional trades.
"""

from datetime import date
from enum import Enum
from typing import Optional
import hashlib

from pydantic import BaseModel, Field, computed_field


class Chamber(str, Enum):
    """Congressional chamber."""
    SENATE = "senate"
    HOUSE = "house"


class TransactionType(str, Enum):
    """Type of financial transaction."""
    PURCHASE = "purchase"
    SALE = "sale"
    SALE_PARTIAL = "sale_partial"
    SALE_FULL = "sale_full"
    EXCHANGE = "exchange"
    RECEIVED = "received"  # Gifts, inheritance

    @classmethod
    def from_raw(cls, raw: str) -> "TransactionType":
        """Parse raw transaction type string from disclosure."""
        raw_lower = raw.lower().strip()

        if "purchase" in raw_lower or "buy" in raw_lower:
            return cls.PURCHASE
        elif "sale" in raw_lower:
            if "partial" in raw_lower:
                return cls.SALE_PARTIAL
            elif "full" in raw_lower:
                return cls.SALE_FULL
            return cls.SALE
        elif "exchange" in raw_lower:
            return cls.EXCHANGE
        elif "received" in raw_lower or "gift" in raw_lower:
            return cls.RECEIVED

        # Default to purchase if unclear
        return cls.PURCHASE


class Party(str, Enum):
    """Political party."""
    DEMOCRAT = "D"
    REPUBLICAN = "R"
    INDEPENDENT = "I"


class Trade(BaseModel):
    """
    A single stock transaction by a member of Congress.

    Represents one row from a financial disclosure report.
    """
    # Politician info
    politician: str = Field(description="Full name of the politician")
    chamber: Chamber
    state: str = Field(min_length=2, max_length=2, description="Two-letter state code")
    party: Optional[Party] = None

    # Asset info
    ticker: Optional[str] = Field(default=None, description="Stock ticker if resolved")
    asset_name: str = Field(description="Full asset description from disclosure")
    asset_type: str = Field(default="Stock", description="Type of asset")

    # Transaction details
    transaction_type: TransactionType
    transaction_date: date = Field(description="Date the trade occurred")
    disclosure_date: date = Field(description="Date the trade was disclosed")

    # Amount range (Congress reports in ranges, not exact amounts)
    amount_min: int = Field(ge=0, description="Minimum transaction amount")
    amount_max: int = Field(ge=0, description="Maximum transaction amount")

    # Optional fields
    comment: Optional[str] = None
    owner: Optional[str] = Field(default=None, description="SP (spouse), JT (joint), DC (child)")

    # Metadata
    source_url: str = Field(description="URL to the original disclosure")
    report_id: Optional[str] = Field(default=None, description="Unique report identifier")
    scraped_at: date = Field(default_factory=date.today)

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID for this trade."""
        unique_str = f"{self.politician}|{self.transaction_date}|{self.asset_name}|{self.amount_min}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]

    @computed_field
    @property
    def amount_midpoint(self) -> int:
        """Midpoint of the amount range."""
        return (self.amount_min + self.amount_max) // 2

    @computed_field
    @property
    def disclosure_delay_days(self) -> int:
        """Days between transaction and disclosure."""
        return (self.disclosure_date - self.transaction_date).days


class Politician(BaseModel):
    """A member of Congress who has filed financial disclosures."""
    name: str
    chamber: Chamber
    state: str
    party: Optional[Party] = None

    # Stats
    total_trades: int = 0
    last_trade_date: Optional[date] = None

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID."""
        return hashlib.md5(f"{self.name}|{self.chamber}".encode()).hexdigest()[:12]


# Amount ranges used in disclosures
AMOUNT_RANGES = {
    "$1,001 - $15,000": (1001, 15000),
    "$15,001 - $50,000": (15001, 50000),
    "$50,001 - $100,000": (50001, 100000),
    "$100,001 - $250,000": (100001, 250000),
    "$250,001 - $500,000": (250001, 500000),
    "$500,001 - $1,000,000": (500001, 1000000),
    "$1,000,001 - $5,000,000": (1000001, 5000000),
    "$5,000,001 - $25,000,000": (5000001, 25000000),
    "$25,000,001 - $50,000,000": (25000001, 50000000),
    "Over $50,000,000": (50000001, 100000000),
}


def parse_amount_range(raw: str) -> tuple[int, int]:
    """Parse amount range string to (min, max) tuple."""
    raw = raw.strip()

    # Try exact match first
    if raw in AMOUNT_RANGES:
        return AMOUNT_RANGES[raw]

    # Try partial match
    for key, value in AMOUNT_RANGES.items():
        if key.lower() in raw.lower() or raw.lower() in key.lower():
            return value

    # Try to parse custom range
    import re
    numbers = re.findall(r'[\d,]+', raw)
    if len(numbers) >= 2:
        min_val = int(numbers[0].replace(',', ''))
        max_val = int(numbers[1].replace(',', ''))
        return (min_val, max_val)
    elif len(numbers) == 1:
        val = int(numbers[0].replace(',', ''))
        return (val, val)

    # Default to smallest range
    return (1001, 15000)
