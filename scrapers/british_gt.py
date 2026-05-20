"""
BoxBox – British GT Championship scraper
Scrapes race session times from britishgt.com event pages.
Pages show both local and GMT times; we use GMT directly.
"""

from datetime import datetime, timedelta

import pytz
import re
import requests
from bs4 import BeautifulSoup

_UTC = pytz.utc
_BASE = "https://www.britishgt.com"
_HEADERS = {"User-Agent": "BoxBox/1.0"}
_MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5,
    "June": 6, "July": 7, "August": 8, "September": 9, "October": 10,
    "November": 11, "December": 12,
}

_DAY_PATTERN = re.compile(
    r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+\d+\s+\w+", re.I
)

# (event_id, name, location)
_EVENTS = [
    (109, "Silverstone",         "Silverstone Circuit, Silverstone, Northamptonshire NN12 8TN"),
    (110, "Oulton Park",         "Oulton Park Circuit, Little Budworth, Tarporley CW6 9BW"),
    (111, "Spa-Francorchamps",   "Circuit de Spa-Francorchamps, Stavelot, Belgium"),
    (112, "Snetterton",          "Snetterton Circuit, Snetterton, Norwich NR16 2JU"),
    (113, "Brands Hatch",        "Brands Hatch, Fawkham, Longfield DA3 8NG"),
    (114, "Donington Park",      "Donington Park Circuit, Castle Donington, Derby DE74 2RP"),
]


def _parse_date(day_str, year):
    """Parse 'Monday, 25 May' or 'Saturday, 23 May' into a date."""
    m = re.search(r"(\d+)\s+(\w+)", day_str)
    if not m:
        return None
    day, month_name = int(m.group(1)), m.group(2)
    month = _MONTHS.get(month_name)
    if not month:
        return None
    return datetime(year, month, day)


def _scrape_event(event_id, name, location):
    url = f"{_BASE}/event/{event_id}"
    try:
        resp = requests.get(url, timeout=15, headers=_HEADERS)
        resp.raise_for_status()
    except Exception as exc:
        print(f"      ERROR {name}: {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    year_match = re.search(r"\b(202\d)\b", soup.get_text())
    year = int(year_match.group(1)) if year_match else 2026

    # Slice the full page text into per-day sections by finding day headers
    page_text = soup.get_text(" ", strip=True)
    day_matches = list(_DAY_PATTERN.finditer(page_text))

    sessions = []

    for i, dm in enumerate(day_matches):
        race_date = _parse_date(dm.group(0), year)
        if not race_date:
            continue

        # Only include text up to the next day header
        start_pos = dm.start()
        end_pos = day_matches[i + 1].start() if i + 1 < len(day_matches) else len(page_text)
        section = page_text[start_pos:end_pos]

        # Match "Race N  {local}  {gmt}" (numbered) or "Race  {local}  {gmt}" (single race)
        for m in re.finditer(
                r"Race\s+(?:(\d)\s+)?(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})",
                section):
            race_num_str = m.group(1)
            local_time_str = m.group(2)
            gmt_time_str = m.group(3)

            # Skip placeholder 00:00 times (schedule not yet confirmed)
            if local_time_str in ("0:00", "00:00"):
                continue

            race_label = f"Race {race_num_str}" if race_num_str else "Race"
            h, mi = map(int, gmt_time_str.split(":"))
            start = _UTC.localize(race_date.replace(hour=h, minute=mi))
            end = start + timedelta(hours=2)

            sessions.append({
                "series":      "British GT",
                "title":       f"{name} {race_label}",
                "location":    location,
                "start":       start,
                "end":         end,
                "url":         url,
                "description": (
                    f"British GT Championship 2026\n{name} | {race_label}\n\n"
                    f"Live on ITV4\n\n{url}"
                ),
            })

    # Deduplicate by (title, start) in case a pattern appears twice in a section
    seen = set()
    unique = []
    for s in sessions:
        key = (s["title"], s["start"])
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


def get_sessions():
    """Return all 2026 British GT race sessions."""
    all_sessions = []
    for event_id, name, location in _EVENTS:
        sessions = _scrape_event(event_id, name, location)
        print(f"      {name}: {len(sessions)} sessions")
        all_sessions.extend(sessions)
    return all_sessions
