"""
BoxBox – motorsportcalendars.com JSON API base
Shared utility for IndyCar, Formula E, F2, and F3 scrapers.
All four series use identical API structure at *calendar.com/api/calendar.
"""

from datetime import datetime, timedelta

import pytz
import requests

_HEADERS = {"User-Agent": "BoxBox/1.0"}

_SESSION_LABELS = {
    "Race":    "Race",
    "Sprint":  "Sprint Race",
    "Feature": "Feature Race",
}


def fetch_sessions(api_url, series, allowed_sessions, session_durations, series_url):
    """Return standardised session dicts from a motorsportcalendars.com-style JSON API."""
    print(f"    {series}: fetching {api_url}")

    try:
        resp = requests.get(api_url, timeout=15, headers=_HEADERS)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"      ERROR: {exc}")
        return []

    races = data.get("races", [])
    print(f"      {len(races)} rounds found")

    all_sessions = []
    for race in races:
        name = race["name"]
        location = race.get("location") or name
        sessions = race.get("sessions", {})

        count = 0
        for session_key, dt_str in sessions.items():
            if session_key not in allowed_sessions or not dt_str:
                continue

            label = _SESSION_LABELS.get(session_key, session_key)
            start = datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone(pytz.utc)
            end = start + timedelta(minutes=session_durations.get(session_key, 60))

            all_sessions.append({
                "series":      series,
                "title":       f"{name} {label}",
                "location":    location,
                "start":       start,
                "end":         end,
                "url":         series_url,
                "description": (
                    f"{series} 2026\n"
                    f"{name} | {label}\n\n"
                    f"{series_url}"
                ),
            })
            count += 1

        if count:
            print(f"      {name}: {count} sessions")

    return all_sessions
