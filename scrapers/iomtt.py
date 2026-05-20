"""
BoxBox – Isle of Man TT scraper
2026 race schedule hardcoded from iomttraces.com.
All times are BST (Europe/London). Schedule is weather-dependent;
this reflects the published programme for the 2026 event.
"""

from datetime import datetime, date, time

import pytz

_BST = pytz.timezone("Europe/London")
_URL = "https://www.iomttraces.com/racing/page/schedule/"

# (title, date, time_bst, duration_minutes)
_RACES = [
    ("Superstock Race 1",  date(2026,  5, 30), time(10, 45),  75),
    ("Sidecar Race 1",     date(2026,  5, 30), time(13, 30),  50),
    ("Superbike TT",       date(2026,  5, 31), time(13, 30), 110),
    ("Supersport Race 1",  date(2026,  6,  2), time(10, 45),  80),
    ("Sportbike Race 1",   date(2026,  6,  2), time(14, 15),  70),
    ("Sidecar Race 2",     date(2026,  6,  3), time(10, 45),  50),
    ("Superstock Race 2",  date(2026,  6,  3), time(13, 30),  75),
    ("Supersport Race 2",  date(2026,  6,  5), time(10, 45),  80),
    ("Sportbike Race 2",   date(2026,  6,  5), time(14,  0),  70),
    ("Senior TT",          date(2026,  6,  6), time(11,  0), 110),
]


def get_sessions():
    """Return all 2026 Isle of Man TT race sessions."""
    print("    IoM TT: using hardcoded 2026 schedule")
    sessions = []
    for title, d, t, duration in _RACES:
        start = _BST.localize(datetime.combine(d, t))
        from datetime import timedelta
        end = start + timedelta(minutes=duration)
        sessions.append({
            "series":      "IoM TT",
            "title":       title,
            "location":    "Isle of Man TT Course, Isle of Man",
            "start":       start,
            "end":         end,
            "url":         _URL,
            "description": (
                f"Isle of Man TT 2026\n{title}\n\n"
                f"Watch at iomttraces.com/live\n\n{_URL}"
            ),
        })
    print(f"      {len(sessions)} races")
    return sessions
