"""
BoxBox – Formula E scraper
Fetches Formula E race sessions from fecalendar.com JSON API.
"""

from .calendar_api import fetch_sessions

_API = "https://formulaecal.com/api/calendar"
_URL = "https://www.fiaformulae.com/en/calendar"
_ALLOWED = {"Race"}
_DURATIONS = {"Race": 50}


def get_sessions():
    """Return all 2026 Formula E race sessions."""
    return fetch_sessions(_API, "Formula E", _ALLOWED, _DURATIONS, _URL)
