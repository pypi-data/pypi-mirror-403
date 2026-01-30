"""
Local SQLite cache for congressional trades data.

Provides fast local access without hitting the source on every request.
Cache can be refreshed manually or auto-expires after a configurable period.
"""

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterator, Optional

from .models import Trade, Politician, Chamber, TransactionType, Party


def get_cache_dir() -> Path:
    """Get the cache directory, creating if needed."""
    cache_dir = Path.home() / ".cache" / "congressional-trades"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_db_path() -> Path:
    """Get path to SQLite database."""
    return get_cache_dir() / "trades.db"


class TradeCache:
    """
    SQLite-backed cache for congressional trades.

    Usage:
        cache = TradeCache()
        cache.add_trades(trades)
        trades = cache.get_trades(ticker="NVDA")
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                politician TEXT NOT NULL,
                chamber TEXT NOT NULL,
                state TEXT NOT NULL,
                party TEXT,
                ticker TEXT,
                asset_name TEXT NOT NULL,
                asset_type TEXT,
                transaction_type TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                disclosure_date TEXT NOT NULL,
                amount_min INTEGER NOT NULL,
                amount_max INTEGER NOT NULL,
                comment TEXT,
                owner TEXT,
                source_url TEXT NOT NULL,
                report_id TEXT,
                scraped_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_trades_politician ON trades(politician);
            CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker);
            CREATE INDEX IF NOT EXISTS idx_trades_transaction_date ON trades(transaction_date);
            CREATE INDEX IF NOT EXISTS idx_trades_chamber ON trades(chamber);

            CREATE TABLE IF NOT EXISTS politicians (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                chamber TEXT NOT NULL,
                state TEXT NOT NULL,
                party TEXT,
                total_trades INTEGER DEFAULT 0,
                last_trade_date TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        conn.close()

    def add_trades(self, trades: list[Trade]) -> int:
        """
        Add trades to cache, updating existing entries.

        Returns number of trades added/updated.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        count = 0

        for trade in trades:
            cursor.execute("""
                INSERT OR REPLACE INTO trades (
                    id, politician, chamber, state, party, ticker, asset_name,
                    asset_type, transaction_type, transaction_date, disclosure_date,
                    amount_min, amount_max, comment, owner, source_url, report_id, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.id,
                trade.politician,
                trade.chamber.value,
                trade.state,
                trade.party.value if trade.party else None,
                trade.ticker,
                trade.asset_name,
                trade.asset_type,
                trade.transaction_type.value,
                trade.transaction_date.isoformat(),
                trade.disclosure_date.isoformat(),
                trade.amount_min,
                trade.amount_max,
                trade.comment,
                trade.owner,
                trade.source_url,
                trade.report_id,
                trade.scraped_at.isoformat(),
            ))
            count += 1

        # Update last scrape time
        cursor.execute("""
            INSERT OR REPLACE INTO meta (key, value, updated_at)
            VALUES ('last_scrape', ?, ?)
        """, (datetime.now().isoformat(), datetime.now().isoformat()))

        conn.commit()
        conn.close()

        # Update politician stats
        self._update_politician_stats()

        return count

    def _update_politician_stats(self):
        """Update politician stats from trades."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO politicians (id, name, chamber, state, party, total_trades, last_trade_date, updated_at)
            SELECT
                substr(hex(randomblob(6)), 1, 12) as id,
                politician as name,
                chamber,
                state,
                party,
                COUNT(*) as total_trades,
                MAX(transaction_date) as last_trade_date,
                datetime('now') as updated_at
            FROM trades
            GROUP BY politician, chamber
        """)

        conn.commit()
        conn.close()

    def get_trades(
        self,
        chamber: Optional[str] = None,
        politician: Optional[str] = None,
        ticker: Optional[str] = None,
        start_date: Optional[str | date] = None,
        end_date: Optional[str | date] = None,
        transaction_type: Optional[str] = None,
        limit: int = 1000,
    ) -> list[Trade]:
        """
        Query trades from cache with optional filters.

        Args:
            chamber: "senate" or "house"
            politician: Partial name match (case-insensitive)
            ticker: Exact ticker match
            start_date: Filter trades on or after this date
            end_date: Filter trades on or before this date
            transaction_type: "purchase", "sale", etc.
            limit: Maximum number of results

        Returns:
            List of Trade objects matching the criteria
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        query = "SELECT * FROM trades WHERE 1=1"
        params = []

        if chamber:
            query += " AND chamber = ?"
            params.append(chamber.lower())

        if politician:
            query += " AND politician LIKE ?"
            params.append(f"%{politician}%")

        if ticker:
            query += " AND ticker = ?"
            params.append(ticker.upper())

        if start_date:
            if isinstance(start_date, date):
                start_date = start_date.isoformat()
            query += " AND transaction_date >= ?"
            params.append(start_date)

        if end_date:
            if isinstance(end_date, date):
                end_date = end_date.isoformat()
            query += " AND transaction_date <= ?"
            params.append(end_date)

        if transaction_type:
            query += " AND transaction_type = ?"
            params.append(transaction_type.lower())

        query += " ORDER BY transaction_date DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_trade(row) for row in rows]

    def _row_to_trade(self, row: sqlite3.Row) -> Trade:
        """Convert database row to Trade model."""
        return Trade(
            politician=row["politician"],
            chamber=Chamber(row["chamber"]),
            state=row["state"],
            party=Party(row["party"]) if row["party"] else None,
            ticker=row["ticker"],
            asset_name=row["asset_name"],
            asset_type=row["asset_type"] or "Stock",
            transaction_type=TransactionType(row["transaction_type"]),
            transaction_date=date.fromisoformat(row["transaction_date"]),
            disclosure_date=date.fromisoformat(row["disclosure_date"]),
            amount_min=row["amount_min"],
            amount_max=row["amount_max"],
            comment=row["comment"],
            owner=row["owner"],
            source_url=row["source_url"],
            report_id=row["report_id"],
            scraped_at=date.fromisoformat(row["scraped_at"]),
        )

    def get_politicians(self, chamber: Optional[str] = None) -> list[Politician]:
        """Get list of politicians with trade activity."""
        conn = self._get_conn()
        cursor = conn.cursor()

        query = "SELECT * FROM politicians WHERE 1=1"
        params = []

        if chamber:
            query += " AND chamber = ?"
            params.append(chamber.lower())

        query += " ORDER BY total_trades DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            Politician(
                name=row["name"],
                chamber=Chamber(row["chamber"]),
                state=row["state"],
                party=Party(row["party"]) if row["party"] else None,
                total_trades=row["total_trades"],
                last_trade_date=date.fromisoformat(row["last_trade_date"]) if row["last_trade_date"] else None,
            )
            for row in rows
        ]

    def get_last_scrape(self) -> Optional[datetime]:
        """Get timestamp of last scrape."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM meta WHERE key = 'last_scrape'")
        row = cursor.fetchone()
        conn.close()

        if row:
            return datetime.fromisoformat(row["value"])
        return None

    def is_stale(self, max_age_hours: int = 24) -> bool:
        """Check if cache is stale and needs refresh."""
        last_scrape = self.get_last_scrape()
        if not last_scrape:
            return True
        return datetime.now() - last_scrape > timedelta(hours=max_age_hours)

    def clear(self):
        """Clear all cached data."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trades")
        cursor.execute("DELETE FROM politicians")
        cursor.execute("DELETE FROM meta")
        conn.commit()
        conn.close()

    def stats(self) -> dict:
        """Get cache statistics."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM trades")
        trade_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM politicians")
        politician_count = cursor.fetchone()["count"]

        cursor.execute("SELECT MIN(transaction_date) as min_date, MAX(transaction_date) as max_date FROM trades")
        date_range = cursor.fetchone()

        conn.close()

        return {
            "trade_count": trade_count,
            "politician_count": politician_count,
            "date_range": {
                "min": date_range["min_date"],
                "max": date_range["max_date"],
            },
            "last_scrape": self.get_last_scrape(),
            "is_stale": self.is_stale(),
            "db_path": str(self.db_path),
        }
