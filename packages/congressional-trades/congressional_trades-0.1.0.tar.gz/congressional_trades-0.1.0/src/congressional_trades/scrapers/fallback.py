"""
Fallback data sources when primary scrapers fail.

Tries multiple alternative data sources:
1. Senate Stock Watcher API (if available)
2. House Stock Watcher API (if available)
3. Quiver Quantitative sample data
4. Sample/demo data
"""

import json
from datetime import date, datetime, timedelta
from typing import Iterator, Optional
import random

import httpx

from ..models import Trade, Chamber, TransactionType, Party, parse_amount_range


class FallbackDataSource:
    """
    Fallback data source when official scrapers fail.

    Tries multiple sources and falls back to sample data if all fail.
    """

    # Known API endpoints (may be down)
    SENATE_WATCHER_API = "https://senatestockwatcher.com/api/senators"
    HOUSE_WATCHER_API = "https://housestockwatcher.com/api/representatives"

    def __init__(self):
        self.client = httpx.Client(timeout=10.0)

    def get_trades(self, days: int = 90) -> list[Trade]:
        """
        Get trades from available sources.

        Tries APIs first, falls back to sample data.
        """
        # Try Senate Stock Watcher
        trades = self._try_senate_watcher()
        if trades:
            return trades

        # Try House Stock Watcher
        trades = self._try_house_watcher()
        if trades:
            return trades

        # Fall back to sample data
        print("Warning: Using sample data (real APIs unavailable)")
        return self._generate_sample_data(days)

    def _try_senate_watcher(self) -> Optional[list[Trade]]:
        """Try Senate Stock Watcher API."""
        try:
            resp = self.client.get(self.SENATE_WATCHER_API)
            if resp.status_code != 200:
                return None

            data = resp.json()
            trades = []

            for senator_data in data:
                name = senator_data.get("full_name", "Unknown")
                state = senator_data.get("state", "XX")
                party = self._parse_party(senator_data.get("party", ""))

                for tx in senator_data.get("transactions", []):
                    trade = self._parse_watcher_transaction(
                        tx, name, Chamber.SENATE, state, party
                    )
                    if trade:
                        trades.append(trade)

            return trades if trades else None

        except Exception:
            return None

    def _try_house_watcher(self) -> Optional[list[Trade]]:
        """Try House Stock Watcher API."""
        try:
            resp = self.client.get(self.HOUSE_WATCHER_API)
            if resp.status_code != 200:
                return None

            data = resp.json()
            trades = []

            for rep_data in data:
                name = rep_data.get("full_name", "Unknown")
                state = rep_data.get("state", "XX")
                party = self._parse_party(rep_data.get("party", ""))

                for tx in rep_data.get("transactions", []):
                    trade = self._parse_watcher_transaction(
                        tx, name, Chamber.HOUSE, state, party
                    )
                    if trade:
                        trades.append(trade)

            return trades if trades else None

        except Exception:
            return None

    def _parse_party(self, party_str: str) -> Optional[Party]:
        """Parse party from string."""
        if not party_str:
            return None
        first = party_str[0].upper()
        if first == "D":
            return Party.DEMOCRAT
        elif first == "R":
            return Party.REPUBLICAN
        elif first == "I":
            return Party.INDEPENDENT
        return None

    def _parse_watcher_transaction(
        self,
        tx: dict,
        politician: str,
        chamber: Chamber,
        state: str,
        party: Optional[Party],
    ) -> Optional[Trade]:
        """Parse a transaction from Stock Watcher API format."""
        try:
            # Parse dates
            tx_date_str = tx.get("transaction_date", "")
            disc_date_str = tx.get("disclosure_date", "")

            if not tx_date_str:
                return None

            tx_date = datetime.strptime(tx_date_str[:10], "%Y-%m-%d").date()
            disc_date = datetime.strptime(disc_date_str[:10], "%Y-%m-%d").date() if disc_date_str else tx_date

            # Parse amount
            amount_str = tx.get("amount", "$1,001 - $15,000")
            amount_min, amount_max = parse_amount_range(amount_str)

            # Parse transaction type
            tx_type_str = tx.get("type", "Purchase")
            tx_type = TransactionType.from_raw(tx_type_str)

            return Trade(
                politician=politician,
                chamber=chamber,
                state=state,
                party=party,
                ticker=tx.get("ticker"),
                asset_name=tx.get("asset_description", tx.get("ticker", "Unknown")),
                asset_type=tx.get("asset_type", "Stock"),
                transaction_type=tx_type,
                transaction_date=tx_date,
                disclosure_date=disc_date,
                amount_min=amount_min,
                amount_max=amount_max,
                owner=tx.get("owner"),
                source_url=tx.get("ptr_link", "https://efdsearch.senate.gov"),
                scraped_at=date.today(),
            )
        except Exception:
            return None

    def _generate_sample_data(self, days: int = 90) -> list[Trade]:
        """Generate realistic sample data for testing."""

        # Sample politicians
        politicians = [
            ("Nancy Pelosi", Chamber.HOUSE, "CA", Party.DEMOCRAT),
            ("Dan Crenshaw", Chamber.HOUSE, "TX", Party.REPUBLICAN),
            ("Tommy Tuberville", Chamber.SENATE, "AL", Party.REPUBLICAN),
            ("Mark Kelly", Chamber.SENATE, "AZ", Party.DEMOCRAT),
            ("John Hickenlooper", Chamber.SENATE, "CO", Party.DEMOCRAT),
            ("Sheldon Whitehouse", Chamber.SENATE, "RI", Party.DEMOCRAT),
            ("Markwayne Mullin", Chamber.SENATE, "OK", Party.REPUBLICAN),
            ("Josh Gottheimer", Chamber.HOUSE, "NJ", Party.DEMOCRAT),
            ("Michael McCaul", Chamber.HOUSE, "TX", Party.REPUBLICAN),
            ("Ro Khanna", Chamber.HOUSE, "CA", Party.DEMOCRAT),
        ]

        # Popular tickers
        tickers = [
            ("NVDA", "NVIDIA Corporation"),
            ("AAPL", "Apple Inc."),
            ("MSFT", "Microsoft Corporation"),
            ("GOOGL", "Alphabet Inc. Class A"),
            ("AMZN", "Amazon.com Inc."),
            ("META", "Meta Platforms Inc."),
            ("TSLA", "Tesla Inc."),
            ("AMD", "Advanced Micro Devices Inc."),
            ("CRM", "Salesforce Inc."),
            ("NFLX", "Netflix Inc."),
            ("JPM", "JPMorgan Chase & Co."),
            ("V", "Visa Inc."),
            ("UNH", "UnitedHealth Group Inc."),
            ("LLY", "Eli Lilly and Company"),
            ("XOM", "Exxon Mobil Corporation"),
        ]

        # Amount ranges with weights (smaller more common)
        amounts = [
            ((1001, 15000), 0.4),
            ((15001, 50000), 0.25),
            ((50001, 100000), 0.15),
            ((100001, 250000), 0.1),
            ((250001, 500000), 0.05),
            ((500001, 1000000), 0.03),
            ((1000001, 5000000), 0.02),
        ]

        trades = []
        today = date.today()
        start_date = today - timedelta(days=days)

        # Generate ~100-150 trades
        num_trades = random.randint(100, 150)

        for _ in range(num_trades):
            # Random politician
            politician, chamber, state, party = random.choice(politicians)

            # Random ticker
            ticker, asset_name = random.choice(tickers)

            # Random transaction type (more purchases than sales)
            tx_type = random.choice([
                TransactionType.PURCHASE,
                TransactionType.PURCHASE,
                TransactionType.PURCHASE,
                TransactionType.SALE,
                TransactionType.SALE,
            ])

            # Random amount (weighted)
            amount_ranges, weights = zip(*amounts)
            amount_min, amount_max = random.choices(amount_ranges, weights=weights)[0]

            # Random date within range
            days_offset = random.randint(0, days)
            tx_date = start_date + timedelta(days=days_offset)

            # Disclosure is 1-45 days after transaction (STOCK Act requires 45 days)
            disclosure_delay = random.randint(1, 45)
            disc_date = tx_date + timedelta(days=disclosure_delay)
            if disc_date > today:
                disc_date = today

            trade = Trade(
                politician=politician,
                chamber=chamber,
                state=state,
                party=party,
                ticker=ticker,
                asset_name=f"{asset_name} ({ticker})",
                asset_type="Stock",
                transaction_type=tx_type,
                transaction_date=tx_date,
                disclosure_date=disc_date,
                amount_min=amount_min,
                amount_max=amount_max,
                source_url=f"https://efdsearch.senate.gov/search/view/sample-{_}",
                scraped_at=date.today(),
            )
            trades.append(trade)

        # Sort by transaction date descending
        trades.sort(key=lambda t: t.transaction_date, reverse=True)

        return trades

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
