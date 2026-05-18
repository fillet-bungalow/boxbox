# BTCC 2026 iCal Feed

Auto-generates a subscribable `.ics` calendar feed for the BTCC 2026 season, scraped daily from [btcc.net](https://btcc.net).

## Sessions included

Each race weekend includes:
- 🏁 Free Practice (Saturday)
- 🏁 Qualifying (Saturday)
- 🏁 Qualifying Race (Saturday – new for 2026)
- 🏁 Race 1, 2 & 3 (Sunday)

## Subscribe in iCloud Calendar

1. Copy the **raw URL** of `btcc_2026.ics` from this repo:
   ```
   https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/btcc_2026.ics
   ```
2. On iPhone: **Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar**
3. Paste the URL and tap Next
4. On Mac: **Calendar → File → New Calendar Subscription…** and paste the URL

iCloud will refresh the feed automatically. The GitHub Action updates the file daily at 06:00 UTC.

## How it works

`btcc_scraper.py` fetches each circuit page from btcc.net, parses the timetable tables, filters for BTCC sessions, and writes a valid `.ics` file. Session UIDs are stable (MD5 of venue + label + start time) so iCloud won't duplicate events on refresh.

## Rounds covered

| Round | Venue | Date |
|---|---|---|
| 7–9 | Snetterton | 23–24 May |
| 10–12 | Oulton Park | 6–7 Jun |
| 13–15 | Thruxton | 25–26 Jul |
| 16–18 | Knockhill | 8–9 Aug |
| 19–21 | Donington Park GP | 22–23 Aug |
| 22–24 | Croft | 5–6 Sep |
| 25–27 | Silverstone | 26–27 Sep |
| 28–30 | Brands Hatch GP | 10–11 Oct |

Rounds 1–6 (Donington Park & Brands Hatch Indy) have already taken place and are not included.
