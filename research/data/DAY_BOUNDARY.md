# What the date in a day-file's name actually means

CRYP-005, resolved at source by the Resolver on 2026-08-21 after the lab self-reported it
the same morning. Read this before quoting any per-day number off a `BTC-USD_<date>.csv`.

`research/collector.py` rotates its output once per day and names the file with that day.
Until 2026-08-21 it rotated on the **LOCAL day** (America/Los_Angeles) while CRYP-002 and
SCHED-001 both define this lab's unit as the **UTC day**. The label and the slice disagreed
by seven hours. The lab measured one file and found roughly **60/40** of its rows belonging
to two different UTC days.

## The boundary, file by file

| files | boundary the slice actually uses |
|---|---|
| `BTC-USD_2026-07-22` … `BTC-USD_2026-08-20` | **LOCAL day** (America/Los_Angeles, UTC−7). A file dated D holds `D 00:00 PT` → `D+1 00:00 PT`, i.e. `D 07:00 UTC` → `D+1 07:00 UTC`. |
| `BTC-USD_2026-08-21` | **HYBRID, and it is the only one.** It opened on the local boundary and closes on the UTC one, because the collector was restarted onto UTC rotation part-way through the day. It holds `2026-08-21 07:00 UTC` → `2026-08-22 00:00 UTC`. |
| `BTC-USD_2026-08-22` onward | **UTC day**, which is what the filename has always claimed. |

## What was fixed and what was not

**Fixed:** rotation. Every file from 2026-08-22 is a true UTC-day slice, so the unit the
filename declares is the unit the file contains.

**Not fixed, and it cannot be:** the 31 files already on disk are local-day slices and stay
that way. Re-slicing them would rewrite recorded history to look like something it never
was. They are declared here instead. Any per-day statistic quoted off a file dated
2026-08-21 or earlier is a **local-day** statistic and must say so on its face — which is
what the lab did on 2026-08-21 ("today's file (local day, boundary as above)").

**Nothing scored was ever affected.** The minute instrument reads `target_minute_utc` and
resolves in UTC; the 1-day ledger is retired under CRYP-002 and closed at four rows.
