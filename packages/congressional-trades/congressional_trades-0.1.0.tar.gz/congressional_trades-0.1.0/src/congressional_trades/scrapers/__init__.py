"""
Scrapers for congressional financial disclosures.
"""

from .senate import SenateScraper
from .fallback import FallbackDataSource

__all__ = ["SenateScraper", "FallbackDataSource"]
