"""Tests for ticker resolution."""

import pytest

from congressional_trades.ticker_resolver import (
    resolve_ticker,
    is_stock,
    batch_resolve,
)


class TestResolveTicker:
    def test_ticker_in_parens(self):
        assert resolve_ticker("Apple Inc. (AAPL)") == "AAPL"
        assert resolve_ticker("NVIDIA Corporation (NVDA)") == "NVDA"

    def test_known_companies(self):
        assert resolve_ticker("Apple Inc.") == "AAPL"
        assert resolve_ticker("Microsoft Corporation") == "MSFT"
        assert resolve_ticker("NVIDIA Corporation") == "NVDA"
        assert resolve_ticker("Amazon.com Inc.") == "AMZN"

    def test_partial_match(self):
        assert resolve_ticker("Apple common stock") == "AAPL"
        assert resolve_ticker("Tesla Motors") == "TSLA"

    def test_unknown_returns_none(self):
        assert resolve_ticker("Some Unknown Company Inc.") is None

    def test_non_stock_returns_none(self):
        assert resolve_ticker("Municipal Bond Fund") is None
        assert resolve_ticker("Treasury Bills") is None
        assert resolve_ticker("Real Estate Partnership") is None


class TestIsStock:
    def test_obvious_stocks(self):
        assert is_stock("Apple Inc. (AAPL)") is True
        assert is_stock("Microsoft Corporation Stock") is True

    def test_obvious_non_stocks(self):
        assert is_stock("Municipal Bond") is False
        assert is_stock("Treasury Bill") is False
        assert is_stock("Money Market Fund") is False
        assert is_stock("Private Partnership LLC") is False


class TestBatchResolve:
    def test_batch(self):
        names = ["Apple Inc.", "Unknown Corp", "Microsoft"]
        results = batch_resolve(names)

        assert results["Apple Inc."] == "AAPL"
        assert results["Unknown Corp"] is None
        assert results["Microsoft"] == "MSFT"
