# congressional-trades

Scrape and analyze stock trades by members of the US Congress.

[![PyPI version](https://badge.fury.io/py/congressional-trades.svg)](https://badge.fury.io/py/congressional-trades)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Scrapes directly from official sources (efdsearch.senate.gov)
- Clean, typed Python API
- Local caching for fast repeated queries
- Export to CSV/DataFrame
- Daily updates via GitHub Actions

## Installation

```bash
pip install congressional-trades
```

## Quick Start

```python
from congressional_trades import get_trades, get_politicians

# Get all recent trades
trades = get_trades()

# Filter by various criteria
trades = get_trades(
    chamber="senate",
    ticker="NVDA",
    start_date="2024-01-01",
    transaction_type="purchase",
)

# Get as pandas DataFrame
df = get_trades(as_dataframe=True)

# List all politicians
politicians = get_politicians(chamber="senate")
```

## CLI Usage

```bash
# List recent trades
congressional-trades list --ticker NVDA --since 2024-01-01

# Export to CSV
congressional-trades export trades.csv

# Force refresh from source
congressional-trades refresh
```

## Data Sources

- **Senate**: [efdsearch.senate.gov](https://efdsearch.senate.gov) - Electronic Financial Disclosure
- **House**: Coming in v2 (PDF parsing required)

## Data Model

Each trade includes:

| Field | Type | Description |
|-------|------|-------------|
| `politician` | str | Full name |
| `chamber` | str | "senate" or "house" |
| `party` | str | "D", "R", or "I" |
| `state` | str | Two-letter state code |
| `ticker` | str | Stock ticker (if resolved) |
| `asset_name` | str | Full asset description |
| `transaction_type` | str | "purchase", "sale", etc. |
| `transaction_date` | date | When trade occurred |
| `disclosure_date` | date | When disclosed |
| `amount_min` | int | Minimum transaction amount |
| `amount_max` | int | Maximum transaction amount |

## Contributing

Contributions welcome! The biggest need is help with House PDF parsing.

```bash
# Development setup
git clone https://github.com/guttu44/congressional-trades
cd congressional-trades
pip install -e ".[dev]"
pytest
```

## License

MIT
