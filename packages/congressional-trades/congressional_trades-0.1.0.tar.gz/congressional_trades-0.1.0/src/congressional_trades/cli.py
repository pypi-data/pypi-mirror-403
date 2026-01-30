"""
Command Line Interface for congressional-trades.

Usage:
    congressional-trades list [--ticker TICKER] [--since DATE] [--chamber CHAMBER]
    congressional-trades export FILE [--format FORMAT]
    congressional-trades refresh [--days DAYS]
    congressional-trades stats
"""

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from typing import Optional

from .cache import TradeCache
from .scrapers import SenateScraper


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="congressional-trades",
        description="Scrape and analyze stock trades by members of US Congress",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List trades")
    list_parser.add_argument("--ticker", "-t", help="Filter by ticker symbol")
    list_parser.add_argument("--politician", "-p", help="Filter by politician name")
    list_parser.add_argument("--chamber", "-c", choices=["senate", "house"], help="Filter by chamber")
    list_parser.add_argument("--since", "-s", help="Start date (YYYY-MM-DD)")
    list_parser.add_argument("--until", "-u", help="End date (YYYY-MM-DD)")
    list_parser.add_argument("--type", dest="tx_type", choices=["purchase", "sale"], help="Transaction type")
    list_parser.add_argument("--limit", "-n", type=int, default=50, help="Max results")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export trades to file")
    export_parser.add_argument("file", help="Output file path")
    export_parser.add_argument("--format", "-f", choices=["csv", "json"], default="csv")
    export_parser.add_argument("--chamber", "-c", choices=["senate", "house"])
    export_parser.add_argument("--since", "-s", help="Start date")

    # Refresh command
    refresh_parser = subparsers.add_parser("refresh", help="Refresh data from source")
    refresh_parser.add_argument("--days", "-d", type=int, default=30, help="Days to fetch")
    refresh_parser.add_argument("--force", "-f", action="store_true", help="Force refresh even if cache is fresh")

    # Stats command
    subparsers.add_parser("stats", help="Show cache statistics")

    # Politicians command
    pol_parser = subparsers.add_parser("politicians", help="List politicians")
    pol_parser.add_argument("--chamber", "-c", choices=["senate", "house"])

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "refresh":
        cmd_refresh(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "politicians":
        cmd_politicians(args)
    else:
        parser.print_help()
        sys.exit(1)


def cmd_list(args):
    """List trades command."""
    cache = TradeCache()

    # Check if we need to refresh
    if cache.is_stale():
        print("Cache is stale. Run 'congressional-trades refresh' to update.", file=sys.stderr)

    trades = cache.get_trades(
        chamber=args.chamber,
        politician=args.politician,
        ticker=args.ticker,
        start_date=args.since,
        end_date=args.until,
        transaction_type=args.tx_type,
        limit=args.limit,
    )

    if args.json:
        print(json.dumps([t.model_dump(mode="json") for t in trades], indent=2, default=str))
    else:
        if not trades:
            print("No trades found matching criteria.")
            return

        # Print header
        print(f"{'Date':<12} {'Politician':<20} {'Type':<10} {'Ticker':<8} {'Amount':<20}")
        print("-" * 75)

        for trade in trades:
            ticker = trade.ticker or "N/A"
            amount = f"${trade.amount_min:,} - ${trade.amount_max:,}"
            politician = trade.politician[:18] + ".." if len(trade.politician) > 20 else trade.politician

            print(f"{trade.transaction_date} {politician:<20} {trade.transaction_type.value:<10} {ticker:<8} {amount}")


def cmd_export(args):
    """Export trades command."""
    cache = TradeCache()

    trades = cache.get_trades(
        chamber=args.chamber,
        start_date=args.since,
        limit=10000,
    )

    if not trades:
        print("No trades to export.")
        return

    if args.format == "csv":
        with open(args.file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "id", "politician", "chamber", "state", "party",
                "ticker", "asset_name", "transaction_type",
                "transaction_date", "disclosure_date",
                "amount_min", "amount_max", "source_url"
            ])
            writer.writeheader()
            for trade in trades:
                writer.writerow({
                    "id": trade.id,
                    "politician": trade.politician,
                    "chamber": trade.chamber.value,
                    "state": trade.state,
                    "party": trade.party.value if trade.party else "",
                    "ticker": trade.ticker or "",
                    "asset_name": trade.asset_name,
                    "transaction_type": trade.transaction_type.value,
                    "transaction_date": trade.transaction_date.isoformat(),
                    "disclosure_date": trade.disclosure_date.isoformat(),
                    "amount_min": trade.amount_min,
                    "amount_max": trade.amount_max,
                    "source_url": trade.source_url,
                })
    else:
        with open(args.file, "w") as f:
            json.dump(
                [t.model_dump(mode="json") for t in trades],
                f,
                indent=2,
                default=str
            )

    print(f"Exported {len(trades)} trades to {args.file}")


def cmd_refresh(args):
    """Refresh data from source."""
    cache = TradeCache()

    if not args.force and not cache.is_stale():
        stats = cache.stats()
        print(f"Cache is fresh (last updated: {stats['last_scrape']})")
        print(f"Use --force to refresh anyway.")
        return

    print(f"Fetching Senate trades from the last {args.days} days...")

    try:
        with SenateScraper() as scraper:
            trades = list(scraper.scrape_recent(days=args.days))

        if trades:
            count = cache.add_trades(trades)
            print(f"Added {count} trades to cache.")
        else:
            print("No trades found. The scraper may need updating.")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Show cache statistics."""
    cache = TradeCache()
    stats = cache.stats()

    print("Congressional Trades Cache Statistics")
    print("=" * 40)
    print(f"Total trades:     {stats['trade_count']:,}")
    print(f"Politicians:      {stats['politician_count']}")
    print(f"Date range:       {stats['date_range']['min']} to {stats['date_range']['max']}")
    print(f"Last updated:     {stats['last_scrape'] or 'Never'}")
    print(f"Cache status:     {'Stale' if stats['is_stale'] else 'Fresh'}")
    print(f"Database:         {stats['db_path']}")


def cmd_politicians(args):
    """List politicians command."""
    cache = TradeCache()

    politicians = cache.get_politicians(chamber=args.chamber)

    if not politicians:
        print("No politicians found. Run 'congressional-trades refresh' first.")
        return

    print(f"{'Name':<30} {'Chamber':<10} {'State':<6} {'Party':<6} {'Trades':<8} {'Last Trade'}")
    print("-" * 80)

    for pol in politicians:
        party = pol.party.value if pol.party else "?"
        last_trade = pol.last_trade_date.isoformat() if pol.last_trade_date else "N/A"
        name = pol.name[:28] + ".." if len(pol.name) > 30 else pol.name

        print(f"{name:<30} {pol.chamber.value:<10} {pol.state:<6} {party:<6} {pol.total_trades:<8} {last_trade}")


if __name__ == "__main__":
    main()
