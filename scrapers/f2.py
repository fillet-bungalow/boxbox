"""
BoxBox – Formula 2 scraper
Fetches F2 Sprint Race and Feature Race sessions from f2calendar.com JSON API.
"""

from .calendar_api import fetch_sessions

_API = "https://www.f2calendar.com/api/calendar"
_URL = "https://www.fiaformula2.com/Calendar"
_ALLOWED = {"Sprint", "Feature"}
_DURATIONS = {"Sprint": 35, "Feature": 50}


def get_sessions():
    """Return all 2026 F2 race sessions (sprint and feature)."""
    return fetch_sessions(_API, "F2", _ALLOWED, _DURATIONS, _URL)
