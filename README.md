# BoxBox 🏁

A self-updating motorsport calendar feed for iCloud (and any iCal-compatible app).

All sessions from all series in one subscribable `.ics` file, refreshed daily via GitHub Actions.

## Subscribe

```
https://raw.githubusercontent.com/fillet-bungalow/boxbox/main/boxbox.ics
```

**iCloud on iPhone:** Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar

**iCloud on Mac:** Calendar → File → New Calendar Subscription…

## Series covered

| Prefix | Series |
|--------|--------|
| `[BTCC]` | Kwik Fit British Touring Car Championship |
| `[F1]` | Formula 1 World Championship |
| `[MotoGP]` | MotoGP World Championship (qualifying, sprint & race) |
| `[Moto2]` | Moto2 World Championship (race only) |
| `[Moto3]` | Moto3 World Championship (race only) |

## Event format

```
[BTCC] Snetterton Race 1 🏁
[F1] British GP Qualifying 🏁
```

## Adding a new series

1. Create `scrapers/myseries.py` with a `get_sessions()` function that returns a list of dicts:
   ```python
   {
       "series":      "MYSERIES",   # used for [MYSERIES] prefix
       "title":       "Venue Session Name",
       "location":    "Venue, City Postcode",
       "start":       datetime,     # timezone-aware
       "end":         datetime,     # timezone-aware
       "url":         "https://...",
       "description": "...",
   }
   ```
2. Import and add it to `SCRAPERS` in `generate.py`

## Structure

```
boxbox/
├── generate.py              ← main script
├── scrapers/
│   ├── __init__.py
│   ├── btcc.py              ← scrapes btcc.net
│   ├── f1.py               ← fetches Jolpica API
│   ├── motogp_base.py      ← shared MotoGP PulseLive API logic
│   ├── motogp.py           ← MotoGP class (qualifying, sprint, race)
│   ├── moto2.py            ← Moto2 class (race only)
│   └── moto3.py            ← Moto3 class (race only)
└── .github/workflows/
    └── generate.yml         ← runs daily at 06:00 UTC
```
