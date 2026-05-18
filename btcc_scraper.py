#!/usr/bin/env python3
"""
BTCC 2026 Season ICS Generator
Scrapes btcc.net circuit pages and builds a subscribable iCal feed.
Run daily via cron / GitHub Actions to keep session times up to date.
"""

import re
import hashlib
from datetime import datetime, date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
import pytz

LONDON = pytz.timezone("Europe/London")

VENUES = [
    {
        "name": "Snetterton",
        "slug": "snetterton",
        "saturday": date(2026, 5, 23),
        "sunday": date(2026, 5, 24),
        "rounds": "7, 8 & 9",
        "location": "Snetterton Circuit, Norwich, Norfolk, NR16 2JU",
    },
    {
        "name": "Oulton Park",
        "slug": "oulton-park",
        "saturday": date(2026, 6, 6),
        "sunday": date(2026, 6, 7),
        "rounds": "10, 11 & 12",
        "location": "Oulton Park Circuit, Little Budworth, Cheshire, CW6 9BW",
    },
    {
        "name": "Thruxton",
        "slug": "thruxton",
        "saturday": date(2026, 7, 25),
        "sunday": date(2026, 7, 26),
        "rounds": "13, 14 & 15",
        "location": "Thruxton Circuit, Andover, Hampshire, SP11 8PN",
    },
    {
        "name": "Knockhill",
        "slug": "knockhill",
        "saturday": date(2026, 8, 8),
        "sunday": date(2026, 8, 9),
        "rounds": "16, 17 & 18",
        "location": "Knockhill Racing Circuit, Dunfermline, Fife, KY12 9TF",
    },
    {
        "name": "Donington Park GP",
        "slug": "donington-park-gp",
        "saturday": date(2026, 8, 22),
        "sunday": date(2026, 8, 23),
        "rounds": "19, 20 & 21",
        "location": "Donington Park Circuit, Castle Donington, Leicestershire, DE74 2RP",
    },
    {
        "name": "Croft",
        "slug": "croft",
        "saturday": date(2026, 9, 5),
        "sunday": date(2026, 9, 6),
        "rounds": "22, 23 & 24",
        "location": "Croft Circuit, Darlington, County Durham, DL2 2PL",
    },
    {
        "name": "Silverstone",
        "slug": "silverstone",
        "saturday": date(2026, 9, 26),
        "sunday": date(2026, 9, 27),
        "rounds": "25, 26 & 27",
        "location": "Silverstone Circuit, Towcester, Northamptonshire, NN12 8TN",
    },
    {
        "name": "Brands Hatch GP",
        "slug": "brands-hatch-gp",
        "saturday": date(2026, 10, 10),
        "sunday": date(2026, 10, 11),
        "rounds": "28, 29 & 30",
        "location": "Brands Hatch Circuit, Fawkham, Longfield, Kent, DA3 8NG",
    },
]

BTCC_KEYWORDS = [
    "kwik fit british touring car",
    "british touring car championship",
    "qualifying race",  # BTCC qualifying race rows may just say this
]

# Default durations (minutes) when no end time is listed
SESSION_DURATIONS = {
    "free practice": 40,
    "qualifying": 35,
    "qualifying race": 25,
    "race": 35,
}


def is_btcc_row(cells):
    """Return True if any cell references the BTCC."""
    text = " ".join(c.get_text(strip=True).lower() for c in cells)
    return any(kw in text for kw in BTCC_KEYWORDS)


def is_logistical_row(row):
    """Skip non-session rows: lunch breaks, pit lane opens, autograph sessions, etc."""
    text = row.get_text(strip=True).lower()
    skip_phrases = [
        "lunch break", "pit lane opens", "pit lane walkabout",
        "autograph session", "to grid", "tbc",
    ]
    # Rows with italic/em content are typically logistical
    if row.find(["em", "i"]):
        return True
    return any(p in text for p in skip_phrases)


def parse_time_range(raw, event_date):
    """
    Parse strings like '10:30 – 11:10', '09.15 – 09.50', '15:05'
    Returns (start_dt, end_dt). end_dt may be None.
    """
    # Normalise separators: dots to colons, various dashes to ASCII hyphen
    cleaned = raw.strip().replace(".", ":").replace("–", "-").replace("—", "-")
    # Strip anything that isn't digits, colons, hyphens, or spaces
    cleaned = re.sub(r"[^\d:\-\s]", "", cleaned).strip()

    parts = [p.strip() for p in cleaned.split("-") if p.strip()]

    def to_dt(t):
        t = t.strip()
        m = re.match(r"^(\d{1,2}):(\d{2})$", t)
        if not m:
            return None
        h, mi = int(m.group(1)), int(m.group(2))
        try:
            naive = datetime(event_date.year, event_date.month, event_date.day, h, mi)
            return LONDON.localize(naive)
        except ValueError:
            return None

    start = to_dt(parts[0]) if parts else None
    end = to_dt(parts[1]) if len(parts) > 1 else None
    return start, end


