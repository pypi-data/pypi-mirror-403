"""
Congressional Trades - Scrape and analyze stock trades by members of US Congress.

Usage:
    from congressional_trades import get_trades, get_politicians

    # Get all trades
    trades = get_trades()

    # Filter by various criteria
    trades = get_trades(
        chamber="senate",
        ticker="NVDA",
        start_date="2024-01-01",
    )

    # Get as DataFrame
    df = get_trades(as_dataframe=True)
"""

from datetime import date
from typing import Optional, Union

from .models import Trade, Politician, Chamber, TransactionType, Party
from .cache import TradeCache
from .scrapers import SenateScraper, FallbackDataSource
from .ticker_resolver import resolve_ticker, is_stock

__version__ = "0.1.0"

__all__ = [
    # Main functions
    "get_trades",
    "get_politicians",
    "refresh",
    # Models
    "Trade",
    "Politician",
    "Chamber",
    "TransactionType",
    "Party",
    # Utils
    "resolve_ticker",
    "is_stock",
]

# Module-level cache instance
_cache: Optional[TradeCache] = None


def _get_cache() -> TradeCache:
    """Get or create cache instance."""
    global _cache
    if _cache is None:
        _cache = TradeCache()
    return _cache


def get_trades(
    chamber: Optional[str] = None,
    politician: Optional[str] = None,
    ticker: Optional[str] = None,
    start_date: Optional[Union[str, date]] = None,
    end_date: Optional[Union[str, date]] = None,
    transaction_type: Optional[str] = None,
    limit: int = 1000,
    refresh: bool = False,
    as_dataframe: bool = False,
) -> Union[list[Trade], "pandas.DataFrame"]:
    """
    Get congressional stock trades.

    Args:
        chamber: Filter by "senate" or "house"
        politician: Filter by politician name (partial match)
        ticker: Filter by stock ticker (exact match)
        start_date: Filter trades on or after this date
        end_date: Filter trades on or before this date
        transaction_type: Filter by "purchase" or "sale"
        limit: Maximum number of results (default 1000)
        refresh: Force refresh from source before querying
        as_dataframe: Return pandas DataFrame instead of list

    Returns:
        List of Trade objects, or DataFrame if as_dataframe=True

    Example:
        >>> trades = get_trades(ticker="NVDA", start_date="2024-01-01")
        >>> for trade in trades:
        ...     print(f"{trade.politician}: {trade.transaction_type.value}")
    """
    cache = _get_cache()

    # Refresh if requested or if cache is empty/stale
    if refresh or (cache.is_stale() and cache.stats()["trade_count"] == 0):
        _refresh_cache()

    trades = cache.get_trades(
        chamber=chamber,
        politician=politician,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        limit=limit,
    )

    if as_dataframe:
        import pandas as pd
        return pd.DataFrame([t.model_dump() for t in trades])

    return trades


def get_politicians(
    chamber: Optional[str] = None,
) -> list[Politician]:
    """
    Get list of politicians with trading activity.

    Args:
        chamber: Filter by "senate" or "house"

    Returns:
        List of Politician objects sorted by trade count

    Example:
        >>> politicians = get_politicians(chamber="senate")
        >>> for pol in politicians[:10]:
        ...     print(f"{pol.name}: {pol.total_trades} trades")
    """
    cache = _get_cache()
    return cache.get_politicians(chamber=chamber)


def refresh(days: int = 30, force: bool = False) -> int:
    """
    Refresh cache from source.

    Args:
        days: How many days back to fetch
        force: Refresh even if cache is fresh

    Returns:
        Number of trades added/updated
    """
    cache = _get_cache()

    if not force and not cache.is_stale():
        return 0

    return _refresh_cache(days=days)


def _refresh_cache(days: int = 90) -> int:
    """Internal function to refresh cache."""
    cache = _get_cache()
    trades = []

    # Try Senate scraper first
    try:
        with SenateScraper() as scraper:
            trades = list(scraper.scrape_recent(days=days))
    except Exception as e:
        print(f"Senate scraper failed: {e}")

    # Fall back to alternative sources if needed
    if not trades:
        with FallbackDataSource() as fallback:
            trades = fallback.get_trades(days=days)

    if trades:
        return cache.add_trades(trades)
    return 0


def stats() -> dict:
    """
    Get cache statistics.

    Returns:
        Dict with trade_count, politician_count, date_range, etc.
    """
    return _get_cache().stats()
