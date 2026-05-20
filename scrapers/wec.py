"""
BoxBox – WEC (FIA World Endurance Championship) scraper
Scrapes qualifying and race sessions from fiawec.com event pages.
Uses data-timestamp attributes (Unix UTC) for exact session times.
"""

import re
from datetime import datetime, timedelta, timezone

import pytz
import requests
from bs4 import BeautifulSoup

_UTC = pytz.utc
_BASE = "https://www.fiawec.com/en/race"
_HEADERS = {"User-Agent": "BoxBox/1.0"}

# (slug, display_name, location, race_duration_minutes)
_EVENTS = [
    ("6-hours-of-imola-2026",
     "6 Hours of Imola",      "Autodromo Internazionale Enzo e Dino Ferrari, Imola, Italy",   360),
    ("totalenergies-6-hours-of-spa-francorchamps-2026",
     "6 Hours of Spa",        "Circuit de Spa-Francorchamps, Stavelot, Belgium",               360),
    ("24-hours-of-le-mans-2026",
     "24 Hours of Le Mans",   "Circuit de la Sarthe, Le Mans, France",                        1440),
    ("rolex-6-hours-of-sao-paulo-2026",
     "6 Hours of São Paulo",  "Autódromo José Carlos Pace, São Paulo, Brazil",                 360),
    ("lone-star-le-mans-2026",
     "Lone Star Le Mans",     "Circuit of The Americas, Austin, Texas, USA",                  360),
    ("6-hours-of-fuji-2026",
     "6 Hours of Fuji",       "Fuji Speedway, Oyama, Shizuoka, Japan",                        360),
    ("qatar-1812km-2026",
     "Qatar 1812km",          "Lusail International Circuit, Lusail, Qatar",                  360),
    ("bapco-energies-8-hours-of-bahrain-2026",
     "8 Hours of Bahrain",    "Bahrain International Circuit, Sakhir, Bahrain",               480),
]

# Sessions whose names match these patterns are included
_INCLUDE_RE = re.compile(r"qualifying|hyperpole|race|warm.?up", re.I)

_SESSION_DURATIONS = {
    re.compile(r"free practice", re.I): 90,
    re.compile(r"qualifying",    re.I): 25,
    re.compile(r"hyperpole",     re.I): 30,
    re.compile(r"warm.?up",      re.I): 15,
}


def _session_duration(name, race_duration):
    if re.search(r"\brace\b", name, re.I):
        return race_duration
    for pattern, mins in _SESSION_DURATIONS.items():
        if pattern.search(name):
            return mins
    return 30


def _clean_name(raw):
    """Strip times, Replay/Results suffixes from row text to get session name."""
    name = re.sub(r"\d{1,2}:\d{2}\s*(AM|PM)?", "", raw, flags=re.I)
    name = re.sub(r"\b(Replay|Results|Highlights)\b.*", "", name, flags=re.I)
    return name.strip()


def _scrape_event(slug, display_name, location, race_duration):
    url = f"{_BASE}/{slug}"
    try:
        resp = requests.get(url, timeout=15, headers=_HEADERS)
        resp.raise_for_status()
    except Exception as exc:
        print(f"      ERROR {display_name}: {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    sessions = []
    seen = set()

    for el in soup.find_all(attrs={"data-timestamp": True}):
        ts = int(el["data-timestamp"])
        start = datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=_UTC)

        # Walk up to find row container with session name
        node = el.parent
        row_text = ""
        for _ in range(6):
            if node is None:
                break
            txt = node.get_text(" ", strip=True)
            if 20 < len(txt) < 200:
                row_text = txt
                break
            node = node.parent

        session_name = _clean_name(row_text)
        if not session_name or not _INCLUDE_RE.search(session_name):
            continue

        key = (session_name, ts)
        if key in seen:
            continue
        seen.add(key)

        duration = _session_duration(session_name, race_duration)
        end = start + timedelta(minutes=duration)

        sessions.append({
            "series":      "WEC",
            "title":       f"{display_name} {session_name}",
            "location":    location,
            "start":       start,
            "end":         end,
            "url":         url,
            "description": (
                f"FIA World Endurance Championship 2026\n"
                f"{display_name} | {session_name}\n\n"
                f"Live on Eurosport\n\n{url}"
            ),
        })

    return sessions


def get_sessions():
    """Return all 2026 WEC qualifying and race sessions."""
    all_sessions = []
    for slug, name, location, race_duration in _EVENTS:
        sessions = _scrape_event(slug, name, location, race_duration)
        print(f"      {name}: {len(sessions)} sessions")
        all_sessions.extend(sessions)
    return all_sessions
