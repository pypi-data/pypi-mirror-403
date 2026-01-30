"""Tests for data models."""

from datetime import date

import pytest

from congressional_trades.models import (
    Trade,
    Politician,
    Chamber,
    TransactionType,
    Party,
    parse_amount_range,
)


class TestTransactionType:
    def test_from_raw_purchase(self):
        assert TransactionType.from_raw("Purchase") == TransactionType.PURCHASE
        assert TransactionType.from_raw("PURCHASE") == TransactionType.PURCHASE
        assert TransactionType.from_raw("Buy") == TransactionType.PURCHASE

    def test_from_raw_sale(self):
        assert TransactionType.from_raw("Sale") == TransactionType.SALE
        assert TransactionType.from_raw("Sale (Full)") == TransactionType.SALE_FULL
        assert TransactionType.from_raw("Sale (Partial)") == TransactionType.SALE_PARTIAL

    def test_from_raw_exchange(self):
        assert TransactionType.from_raw("Exchange") == TransactionType.EXCHANGE


class TestAmountRange:
    def test_standard_ranges(self):
        assert parse_amount_range("$1,001 - $15,000") == (1001, 15000)
        assert parse_amount_range("$15,001 - $50,000") == (15001, 50000)
        assert parse_amount_range("$100,001 - $250,000") == (100001, 250000)

    def test_over_50m(self):
        result = parse_amount_range("Over $50,000,000")
        assert result[0] == 50000001

    def test_partial_match(self):
        # Should handle slight variations
        result = parse_amount_range("$1,001-$15,000")
        assert result == (1001, 15000)


class TestTrade:
    def test_create_trade(self):
        trade = Trade(
            politician="John Doe",
            chamber=Chamber.SENATE,
            state="CA",
            party=Party.DEMOCRAT,
            ticker="AAPL",
            asset_name="Apple Inc.",
            transaction_type=TransactionType.PURCHASE,
            transaction_date=date(2024, 1, 15),
            disclosure_date=date(2024, 1, 20),
            amount_min=1001,
            amount_max=15000,
            source_url="https://example.com/report",
        )

        assert trade.politician == "John Doe"
        assert trade.chamber == Chamber.SENATE
        assert trade.ticker == "AAPL"
        assert trade.id is not None  # Auto-generated

    def test_amount_midpoint(self):
        trade = Trade(
            politician="Jane Doe",
            chamber=Chamber.SENATE,
            state="NY",
            asset_name="Test Stock",
            transaction_type=TransactionType.PURCHASE,
            transaction_date=date(2024, 1, 1),
            disclosure_date=date(2024, 1, 5),
            amount_min=1001,
            amount_max=15000,
            source_url="https://example.com",
        )

        assert trade.amount_midpoint == 8000  # (1001 + 15000) // 2

    def test_disclosure_delay(self):
        trade = Trade(
            politician="Test",
            chamber=Chamber.SENATE,
            state="TX",
            asset_name="Test",
            transaction_type=TransactionType.PURCHASE,
            transaction_date=date(2024, 1, 1),
            disclosure_date=date(2024, 1, 15),
            amount_min=1001,
            amount_max=15000,
            source_url="https://example.com",
        )

        assert trade.disclosure_delay_days == 14


class TestPolitician:
    def test_create_politician(self):
        pol = Politician(
            name="Nancy Pelosi",
            chamber=Chamber.HOUSE,
            state="CA",
            party=Party.DEMOCRAT,
            total_trades=100,
        )

        assert pol.name == "Nancy Pelosi"
        assert pol.id is not None
