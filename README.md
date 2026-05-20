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

| Prefix | Series | Sessions included |
|--------|--------|------------------|
| `[BTCC]` | British Touring Car Championship | All races |
| `[F1]` | Formula 1 World Championship | Practice, qualifying, sprint & race |
| `[MotoGP]` | MotoGP World Championship | Qualifying, sprint & race |
| `[Moto2]` | Moto2 World Championship | Race only |
| `[Moto3]` | Moto3 World Championship | Race only |
| `[IndyCar]` | IndyCar Series | Race only |
| `[Formula E]` | ABB FIA Formula E World Championship | Race only |
| `[F2]` | FIA Formula 2 Championship | Sprint & Feature Race |
| `[F3]` | FIA Formula 3 Championship | Sprint & Feature Race |
| `[WEC]` | FIA World Endurance Championship | Qualifying, hyperpole, warm-up & race |
| `[BSB]` | British Superbike Championship | All races (Race 1, 2, 3) |
| `[British GT]` | British GT Championship | All races |
| `[IoM TT]` | Isle of Man TT | All classes |

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
│   ├── f1.py                ← fetches Jolpica/Ergast API
│   ├── motogp_base.py       ← shared MotoGP PulseLive API logic
│   ├── motogp.py            ← MotoGP (qualifying, sprint, race)
│   ├── moto2.py             ← Moto2 (race only)
│   ├── moto3.py             ← Moto3 (race only)
│   ├── calendar_api.py      ← shared motorsportcalendars.com-style API
│   ├── indycar.py           ← IndyCar (race only)
│   ├── formula_e.py         ← Formula E (race only)
│   ├── f2.py                ← F2 (sprint & feature race)
│   ├── f3.py                ← F3 (sprint & feature race)
│   ├── wec.py               ← scrapes fiawec.com
│   ├── bsb.py               ← scrapes britishsuperbike.com
│   ├── british_gt.py        ← scrapes britishgt.com
│   └── iomtt.py             ← hardcoded IoM TT schedule
└── .github/workflows/
    └── generate.yml         ← runs daily at 06:00 UTC
```
