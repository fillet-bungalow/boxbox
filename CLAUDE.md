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

This fetches live data from btcc.net and the Jolpica API, then writes `boxbox.ics`.

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

## Adding a new series

1. Create `scrapers/myseries.py` with a `get_sessions()` function returning the standard dict format above.
2. Import it in `generate.py` and append it to the `SCRAPERS` list.
