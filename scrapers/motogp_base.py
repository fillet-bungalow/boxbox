"""
BoxBox – MotoGP PulseLive API base
Shared utilities for MotoGP, Moto2, and Moto3 scrapers.
Returns standardised session dicts from api.motogp.pulselive.com.
"""

from datetime import datetime, timedelta

import pytz
import requests

_BASE = "https://api.motogp.pulselive.com/motogp/v1/results"
_SEASON_UUID = "e88b4e43-2209-47aa-8e83-0e0b1cedde6e"  # 2026

CATEGORY_UUIDS = {
    "MotoGP": "e8c110ad-64aa-4e8e-8a86-f2f152f6a942",
    "Moto2":  "549640b8-fd9c-4245-acfd-60e4bc38b25c",
    "Moto3":  "954f7e65-2ef2-4423-b949-4961cc603e45",
}

_HEADERS = {"User-Agent": "BoxBox/1.0"}

# Maps (session_type, number) to display label
_SESSION_LABELS = {
    ("FP",  1):    "Free Practice 1",
    ("FP",  2):    "Free Practice 2",
    ("Q",   1):    "Qualifying 1",
    ("Q",   2):    "Qualifying 2",
    ("SPR", None): "Sprint",
    ("WUP", None): "Warm-Up",
    ("RAC", None): "Race",
}

_SESSION_DURATIONS = {
    "Free Practice 1": 45,
    "Free Practice 2": 45,
    "Qualifying 1":    15,
    "Qualifying 2":    15,
    "Sprint":          25,
    "Warm-Up":         10,
    "Race":            45,
}

# Race duration varies by class
_RACE_DURATIONS = {
    "MotoGP": 50,
    "Moto2":  40,
    "Moto3":  40,
}

# Derived from the suffix after stripping "GRAND PRIX OF (THE) " / "GRAND PRIX DE "
_GP_NAMES = {
    "THAILAND":      "Thai GP",
    "BRAZIL":        "Brazilian GP",
    "AMERICAS":      "Americas GP",
    "UNITED STATES": "US GP",
    "SPAIN":         "Spanish GP",
    "FRANCE":        "French GP",
    "CATALONIA":     "Catalan GP",
    "ITALY":         "Italian GP",
    "HUNGARY":       "Hungarian GP",
    "CZECHIA":       "Czech GP",
    "NETHERLANDS":   "Dutch GP",
    "GERMANY":       "German GP",
    "GREAT BRITAIN": "British GP",
    "ARAGON":        "Aragon GP",
    "SAN MARINO":    "San Marino GP",
    "AUSTRIA":       "Austrian GP",
    "JAPAN":         "Japanese GP",
    "INDONESIA":     "Indonesian GP",
    "AUSTRALIA":     "Australian GP",
    "MALAYSIA":      "Malaysian GP",
    "QATAR":         "Qatar GP",
    "PORTUGAL":      "Portuguese GP",
    "VALENCIA":      "Valencia GP",
}

_events_cache = None


def _get_events():
    global _events_cache
    if _events_cache is not None:
        return _events_cache
    url = f"{_BASE}/events?seasonUuid={_SEASON_UUID}"
    print(f"    MotoGP API: fetching {url}")
    resp = requests.get(url, timeout=15, headers=_HEADERS)
    resp.raise_for_status()
    _events_cache = [e for e in resp.json() if not e.get("test", False)]
    print(f"      {len(_events_cache)} race weekends found")
    return _events_cache


def _short_name(event_name):
    name = event_name.upper()
    for prefix in ("GRAND PRIX OF THE ", "GRAND PRIX OF ", "GRAND PRIX DE ", "GRAND PRIX D'"):
        if name.startswith(prefix):
            suffix = name[len(prefix):]
            return _GP_NAMES.get(suffix, suffix.title() + " GP")
    return event_name.title()


def get_series_sessions(series, allowed_types):
    """Return all 2026 sessions for one series, filtered to allowed_types."""
    category_uuid = CATEGORY_UUIDS[series]
    events = _get_events()
    all_sessions = []

    for event in events:
        gp_name = _short_name(event["name"])
        url = f"{_BASE}/sessions?eventUuid={event['id']}&categoryUuid={category_uuid}"

        try:
            resp = requests.get(url, timeout=15, headers=_HEADERS)
            resp.raise_for_status()
            raw = resp.json()
        except Exception as exc:
            print(f"      ERROR {gp_name}: {exc}")
            continue

        if not raw:
            continue

        # Build location from circuit data embedded in the first session
        location = gp_name
        for s in raw:
            circuit = s.get("event", {}).get("circuit", {})
            if circuit.get("name"):
                country = s.get("event", {}).get("country", {}).get("name", "")
                location = f"{circuit['name']}, {circuit['place']}, {country}"
                break

        mgp_url = "https://www.motogp.com/en/racing/2026"
        count = 0

        for s in raw:
            stype = s.get("type")
            if stype not in allowed_types:
                continue

            label = _SESSION_LABELS.get((stype, s.get("number")))
            if not label:
                continue

            date_str = s.get("date")
            if not date_str:
                continue

            start = datetime.fromisoformat(date_str).astimezone(pytz.utc)
            duration = _RACE_DURATIONS[series] if stype == "RAC" else _SESSION_DURATIONS.get(label, 30)
            end = start + timedelta(minutes=duration)

            all_sessions.append({
                "series":      series,
                "title":       f"{gp_name} {label}",
                "location":    location,
                "start":       start,
                "end":         end,
                "url":         mgp_url,
                "description": (
                    f"{series} 2026\n"
                    f"{gp_name} | {label}\n\n"
                    f"Live on TNT Sports\n\n"
                    f"{mgp_url}"
                ),
            })
            count += 1

        print(f"      {gp_name}: {count} sessions")

    return all_sessions
