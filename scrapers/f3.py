"""
BoxBox – Formula 3 scraper
Fetches F3 Sprint Race and Feature Race sessions from f3calendar.com JSON API.
"""

from .calendar_api import fetch_sessions

_API = "https://www.f3calendar.com/api/calendar"
_URL = "https://www.fiaformula3.com/Calendar"
_ALLOWED = {"Sprint", "Feature"}
_DURATIONS = {"Sprint": 30, "Feature": 45}


def get_sessions():
    """Return all 2026 F3 race sessions (sprint and feature)."""
    return fetch_sessions(_API, "F3", _ALLOWED, _DURATIONS, _URL)
