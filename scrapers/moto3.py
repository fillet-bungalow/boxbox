"""
BoxBox – Moto3 scraper
Fetches Moto3 class race sessions only.
"""

from .motogp_base import get_series_sessions


def get_sessions():
    """Return all 2026 Moto3 class race sessions."""
    return get_series_sessions("Moto3", {"RAC"})
