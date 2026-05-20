# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

BoxBox generates a single `boxbox.ics` calendar feed combining motorsport sessions from multiple series. GitHub Actions runs `generate.py` daily at 06:00 UTC and commits the updated `.ics` file to `main`.

## Running locally

Install dependencies:
```
pip install requests beautifulsoup4 icalendar pytz
```

Generate the calendar:
```
python generate.py
```

This fetches live data from multiple sources and writes `boxbox.ics`.

## Architecture

`generate.py` imports each scraper from `scrapers/`, calls `get_sessions()` on each, merges and sorts the results chronologically, then writes the iCal file using `icalendar`.

Each scraper must export a single function:
```python
def get_sessions() -> list[dict]:
```

Each dict in the list must have these keys:
```python
{
    "series":      str,       # used as [PREFIX] in calendar summary
    "title":       str,       # "Venue Session Name"
    "location":    str,
    "start":       datetime,  # timezone-aware
    "end":         datetime,  # timezone-aware
    "url":         str,
    "description": str,
}
```

Event UIDs are derived from an MD5 hash of `series + title + start ISO string`, so they remain stable across runs as long as those three values don't change.

## Scrapers

- **`scrapers/btcc.py`** — HTML scraper against `btcc.net/circuit/<slug>/`. Hardcodes venue dates and locations for the season. Walks page DOM looking for schedule tables, filters to BTCC rows by keyword matching, classifies session type, and parses time ranges into timezone-aware `Europe/London` datetimes. Falls back to fixed durations per session type when end time is absent.

- **`scrapers/f1.py`** — Fetches `https://api.jolpi.ca/ergast/f1/2026.json` (Jolpica/Ergast API). Builds sessions from the structured JSON; race end times use fixed durations since the API only provides start times.

- **`scrapers/motogp.py`**, **`scrapers/moto2.py`**, **`scrapers/moto3.py`** — Thin wrappers over `scrapers/motogp_base.py`, which fetches from the MotoGP PulseLive API (`api.motogp.pulselive.com/motogp/v1/results`). The event list is fetched once and cached at module level; all three scrapers share it. MotoGP includes Q1, Q2, Sprint, and Race; Moto2/Moto3 include Race only. The season UUID and category UUIDs are hardcoded constants in `motogp_base.py` — update `_SEASON_UUID` when adding a new year.

- **`scrapers/calendar_api.py`** — Shared utility for the motorsportcalendars.com-style JSON APIs (IndyCar, Formula E, F2, F3). Call `fetch_sessions(api_url, series, allowed_sessions, session_durations, series_url)`. Note: uses `.replace("Z", "+00:00")` before `fromisoformat()` for Python 3.9 compatibility.

- **`scrapers/indycar.py`** — Uses `https://www.indycarcalendar.com/api/calendar`. Races only (120 min).

- **`scrapers/formula_e.py`** — Uses `https://formulaecal.com/api/calendar` (no `www.`). Races only (50 min).

- **`scrapers/f2.py`** — Uses `https://www.f2calendar.com/api/calendar`. Sprint (35 min) and Feature Race (50 min).

- **`scrapers/f3.py`** — Uses `https://www.f3calendar.com/api/calendar`. Sprint (30 min) and Feature Race (45 min).

- **`scrapers/wec.py`** — HTML scraper for `fiawec.com/en/race/<slug>`. Uses `data-timestamp` Unix UTC attributes for exact session times; no timezone parsing needed. 8 event slugs hardcoded. Includes qualifying, hyperpole, warm-up, and race. Future rounds show 0 sessions until times are published.

- **`scrapers/bsb.py`** — HTML scraper for `britishsuperbike.com/calendar/2026/<slug>`. 11 round slugs and start dates hardcoded. Finds "Race N" text nodes, walks 3 levels up to the container holding `"{Day} Race N {time} BST"`, and maps the day abbreviation to a concrete date via weekday offset from the round start date.

- **`scrapers/british_gt.py`** — HTML scraper for `britishgt.com/event/<id>`. Slices the full page text into per-day sections by finding day headers ("Monday, 25 May" etc.) then searches each slice for `Race N {local} {gmt}` or `Race {local} {gmt}` (single-race events like Silverstone). Skips sessions with placeholder 00:00 local times. 6 event IDs hardcoded.

- **`scrapers/iomtt.py`** — Fully hardcoded 2026 schedule (10 races across all classes). Update `_RACES` each year from `iomttraces.com/racing/page/schedule/`.

## Adding a new series

1. Create `scrapers/myseries.py` with a `get_sessions()` function returning the standard dict format above.
2. Import it in `generate.py` and append it to the `SCRAPERS` list.