def classify_session(activity_text):
    """Map raw activity text to a clean session label."""
    a = activity_text.lower().strip()
    if "qualifying race" in a:
        return "qualifying race"
    if "qualifying" in a:
        return "qualifying"
    if "free practice" in a or "practice" in a:
        return "free practice"
    # Sunday BTCC rows have the full championship name as the activity
    if "british touring car" in a or "kwik fit" in a:
        return "race"
    if "race" in a:
        return "race"
    return "other"


def scrape_venue(venue):
    """Fetch a circuit page and return a list of BTCC session dicts."""
    url = f"https://btcc.net/circuit/{venue['slug']}/"
    print(f"  → {url}")

    try:
        resp = requests.get(
            url, timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; BTCC-Cal/1.0)"},
        )
        resp.raise_for_status()
    except Exception as exc:
        print(f"    ERROR: {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    sessions = []
    current_date = None
    race_count = 0

    # Walk top-level content elements in document order
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

        # It's a <table>
        if current_date is None:
            continue

        for row in el.find_all("tr"):
            cells = row.find_all(["td", "th"])

            # Skip header rows and short rows
            if len(cells) < 2:
                continue
            if all(c.name == "th" for c in cells):
                continue
            if is_logistical_row(row):
                continue
            if not is_btcc_row(cells):
                continue

            time_raw = cells[0].get_text(strip=True)
            activity_raw = cells[1].get_text(strip=True)

            session_type = classify_session(activity_raw)

            # Saturday 4-col rows: Time | Activity | Championship | Laps
            # The Activity column has the session type ("Free Practice", "Qualifying Race", etc.)
            # Sunday 3-col rows: Time | Championship name | Laps
            # The Activity column is the championship name → classify as race
            if len(cells) >= 4:
                # Double-check: championship column (index 2) should confirm BTCC
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
                continue  # skip unknowns

            start_dt, end_dt = parse_time_range(time_raw, current_date)
            if not start_dt:
                print(f"    Could not parse time: {repr(time_raw)}")
                continue

            if not end_dt:
                mins = SESSION_DURATIONS.get(session_type, 35)
                end_dt = start_dt + timedelta(minutes=mins)

            sessions.append({
                "venue": venue["name"],
                "rounds": venue["rounds"],
                "location": venue["location"],
                "label": display_label,
                "start": start_dt,
                "end": end_dt,
            })

    return sessions


def build_calendar(all_sessions):
    cal = Calendar()
    cal.add("prodid", "-//BTCC 2026 Calendar//btcc-cal//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", "BTCC 2026")
    cal.add("x-wr-timezone", "Europe/London")
    cal.add("x-wr-caldesc", "BTCC 2026 session times – all rounds. Auto-generated from btcc.net")
    cal.add("refresh-interval;value=duration", "P1D")
    cal.add("x-published-ttl", "P1D")

    for s in all_sessions:
        event = Event()
        event.add("summary", f"🏁 BTCC {s['label']} – {s['venue']}")
        event.add("dtstart", s["start"])
        event.add("dtend", s["end"])
        event.add("location", s["location"])
        event.add("description", (
            f"BTCC 2026 – Rounds {s['rounds']}\n"
            f"{s['venue']}\n\n"
            f"{s['label']}\n\n"
            f"Sunday races live on ITV4 / ITVX\n"
            f"Qualifying live on ITV Sport YouTube\n\n"
            f"Source: btcc.net"
        ))
        uid_src = f"btcc-2026-{s['venue']}-{s['label']}-{s['start'].isoformat()}"
        event.add("uid", hashlib.md5(uid_src.encode()).hexdigest() + "@btcc-cal")
        event.add("dtstamp", datetime.now(pytz.utc))
        cal.add_component(event)

    return cal


if __name__ == "__main__":
    print("BTCC 2026 ICS Generator")
    print("=" * 50)

    all_sessions = []

    for venue in VENUES:
        print(f"\n{venue['name']}  ({venue['saturday']} / {venue['sunday']})")
        sessions = scrape_venue(venue)
        if sessions:
            for s in sessions:
                day = "Sat" if s["start"].date() == venue["saturday"] else "Sun"
                print(f"    {day} {s['start'].strftime('%H:%M')}–{s['end'].strftime('%H:%M')}  {s['label']}")
        else:
            print("    (no sessions found)")
        all_sessions.extend(sessions)

    print(f"\nTotal BTCC sessions found: {len(all_sessions)}")

    cal = build_calendar(all_sessions)
    out = Path("btcc_2026.ics")
    out.write_bytes(cal.to_ical())
    print(f"Written: {out}  ({out.stat().st_size:,} bytes)")
