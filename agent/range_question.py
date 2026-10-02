#!/opt/anaconda3/bin/python
"""range_question.py - the flow agent's STANDING QUESTION (CRYPTO-008, 2026-10-02): state its base rate, file it, resolve it.

CRYPTO-008 (a) RE-AIM: CRYPTO-006 stopped the minute forecaster, so the old daily question ("minute forecaster directional hit rate on
<day> UTC ...") can never resolve for a new day. The lab's daily forecast is now ONE question the surviving data can answer: a
volatility question on the recorded Coinbase tape, resolved mechanically from research/minutes/BTC-USD_<day>.csv (written once, after
the day ends, by the nightly rotation). It is ONE forecast question, not a strategy: a calibration instrument, barred from trading.

THE QUESTION (frozen; a different bar or a different wording is a NEW question, registered anew, never an edit):

    BTC-USD UTC-day high-low range on <D> (minute file, 100*(max high - min low)/min low) exceeds 3.0%

  range  = 100 * (max high - min low) / min low over the minutes of UTC day D in the minute file (rows whose minute_utc is on D).
  YES    = the range STRICTLY exceeds X (exact decimal arithmetic; a range of exactly X is NO).
  VOID   = fewer than 1,300 valid minutes (high and low both readable) - crypto-desk's MIN_MINUTES_FOR_DAY, one rule for every BTC
           UTC-day question in the estate. A gap in the tape is never imputed. A gap can only SHRINK the observed range, so a YES is
           certain even on a thin day and a NO means "no more than X% in the minutes recorded": the void rule is symmetric on purpose,
           because voiding only the thin NO days would bias the scored sample toward YES.
  WAITING = the minute file for D does not exist yet (the rotation writes it ~00:40 UTC after the day ends): never void, never guessed.
            If it is still missing 3+ days later while a LATER day's file exists, nothing was recorded that day: VOID.
  X      = 3.0, declared from the tape's own history before any row existed (see `reference`); a row at any other X is not this
           question and is never scored here (listed as UNREGISTERED).

Commands (all read-only except `file` and `resolve`, which write agent/forecasts.csv atomically, BOOK-001: write-beside + replace under
the book's flock; if atomicio cannot be loaded they REFUSE rather than fall back to open(path, "w")):

  range_question.py reference [--as-of YYYY-MM-DD]   the base rate over the eligible complete UTC days (what p is filed against)
  range_question.py file --p P --note TEXT [--dry]   append today's ONE row: canonical question, S8 target day, check_date, notes
  range_question.py resolve [--dry]                  score every due row of this form from the minute files; rows already scored,
                                                     rows of any other form and the retired question's rows are never touched

Nothing here edits a scored row (BENCH-002), moves X, or reads another lab's files. A row that is not EXACTLY the canonical form is
listed and left alone, so a paraphrase is never guessed at.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import importlib.util
import os
import re
import sys
from decimal import Decimal, InvalidOperation

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HOME = os.path.expanduser("~")

PRODUCT = "BTC-USD"
X_REGISTERED = (Decimal("3.0"),)      # the frozen bar (CRYPTO-008). Any other X is a different question.
MIN_MINUTES = 1300                    # valid minutes a UTC day needs; crypto-desk cd/registry.py MIN_MINUTES_FOR_DAY
CLEAN_FROM = "2026-08-22"             # first UTC-slice minute file: before it a file is a LOCAL-day slice (research/data/DAY_BOUNDARY.md)
LATE_VOID_DAYS = 3                    # a missing file this many days late, with a later day's file present, means no recording that day
QUESTION = "BTC-USD UTC-day high-low range on {d} (minute file, 100*(max high - min low)/min low) exceeds {x}%"
Q_RE = re.compile(r"^BTC-USD UTC-day high-low range on (\d{4}-\d{2}-\d{2}) "
                  r"\(minute file, 100\*\(max high - min low\)/min low\) exceeds (\d+(?:\.\d+)?)%$")
LEGACY_PREFIX = "minute forecaster directional hit rate on "      # the retired question (CRYP-002, stopped by CRYPTO-006)
COLS = ["date", "instrument", "horizon_days", "question", "p", "check_date", "outcome", "notes"]

# set from the command line so a test can point the whole tool at a scratch copy; the defaults are the lab's real files
BOOK = os.path.join(HERE, "forecasts.csv")
MINUTES = os.path.join(ROOT, "research", "minutes")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _atomic():
    """stock-radar/atomicio.py by path. Writers REFUSE without it: a fallback to open(path, "w") is the one-sided guard BOOK-001 forbids."""
    try:
        return _load("_atomicio_cr008", f"{HOME}/stock-radar/atomicio.py")
    except Exception as e:
        raise SystemExit(f"REFUSED: stock-radar/atomicio.py could not be loaded ({type(e).__name__}: {e}); "
                         f"BOOK-001 forbids a non-atomic write of a shared book")


# ---------------------------------------------------------------------------------------------------------- the tape
def _dec(v):
    try:
        d = Decimal(str(v).strip())
    except (InvalidOperation, ValueError):
        return None
    return d if d.is_finite() else None


def day_stats(day, minutes_dir=None):
    """(n_valid_minutes, max_high, min_low) for UTC day `day` from its minute file, or None if the file does not exist.
    A minute is valid when it is on `day` (minute_utc) and its high and low both read as finite positive numbers with high >= low."""
    p = os.path.join(minutes_dir or MINUTES, f"{PRODUCT}_{day}.csv")
    if not os.path.exists(p):
        return None
    n, hi, lo = 0, None, None
    with open(p, newline="") as fh:
        for r in csv.DictReader(fh):
            if not (r.get("minute_utc") or "").startswith(day):
                continue
            h, l = _dec(r.get("high")), _dec(r.get("low"))
            if h is None or l is None or l <= 0 or h < l:
                continue
            n += 1
            hi = h if hi is None or h > hi else hi
            lo = l if lo is None or l < lo else lo
    return n, hi, lo


def range_pct(hi, lo):
    return 100 * (hi - lo) / lo


def exceeds(hi, lo, x):
    """Exact decimal: 100*(hi-lo)/lo > x  <=>  100*(hi-lo) > x*lo  (lo > 0). A range of exactly x is NOT a YES."""
    return 100 * (hi - lo) > x * lo


def minute_days(minutes_dir=None):
    out = []
    for f in sorted(glob.glob(os.path.join(minutes_dir or MINUTES, f"{PRODUCT}_*.csv"))):
        out.append(os.path.basename(f)[len(PRODUCT) + 1:-4])
    return out


def reference(as_of, minutes_dir=None):
    """The reference class the standing question's p is filed against: the eligible complete UTC days (UTC-slice files from CLEAN_FROM,
    day < as_of, >= MIN_MINUTES valid minutes) and how many of them exceeded the registered X. as_of is a date: only days BEFORE it count."""
    x = X_REGISTERED[0]
    elig = []
    for day in minute_days(minutes_dir):
        if day < CLEAN_FROM or day >= as_of.isoformat():
            continue
        st = day_stats(day, minutes_dir)
        if st and st[0] >= MIN_MINUTES:
            elig.append((day, st[0], range_pct(st[1], st[2]), exceeds(st[1], st[2], x)))
    k = sum(1 for e in elig if e[3])
    base = (Decimal(k) / Decimal(len(elig))) if elig else None
    last = [f"{d} {r:.2f}%" for d, _, r, _ in elig[-3:]]
    line = (f"REFERENCE CLASS recomputed by range_question.py: eligible complete UTC days (>= {MIN_MINUTES} valid minutes, UTC-slice files from "
            f"{CLEAN_FROM}) through {elig[-1][0] if elig else 'none'} = {len(elig)}, of which {k} exceeded {x}% -> base "
            f"{base:.3f}" if elig else "REFERENCE CLASS: no eligible day yet") + (f"; last three eligible days {', '.join(last)}." if elig else ".")
    return {"n": len(elig), "k": k, "base": base, "last": last, "line": line, "days": elig}


# --------------------------------------------------------------------------------------------------------- the book
def read_book(path):
    with open(path, newline="") as fh:
        rd = csv.DictReader(fh)
        cols, rows = list(rd.fieldnames or []), list(rd)
    if cols != COLS:
        raise SystemExit(f"REFUSED: {path} has header {cols}, expected {COLS}")
    return cols, rows


def canonical(row):
    return Q_RE.match((row.get("question") or "").strip())


def next_target(rows, now_utc):
    """S8 + ONE ROW PER RESOLVING DAY: the first UTC day strictly after the UTC date at filing that no canonical row already targets.
    A target day that has begun at filing is partly visible and is never a forecast."""
    taken = {m.group(1) for m in (canonical(r) for r in rows) if m}
    d = now_utc.date() + dt.timedelta(days=1)
    while d.isoformat() in taken:
        d += dt.timedelta(days=1)
    return d


def _p_cal(p):
    """CAL-001 consumer: the calibrated shadow of p, recorded beside it (p stays the registered forecast). Never silent on failure."""
    try:
        return f"{_load('_calibrate_cr008', f'{HOME}/command-center/calibrate.py').calibrate('crypto-microstructure', p):.4f}".rstrip("0").rstrip(".")
    except Exception as e:
        return f"ERR({type(e).__name__})"


# ---------------------------------------------------------------------------------------------------------- commands
def cmd_reference(args):
    as_of = dt.date.fromisoformat(args.as_of) if args.as_of else dt.datetime.now(dt.timezone.utc).date()
    ref = reference(as_of)
    print(ref["line"])
    print(f"as-of {as_of} (UTC): X = {X_REGISTERED[0]}% is the frozen bar; file p against this base unless a conditional has been "
          f"established at the lab's own S14 standard.")
    return 0


def cmd_file(args):
    try:
        p = Decimal(args.p)
    except InvalidOperation:
        raise SystemExit(f"REFUSED: --p {args.p!r} is not a number")
    if not (Decimal(0) < p < Decimal(1)) or p.as_tuple().exponent < -3:
        raise SystemExit("REFUSED: p must be strictly between 0 and 1 with at most 3 decimals")
    note = (args.note or "").strip()
    if len(note) < 20:
        raise SystemExit("REFUSED: --note must carry the run's own reasoning (at least 20 characters); a bare number is not a forecast")
    now_local = dt.datetime.now().astimezone() if not args.now else dt.datetime.fromisoformat(args.now).astimezone()
    now_utc = now_local.astimezone(dt.timezone.utc)
    atom = None if args.dry else _atomic()
    if atom:
        atom.hold_book(BOOK)                       # BOOK-001: the lock is taken BEFORE the first read and held to process exit
    cols, rows = read_book(BOOK)
    filed_date = now_local.date().isoformat()
    if any(canonical(r) and r["date"] == filed_date for r in rows):
        raise SystemExit(f"REFUSED: a row of this question was already filed on {filed_date} - exactly one per run, and a second would "
                         f"be the same observation twice")
    target = next_target(rows, now_utc)
    x = X_REGISTERED[0]
    ref = reference(now_utc.date())
    pcal = _p_cal(float(p))
    row = {
        "date": filed_date, "instrument": "BTC", "horizon_days": str((target - now_local.date()).days),
        "question": QUESTION.format(d=target.isoformat(), x=x), "p": format(p, "f"), "check_date": target.isoformat(), "outcome": "",
        "notes": (f"[flow] [tech] [p_cal={pcal}] Resolves check_date+1 (standing, SCHED-001) -- a PASS by construction, never a deferral. "
                  f"Filed {now_local:%Y-%m-%d %H:%M %Z} ({now_utc:%H:%M} UTC) by range_question.py (CRYPTO-008 standing question). "
                  f"TARGET {target} UTC, not today's: no target day may have begun at filing (S8); ONE ROW PER RESOLVING DAY. "
                  f"{ref['line']} VOID RULE fixed in advance: fewer than {MIN_MINUTES} valid minutes in research/minutes/BTC-USD_{target}.csv "
                  f"= void; a gap in the tape is never imputed. RESOLUTION, mechanical: `python agent/range_question.py resolve` "
                  f"-> YES iff 100*(max high - min low)/min low over that file's minutes strictly exceeds {x} (exact decimal). "
                  f"BARRED FROM TRADING: a calibration question, never a signal. | {note}"),
    }
    print(f"{'[DRY] ' if args.dry else ''}row: date {row['date']} horizon {row['horizon_days']}d target {target} p {row['p']} p_cal {pcal}")
    print(f"  {row['question']}")
    print(f"  {ref['line']}")
    if not args.dry:
        rows.append(row)
        atom.atomic_csv(BOOK, cols, rows)         # BOOK-001: write-beside + replace; a reader sees the old book or the new one
        print(f"filed -> {os.path.relpath(BOOK, HOME)} ({len(rows)} rows)")
    return 0


def cmd_resolve(args):
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(dt.timezone.utc).date()
    atom = None if args.dry else _atomic()
    if atom:
        atom.hold_book(BOOK)
    cols, rows = read_book(BOOK)
    have = set(minute_days())
    scored = voided = waiting = 0
    lines, changed = [], False
    for r in rows:
        if (r.get("outcome") or "").strip():
            continue                                     # a scored (or void) row is never edited again (BENCH-002)
        q = (r.get("question") or "").strip()
        m = Q_RE.match(q)
        if not m:
            lines.append(f"  {'LEGACY' if q.startswith(LEGACY_PREFIX) else 'SKIP (unparsed)'}: {r.get('date')} - {q[:84]}"
                         + (" (retired question: its own rule, not this tool)" if q.startswith(LEGACY_PREFIX) else ""))
            continue
        day, xs = m.group(1), m.group(2)
        x = Decimal(xs)
        if x not in X_REGISTERED:
            lines.append(f"  UNREGISTERED: {r['date']} asks {xs}%, the registered bar is {X_REGISTERED[0]}% - a different question, never scored here")
            continue
        if r.get("check_date") != day:
            lines.append(f"  REFUSED: {r['date']} check_date {r.get('check_date')!r} disagrees with the question's day {day}")
            continue
        if day >= today.isoformat():
            waiting += 1
            lines.append(f"  waiting: {day} has not ended yet")
            continue
        st = day_stats(day)
        if st is None:
            late = (today - dt.date.fromisoformat(day)).days
            if late >= LATE_VOID_DAYS and any(d > day for d in have):
                r["outcome"] = "void"
                r["notes"] = (r.get("notes") or "") + (f" | VOID {today} by range_question.py: no minute file for {day} {late} days on, while a later "
                                                        f"day's file exists - nothing was recorded that day; a gap is never imputed")
                voided += 1; changed = True
                lines.append(f"  VOID {day}: no minute file ({late} days late, later files exist)")
            else:
                waiting += 1
                lines.append(f"  waiting: no minute file for {day} yet" + (f" ({late} days late: OVERDUE)" if late >= LATE_VOID_DAYS else ""))
            continue
        n, hi, lo = st
        if n < MIN_MINUTES:
            r["outcome"] = "void"
            r["notes"] = (r.get("notes") or "") + (f" | VOID {today} by range_question.py: {n} valid minutes on {day} < {MIN_MINUTES}; "
                                                    f"a gap in the tape is never imputed")
            voided += 1; changed = True
            lines.append(f"  VOID {day}: {n} valid minutes < {MIN_MINUTES}")
            continue
        yes = exceeds(hi, lo, x)
        rng = range_pct(hi, lo)
        r["outcome"] = "1" if yes else "0"
        r["notes"] = (r.get("notes") or "") + (f" | RESOLVED {today} by range_question.py: BTC-USD {day} range {rng:.3f}% (high {hi}, low {lo}, "
                                               f"{n} minutes) {'>' if yes else '<='} {x}% -> {'YES' if yes else 'NO'}")
        scored += 1; changed = True
        lines.append(f"  {day}: range {rng:.3f}% (n={n}) {'>' if yes else '<='} {x}% -> {'YES' if yes else 'no'}  (p={r['p']})")
    if changed and not args.dry:
        atom.atomic_csv(BOOK, cols, rows)             # BOOK-001
    for l in lines:
        print(l)
    print(f"range_question resolve {today}: {scored} scored, {voided} void, {waiting} waiting{' [DRY]' if args.dry else ''}")
    return 0


def main(argv=None):
    global BOOK, MINUTES
    ap = argparse.ArgumentParser(description="CRYPTO-008 standing question: reference | file | resolve")
    ap.add_argument("--book", help="forecasts.csv path (default: the lab's; a test points this at a scratch copy)")
    ap.add_argument("--minutes-dir", help="research/minutes path (default: the lab's)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("reference"); s.add_argument("--as-of")
    s = sub.add_parser("file"); s.add_argument("--p", required=True); s.add_argument("--note", required=True)
    s.add_argument("--dry", action="store_true"); s.add_argument("--now", help="ISO time override (tests)")
    s = sub.add_parser("resolve"); s.add_argument("--dry", action="store_true"); s.add_argument("--today", help="YYYY-MM-DD UTC override (tests)")
    args = ap.parse_args(argv)
    if args.book:
        BOOK = args.book
    if args.minutes_dir:
        MINUTES = args.minutes_dir
    return {"reference": cmd_reference, "file": cmd_file, "resolve": cmd_resolve}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
