"""
BoxBox – BSB (British Superbike Championship) scraper
Scrapes race session times from britishsuperbike.com round pages.
All times on the site are BST (Europe/London).
"""

from datetime import date, datetime, timedelta

import pytz
import requests
from bs4 import BeautifulSoup

_BST = pytz.timezone("Europe/London")
_BASE = "https://www.britishsuperbike.com/calendar/2026"
_HEADERS = {"User-Agent": "BoxBox/1.0"}

# (slug, start_date, venue_name, location)
_ROUNDS = [
    ("r1-oulton-park",     date(2026,  5,  2), "Oulton Park",     "Oulton Park Circuit, Little Budworth, Tarporley CW6 9BW"),
    ("r2-donington-park",  date(2026,  5, 15), "Donington Park",  "Donington Park Circuit, Castle Donington, Derby DE74 2RP"),
    ("r3-knockhill",       date(2026,  6, 19), "Knockhill",       "Knockhill Racing Circuit, Dunfermline KY12 9TF"),
    ("r4-snetterton",      date(2026,  7,  3), "Snetterton",      "Snetterton Circuit, Norwich NR16 2JU"),
    ("r5-brands-hatch",    date(2026,  7, 17), "Brands Hatch",    "Brands Hatch, Fawkham, Longfield DA3 8NG"),
    ("r6-oulton-park",     date(2026,  7, 31), "Oulton Park",     "Oulton Park Circuit, Little Budworth, Tarporley CW6 9BW"),
    ("r7-thruxton",        date(2026,  8, 14), "Thruxton",        "Thruxton Circuit, Thruxton, Andover SP11 8PN"),
    ("r8-cadwell-park",    date(2026,  8, 29), "Cadwell Park",    "Cadwell Park, Louth LN11 9SE"),
    ("r9-assen",           date(2026,  9, 18), "Assen",           "TT Circuit Assen, Netherlands"),
    ("r10-donington-park", date(2026, 10,  2), "Donington Park",  "Donington Park Circuit, Castle Donington, Derby DE74 2RP"),
    ("r11-brands-hatch",   date(2026, 10, 16), "Brands Hatch",    "Brands Hatch, Fawkham, Longfield DA3 8NG"),
]

_DAY_NAMES = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}


def _day_to_date(day_abbr, start_date):
    for offset in range(4):
        d = start_date + timedelta(days=offset)
        if _DAY_NAMES[d.weekday()] == day_abbr:
            return d
    return None


def _scrape_round(slug, start_date, venue, location):
    url = f"{_BASE}/{slug}"
    try:
        resp = requests.get(url, timeout=15, headers=_HEADERS)
        resp.raise_for_status()
    except Exception as exc:
        print(f"      ERROR {venue}: {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    sessions = []

    for race_num in (1, 2, 3):
        tag = soup.find(string=f"Race {race_num}")
        if not tag:
            continue
        # Container 3 levels up holds "{Day} Race N {time} BST"
        container = tag.parent
        for _ in range(3):
            if container: container = container.parent
        if not container:
            continue

        text = container.get_text(" ", strip=True)
        import re
        m = re.search(r"(Fri|Sat|Sun|Mon)\s+Race\s+" + str(race_num) + r"\s+(\d{1,2}:\d{2})\s+BST", text)
        if not m:
            continue

        race_date = _day_to_date(m.group(1), start_date)
        if not race_date:
            continue

        h, mi = map(int, m.group(2).split(":"))
        start = _BST.localize(datetime(race_date.year, race_date.month, race_date.day, h, mi))
        end = start + timedelta(minutes=35)

        sessions.append({
            "series":      "BSB",
            "title":       f"{venue} Race {race_num}",
            "location":    location,
            "start":       start,
            "end":         end,
            "url":         url,
            "description": (
                f"BSB 2026\n{venue} | Race {race_num}\n\n"
                f"Live on TNT Sports\n\n{url}"
            ),
        })

    return sessions


def get_sessions():
    """Return all 2026 BSB race sessions (Race 1, 2, 3 per round)."""
    all_sessions = []
    for slug, start_date, venue, location in _ROUNDS:
        sessions = _scrape_round(slug, start_date, venue, location)
        print(f"      {venue}: {len(sessions)} sessions")
        all_sessions.extend(sessions)
    return all_sessions
