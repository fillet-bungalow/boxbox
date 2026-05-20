"""
BoxBox – IndyCar scraper
Fetches IndyCar race sessions from indycarcalendar.com JSON API.
"""

from .calendar_api import fetch_sessions

_API = "https://www.indycarcalendar.com/api/calendar"
_URL = "https://www.indycar.com/Schedule"
_ALLOWED = {"Race"}
_DURATIONS = {"Race": 120}


def get_sessions():
    """Return all 2026 IndyCar race sessions."""
    return fetch_sessions(_API, "IndyCar", _ALLOWED, _DURATIONS, _URL)
