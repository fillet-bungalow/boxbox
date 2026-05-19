"""
BoxBox – MotoGP scraper
Fetches MotoGP class sessions: qualifying (Q1/Q2), sprint, and race.
"""

from .motogp_base import get_series_sessions

_ALLOWED = {"Q", "SPR", "RAC"}


def get_sessions():
    """Return all 2026 MotoGP class sessions."""
    return get_series_sessions("MotoGP", _ALLOWED)
