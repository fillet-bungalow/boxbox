"""
BoxBox – F1 scraper
Fetches session times from the Jolpica API.
Returns a standardised list of session dicts.
"""

from datetime import datetime, timedelta

import requests
import pytz

UTC = pytz.utc
LONDON = pytz.timezone("Europe/London")

API_URL = "https://api.jolpi.ca/ergast/f1/2026.json?limit=40"

SESSION_MAP = {
    "FirstPractice":    "Practice 1",
    "SecondPractice":   "Practice 2",
    "ThirdPractice":    "Practice 3",
    "SprintQualifying": "Sprint Qualifying",
    "Sprint":           "Sprint",
    "Qualifying":       "Qualifying",
}

SESSION_DURATIONS = {
    "Practice 1":        60,
    "Practice 2":        60,
    "Practice 3":        60,
    "Sprint Qualifying": 45,
    "Sprint":            40,
    "Qualifying":        60,
    "Race":             120,
}

GP_SHORT_NAMES = {
    "Australia":    "Australian GP",
    "China":        "Chinese GP",
    "Japan":        "Japanese GP",
    "Bahrain":      "Bahrain GP",
    "Saudi Arabia": "Saudi Arabian GP",
    "Miami":        "Miami GP",
    "Monaco":       "Monaco GP",
    "Canada":       "Canadian GP",
    "Austria":      "Austrian GP",
    "UK":           "British GP",
    "Hungary":      "Hungarian GP",
    "Belgium":      "Belgian GP",
    "Netherlands":  "Dutch GP",
    "Italy":        "Italian GP",
    "Azerbaijan":   "Azerbaijan GP",
    "Singapore":    "Singapore GP",
    "USA":          "US GP",
    "Mexico":       "Mexico City GP",
    "Brazil":       "São Paulo GP",
    "Qatar":        "Qatar GP",
    "Abu Dhabi":    "Abu Dhabi GP",
}


def _short_name(race):
    country = race["Circuit"]["Location"]["country"]
    locality = race["Circuit"]["Location"]["locality"]
    # Two Spanish rounds need locality to differentiate
    if country == "Spain":
        return f"{locality} GP"
    return GP_SHORT_NAMES.get(country, f"{country} GP")


def _parse_dt(date_str, time_str):
    dt = datetime.strptime(f"{date_str}T{time_str}", "%Y-%m-%dT%H:%M:%SZ")
    return UTC.localize(dt)


def _build_sessions(race):
    gp = _short_name(race)
    location = (
        f"{race['Circuit']['circuitName']}, "
        f"{race['Circuit']['Location']['locality']}, "
        f"{race['Circuit']['Location']['country']}"
    )
    f1_url = "https://www.formula1.com/en/racing/2026"
    sessions = []

    for field, label in SESSION_MAP.items():
        if field not in race:
            continue
        s = race[field]
        if not s.get("time"):
            continue
        start = _parse_dt(s["date"], s["time"])
        end = start + timedelta(minutes=SESSION_DURATIONS[label])
        sessions.append({
            "series": "F1",
            "title": f"{gp} {label}",
            "location": location,
            "start": start,
            "end": end,
            "url": f1_url,
            "description": (
                f"Formula 1 2026\n"
                f"{gp} | {label}\n\n"
                f"Live on Sky Sports F1\n\n"
                f"{f1_url}"
            ),
        })

    if race.get("time"):
        start = _parse_dt(race["date"], race["time"])
        end = start + timedelta(minutes=SESSION_DURATIONS["Race"])
        sessions.append({
            "series": "F1",
            "title": f"{gp} Race",
            "location": location,
            "start": start,
            "end": end,
            "url": f1_url,
            "description": (
                f"Formula 1 2026\n"
                f"{gp} | Race\n\n"
                f"Live on Sky Sports F1\n\n"
                f"{f1_url}"
            ),
        })

    return sessions


def get_sessions():
    """Return all F1 2026 sessions as a list of standardised dicts."""
    print(f"    F1: fetching {API_URL}")
    try:
        resp = requests.get(API_URL, timeout=15, headers={"User-Agent": "BoxBox/1.0"})
        resp.raise_for_status()
    except Exception as exc:
        print(f"      ERROR: {exc}")
        return []

    races = resp.json()["MRData"]["RaceTable"]["Races"]
    print(f"      {len(races)} rounds found")

    all_sessions = []
    for race in races:
        sessions = _build_sessions(race)
        gp = _short_name(race)
        print(f"      {race['round']:>2}. {gp}: {len(sessions)} sessions")
        all_sessions.extend(sessions)

    return all_sessions
