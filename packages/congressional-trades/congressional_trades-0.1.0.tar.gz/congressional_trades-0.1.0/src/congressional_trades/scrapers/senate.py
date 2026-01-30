"""
Senate Financial Disclosure Scraper

Scrapes data from efdsearch.senate.gov - the official Senate
Electronic Financial Disclosure system.

The Senate site uses a combination of:
1. Search form POST to get list of filings
2. Individual report pages with transaction tables
"""

import re
import time
from datetime import date, datetime
from typing import Iterator, Optional
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from ..models import Trade, Chamber, TransactionType, Party, parse_amount_range


class SenateScraper:
    """
    Scraper for Senate financial disclosures.

    Usage:
        scraper = SenateScraper()
        trades = list(scraper.scrape_recent(days=30))
    """

    BASE_URL = "https://efdsearch.senate.gov"
    SEARCH_URL = f"{BASE_URL}/search/"
    REPORT_URL = f"{BASE_URL}/search/view/paper/"

    # Map senator names to state/party (we'll build this dynamically)
    SENATOR_INFO: dict[str, dict] = {}

    def __init__(self, delay: float = 1.0):
        """
        Initialize scraper.

        Args:
            delay: Seconds to wait between requests (be nice to the server)
        """
        self.delay = delay
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                "User-Agent": "CongressionalTrades/0.1 (https://github.com/guttu44/congressional-trades)",
            },
            follow_redirects=True,
        )
        self._last_request = 0.0

    def _wait(self):
        """Rate limit requests."""
        elapsed = time.time() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request = time.time()

    def _get(self, url: str) -> httpx.Response:
        """Make rate-limited GET request."""
        self._wait()
        return self.client.get(url)

    def _post(self, url: str, data: dict) -> httpx.Response:
        """Make rate-limited POST request."""
        self._wait()
        return self.client.post(url, data=data)

    def scrape_recent(self, days: int = 30) -> Iterator[Trade]:
        """
        Scrape trades from recent filings.

        Args:
            days: How many days back to search

        Yields:
            Trade objects
        """
        end_date = date.today()
        start_date = date.today().replace(day=1)  # First of current month

        # Go back further if needed
        if days > 30:
            from datetime import timedelta
            start_date = end_date - timedelta(days=days)

        yield from self.scrape_date_range(start_date, end_date)

    def scrape_date_range(
        self,
        start_date: date,
        end_date: date,
        report_types: Optional[list[str]] = None,
    ) -> Iterator[Trade]:
        """
        Scrape trades within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            report_types: Filter by report type (default: periodic transaction reports)

        Yields:
            Trade objects
        """
        if report_types is None:
            report_types = ["11"]  # Periodic Transaction Report

        # First, get the search page to extract any needed tokens
        search_page = self._get(self.SEARCH_URL)
        if search_page.status_code != 200:
            raise Exception(f"Failed to load search page: {search_page.status_code}")

        # Search for filings
        search_data = {
            "start_date": start_date.strftime("%m/%d/%Y"),
            "end_date": end_date.strftime("%m/%d/%Y"),
            "filer_type": "1",  # Senator
            "submitted_start_date": "",
            "submitted_end_date": "",
            "candidate_state": "",
            "senator_state": "",
            "report_type": report_types,
            "first_name": "",
            "last_name": "",
        }

        # Note: The actual Senate EFD site has changed over time.
        # This implementation targets the current (2024+) version.
        # We may need to handle CSRF tokens or session cookies.

        response = self._post(
            f"{self.SEARCH_URL}home/",
            data=search_data,
        )

        if response.status_code != 200:
            raise Exception(f"Search failed: {response.status_code}")

        # Parse search results
        report_urls = self._parse_search_results(response.text)

        # Fetch each report
        for report_url, filer_name, filed_date in report_urls:
            try:
                trades = self._scrape_report(report_url, filer_name, filed_date)
                yield from trades
            except Exception as e:
                print(f"Error scraping {report_url}: {e}")
                continue

    def _parse_search_results(self, html: str) -> list[tuple[str, str, date]]:
        """
        Parse search results page to extract report URLs.

        Returns:
            List of (report_url, filer_name, filed_date) tuples
        """
        parser = HTMLParser(html)
        results = []

        # Find the results table
        # Note: Actual structure depends on current Senate EFD site layout
        table = parser.css_first("table.table")
        if not table:
            # Try alternate selectors
            table = parser.css_first("#filedReports")

        if not table:
            return results

        rows = table.css("tbody tr")
        for row in rows:
            cells = row.css("td")
            if len(cells) < 4:
                continue

            # Extract link to report
            link = cells[0].css_first("a")
            if not link:
                continue

            href = link.attributes.get("href", "")
            if not href:
                continue

            report_url = urljoin(self.BASE_URL, href)

            # Extract filer name
            filer_name = cells[1].text(strip=True) if len(cells) > 1 else "Unknown"

            # Extract filed date
            date_text = cells[3].text(strip=True) if len(cells) > 3 else ""
            try:
                filed_date = datetime.strptime(date_text, "%m/%d/%Y").date()
            except ValueError:
                filed_date = date.today()

            results.append((report_url, filer_name, filed_date))

        return results

    def _scrape_report(
        self,
        report_url: str,
        filer_name: str,
        filed_date: date,
    ) -> Iterator[Trade]:
        """
        Scrape individual transaction report.

        Args:
            report_url: URL to the report
            filer_name: Name of the senator
            filed_date: Date the report was filed

        Yields:
            Trade objects from this report
        """
        response = self._get(report_url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch report: {response.status_code}")

        parser = HTMLParser(response.text)

        # Find transactions section
        # Senate reports have different sections for different asset types
        transactions_section = parser.css_first("#transactions, .transactions-table, section.transactions")

        if not transactions_section:
            # Try to find any table with transaction data
            transactions_section = parser.css_first("table")

        if not transactions_section:
            return

        # Parse state and party from filer info if available
        state, party = self._extract_senator_info(parser, filer_name)

        # Parse transaction rows
        rows = transactions_section.css("tr")
        for row in rows:
            cells = row.css("td")
            if len(cells) < 5:
                continue

            try:
                trade = self._parse_transaction_row(
                    cells,
                    filer_name,
                    filed_date,
                    state,
                    party,
                    report_url,
                )
                if trade:
                    yield trade
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue

    def _extract_senator_info(
        self,
        parser: HTMLParser,
        filer_name: str,
    ) -> tuple[str, Optional[Party]]:
        """Extract state and party from report page."""
        # Try to find in page
        state = "XX"  # Default unknown
        party = None

        # Look for state in filer info
        filer_info = parser.css_first(".filer-info, .senator-info")
        if filer_info:
            text = filer_info.text()
            # Try to extract state code
            state_match = re.search(r'\b([A-Z]{2})\b', text)
            if state_match:
                state = state_match.group(1)

            # Try to extract party
            if "(D)" in text or "Democrat" in text:
                party = Party.DEMOCRAT
            elif "(R)" in text or "Republican" in text:
                party = Party.REPUBLICAN
            elif "(I)" in text or "Independent" in text:
                party = Party.INDEPENDENT

        return state, party

    def _parse_transaction_row(
        self,
        cells: list,
        filer_name: str,
        filed_date: date,
        state: str,
        party: Optional[Party],
        report_url: str,
    ) -> Optional[Trade]:
        """Parse a single transaction row into a Trade object."""

        # Column order varies, but typically:
        # Transaction Date | Owner | Asset | Type | Amount | Comment

        # Get text from cells
        cell_texts = [c.text(strip=True) for c in cells]

        if len(cell_texts) < 5:
            return None

        # Parse transaction date
        try:
            tx_date_str = cell_texts[0]
            transaction_date = datetime.strptime(tx_date_str, "%m/%d/%Y").date()
        except ValueError:
            return None

        # Owner (SP = Spouse, JT = Joint, DC = Dependent Child, etc.)
        owner = cell_texts[1] if len(cell_texts) > 1 else None

        # Asset name
        asset_name = cell_texts[2] if len(cell_texts) > 2 else "Unknown"

        # Transaction type
        tx_type_str = cell_texts[3] if len(cell_texts) > 3 else "Purchase"
        transaction_type = TransactionType.from_raw(tx_type_str)

        # Amount range
        amount_str = cell_texts[4] if len(cell_texts) > 4 else "$1,001 - $15,000"
        amount_min, amount_max = parse_amount_range(amount_str)

        # Comment (optional)
        comment = cell_texts[5] if len(cell_texts) > 5 else None

        # Try to extract ticker from asset name
        ticker = self._extract_ticker(asset_name)

        return Trade(
            politician=filer_name,
            chamber=Chamber.SENATE,
            state=state,
            party=party,
            ticker=ticker,
            asset_name=asset_name,
            asset_type="Stock",  # Could be refined
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            disclosure_date=filed_date,
            amount_min=amount_min,
            amount_max=amount_max,
            comment=comment,
            owner=owner,
            source_url=report_url,
            scraped_at=date.today(),
        )

    def _extract_ticker(self, asset_name: str) -> Optional[str]:
        """
        Try to extract ticker symbol from asset name.

        Examples:
            "Apple Inc. (AAPL)" -> "AAPL"
            "NVIDIA Corporation" -> None (needs external resolution)
        """
        # Look for ticker in parentheses
        match = re.search(r'\(([A-Z]{1,5})\)', asset_name)
        if match:
            return match.group(1)

        # Look for common patterns like "Stock: AAPL"
        match = re.search(r'Stock:\s*([A-Z]{1,5})\b', asset_name)
        if match:
            return match.group(1)

        return None

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
