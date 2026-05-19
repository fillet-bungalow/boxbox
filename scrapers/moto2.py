"""
BoxBox – Moto2 scraper
Fetches Moto2 class race sessions only.
"""

from .motogp_base import get_series_sessions


def get_sessions():
    """Return all 2026 Moto2 class race sessions."""
    return get_series_sessions("Moto2", {"RAC"})
