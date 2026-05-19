"""
BoxBox – BTCC scraper
Scrapes session times from btcc.net circuit pages.
Returns a standardised list of session dicts.
"""

import re
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
import pytz

LONDON = pytz.timezone("Europe/London")

VENUES = [
    {
        "name": "Snetterton",
        "slug": "snetterton",
        "saturday": date(2026, 5, 23),
        "sunday": date(2026, 5, 24),
        "rounds": "7, 8 & 9",
        "location": "Snetterton Circuit, Snetterton, Norwich NR16 2JU",
    },
    {
        "name": "Oulton Park",
        "slug": "oulton-park",
        "saturday": date(2026, 6, 6),
        "sunday": date(2026, 6, 7),
        "rounds": "10, 11 & 12",
        "location": "Oulton Park Circuit, Little Budworth, Tarporley CW6 9BW",
    },
    {
        "name": "Thruxton",
        "slug": "thruxton",
        "saturday": date(2026, 7, 25),
        "sunday": date(2026, 7, 26),
        "rounds": "13, 14 & 15",
        "location": "Thruxton Circuit, Thruxton, Andover SP11 8PN",
    },
    {
        "name": "Knockhill",
        "slug": "knockhill",
        "saturday": date(2026, 8, 8),
        "sunday": date(2026, 8, 9),
        "rounds": "16, 17 & 18",
        "location": "Knockhill Racing Circuit, Knockhill, Dunfermline KY12 9TF",
    },
    {
        "name": "Donington Park",
        "slug": "donington-park-gp",
        "saturday": date(2026, 8, 22),
        "sunday": date(2026, 8, 23),
        "rounds": "19, 20 & 21",
        "location": "Donington Park Circuit, Castle Donington, Derby DE74 2RP",
    },
    {
        "name": "Croft",
        "slug": "croft",
        "saturday": date(2026, 9, 5),
        "sunday": date(2026, 9, 6),
        "rounds": "22, 23 & 24",
        "location": "Croft Circuit, Dalton-on-Tees, Darlington DL2 2PL",
    },
    {
        "name": "Silverstone",
        "slug": "silverstone",
        "saturday": date(2026, 9, 26),
        "sunday": date(2026, 9, 27),
        "rounds": "25, 26 & 27",
        "location": "Silverstone Circuit, Silverstone, Towcester NN12 8TN",
    },
    {
        "name": "Brands Hatch",
        "slug": "brands-hatch-gp",
        "saturday": date(2026, 10, 10),
        "sunday": date(2026, 10, 11),
        "rounds": "28, 29 & 30",
        "location": "Brands Hatch, Fawkham, Longfield DA3 8NG",
    },
]

BTCC_KEYWORDS = [
    "kwik fit british touring car",
    "british touring car championship",
    "qualifying race",
]

SESSION_DURATIONS = {
    "free practice": 40,
    "qualifying": 35,
    "qualifying race": 25,
    "race": 35,
}


def _is_btcc_row(cells):
    text = " ".join(c.get_text(strip=True).lower() for c in cells)
    return any(kw in text for kw in BTCC_KEYWORDS)


def _is_logistical_row(row):
    text = row.get_text(strip=True).lower()
    skip_phrases = [
        "lunch break", "pit lane opens", "pit lane walkabout",
        "autograph session", "to grid", "tbc",
    ]
    if row.find(["em", "i"]):
        return True
    return any(p in text for p in skip_phrases)


def _parse_time_range(raw, event_date):
    cleaned = raw.strip().replace(".", ":").replace("\u2013", "-").replace("\u2014", "-")
    cleaned = re.sub(r"[^\d:\-\s]", "", cleaned).strip()
    parts = [p.strip() for p in cleaned.split("-") if p.strip()]

    def to_dt(t):
        m = re.match(r"^(\d{1,2}):(\d{2})$", t.strip())
        if not m:
            return None
        h, mi = int(m.group(1)), int(m.group(2))
        try:
            return LONDON.localize(datetime(event_date.year, event_date.month, event_date.day, h, mi))
        except ValueError:
            return None

    start = to_dt(parts[0]) if parts else None
    end = to_dt(parts[1]) if len(parts) > 1 else None
    return start, end


def _classify_session(activity_text):
    a = activity_text.lower().strip()
    if "qualifying race" in a:
        return "qualifying race"
    if "qualifying" in a:
        return "qualifying"
    if "free practice" in a or "practice" in a:
        return "free practice"
    if "british touring car" in a or "kwik fit" in a or "race" in a:
        return "race"
    return "other"


def _scrape_venue(venue):
    url = f"https://btcc.net/circuit/{venue['slug']}/"
    print(f"    BTCC: fetching {url}")

    try:
        resp = requests.get(
            url, timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; BoxBox/1.0)"},
        )
        resp.raise_for_status()
    except Exception as exc:
        print(f"      ERROR: {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    sessions = []
    current_date = None
    race_count = 0

    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name in ("h2", "h3", "h4"):
            heading = el.get_text(strip=True).lower()
            if "saturday" in heading:
                current_date = venue["saturday"]
                race_count = 0
            elif "sunday" in heading:
                current_date = venue["sunday"]
                race_count = 0
            continue

        if current_date is None:
            continue

        for row in el.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            if all(c.name == "th" for c in cells):
                continue
            if _is_logistical_row(row):
                continue
            if not _is_btcc_row(cells):
                continue

            time_raw = cells[0].get_text(strip=True)
            activity_raw = cells[1].get_text(strip=True)
            session_type = _classify_session(activity_raw)

            if len(cells) >= 4:
                champ = cells[2].get_text(strip=True).lower()
                if not any(kw in champ for kw in BTCC_KEYWORDS):
                    continue

            if session_type == "race":
                race_count += 1
                display_label = f"Race {race_count}"
            elif session_type == "free practice":
                display_label = "Free Practice"
            elif session_type == "qualifying race":
                display_label = "Qualifying Race"
            elif session_type == "qualifying":
                display_label = "Qualifying"
            else:
                continue

            start_dt, end_dt = _parse_time_range(time_raw, current_date)
            if not start_dt:
                continue
            if not end_dt:
                end_dt = start_dt + timedelta(minutes=SESSION_DURATIONS.get(session_type, 35))

            sessions.append({
                "series": "BTCC",
                "title": f"{venue['name']} {display_label}",
                "location": venue["location"],
                "start": start_dt,
                "end": end_dt,
                "url": f"https://btcc.net/circuit/{venue['slug']}/",
                "description": (
                    f"BTCC 2026 – Rounds {venue['rounds']}\n"
                    f"{venue['name']} | {display_label}\n\n"
                    f"Sunday races: ITV4 / ITVX\n"
                    f"Qualifying: ITV Sport YouTube\n\n"
                    f"https://btcc.net/circuit/{venue['slug']}/"
                ),
            })

    return sessions


def get_sessions():
    """Return all BTCC 2026 sessions as a list of standardised dicts."""
    all_sessions = []
    for venue in VENUES:
        sessions = _scrape_venue(venue)
        print(f"      {venue['name']}: {len(sessions)} sessions found")
        all_sessions.extend(sessions)
    return all_sessions
