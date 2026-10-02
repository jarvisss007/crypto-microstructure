"""PROPOSED resolver checks for CRYPTO-008 — handed to the session that owns council/resolver.py. NOT wired.

CRYPTO-008 (a) RE-AIM (ruled 2026-10-02 by Claude under Anupam's delegation, 'do what neceassary adn audit all the built', 13:02 PT): the flow
agent's one daily forecast is no longer the stopped minute forecaster's hit rate but ONE standing volatility question on the recorded tape,
`BTC-USD UTC-day high-low range on <D> (minute file, 100*(max high - min low)/min low) exceeds 3.0%`, filed and resolved by
~/crypto-microstructure/agent/range_question.py. resolver.py, issues.json and ~/bin/resolve_forecasts.py were NOT edited. Every name here carries
the _crypto008_ prefix; every check is read-only. Suggested registry lines:

    "crypto008_mandate_declared": _crypto008_mandate_declared,          # attach to CRYPTO-008's `check` field (with crypto008_executed)
    "crypto008_rows_conform": _crypto008_rows_conform,
    "crypto008_resolutions_recompute": _crypto008_resolutions_recompute,
    "crypto008_legacy_rows_immutable": _crypto008_legacy_rows_immutable,
    "crypto008_executed": _crypto008_executed,                          # mandate_declared AND legacy_rows_immutable AND rows_conform

CHK-001: a check no register row names never runs, so register a MONITOR row (suggested id CRYPTO-009, type monitor, lab crypto-microstructure)
naming crypto008_resolutions_recompute and crypto008_rows_conform, as CRYPTO-007 did for the stop. They do not move any bar: they hold the
mandate to what it says. `check_labs_still_forecasting` needs NO change: it reads the newest `date` in agent/forecasts.csv and the new rows carry
the filing date (shown green on a copy that holds a filed row; see the README of the run).

What each guards (the failure it exists for):
  mandate_declared     the mandate text, the tool's constants and the tape agree: the canonical question string, X = 3.0 frozen, 1,300 minutes, the run
                       order, and the pre-declaration's own numbers (the 23 eligible days and the 10 that exceeded 3.0%) REPRODUCE from the minute files.
                       A silent change of X, of the void rule or of the wording turns it red (a bar chosen by date is not a bar that has closed).
  rows_conform         every row filed from 2026-10-02 is the canonical question at the registered X, filed once per run and once per resolving day,
                       target strictly after the UTC date at filing (S8), check_date = the target, horizon_days consistent, p strictly inside (0,1) with at
                       most 3 decimals, notes carrying the standard tags and the filing stamp. A row of any other form filed after CRYPTO-008 is red.
  resolutions_recompute every scored row is RESOLVED by range_question.py (its stamp is in the notes) and its outcome equals an INDEPENDENT recomputation
                       from the minute file; a void row is thin (< 1,300 valid minutes) or provably unrecorded; a due row left blank with its file present
                       3+ days on is red (a lab that resolves nothing must age in public, FCST-004's lesson).
  legacy_rows_immutable the 42 rows filed before CRYPTO-008 keep their immutable fields and the 40 outcomes already scored (BENCH-002); the two still
                       pending may be scored once, by their own rule, and nothing else about them may change.

Run live:        /opt/anaconda3/bin/python PROPOSED_resolver_checks_CRYPTO-008.py
Negative controls (on COPIES in a temp dir, never the real book): /opt/anaconda3/bin/python PROPOSED_resolver_checks_CRYPTO-008.py --controls
"""
import csv
import datetime as dt
import hashlib
import importlib.util
import os
import re
import shutil
import sys
import tempfile
from decimal import Decimal

HOME = os.path.expanduser("~")
_CRYPTO008_LAB = os.path.expanduser("~/crypto-microstructure")
_CRYPTO008_BOOK = _CRYPTO008_LAB + "/agent/forecasts.csv"
_CRYPTO008_AGENT = _CRYPTO008_LAB + "/agent/AGENT.md"
_CRYPTO008_TOOL = _CRYPTO008_LAB + "/agent/range_question.py"
_CRYPTO008_MINUTES = _CRYPTO008_LAB + "/research/minutes"
_CRYPTO008_FIRST_DAY = "2026-10-02"          # the standing form did not exist before this filing date
_CRYPTO008_X = Decimal("3.0")
_CRYPTO008_MIN = 1300                          # crypto-desk MIN_MINUTES_FOR_DAY
_CRYPTO008_GRACE_DAYS = 3                      # a due row may wait this long for the sweep/rotation before it is red
_CRYPTO008_Q = (r"^BTC-USD UTC-day high-low range on (\d{4}-\d{2}-\d{2}) "
                r"\(minute file, 100\*\(max high - min low\)/min low\) exceeds (\d+(?:\.\d+)?)%$")
_CRYPTO008_LEGACY = "minute forecaster directional hit rate on "
_CRYPTO008_IMM = ("date", "instrument", "horizon_days", "question", "p", "check_date")
# the 42 rows filed before CRYPTO-008 (indices 0..41), pinned 2026-10-02: immutable fields of all 42; outcomes of the 40 already scored
_CRYPTO008_LEGACY_N = 42
_CRYPTO008_LEGACY_IMM_SHA = "4546b3783f023696fd08b3839eb406f2f0fc23b604c1839753da81c4208d0111"
_CRYPTO008_LEGACY_SCORED = tuple(range(40))
_CRYPTO008_LEGACY_SCORED_SHA = "2d05f61052dfe8f033f2d2227feda74fb4c415147b1902898b3f13c9b92fc389"


def _crypto008_book():
    """The flow ledger's rows, or None if it cannot be read (unreadable is reported, never assumed clean)."""
    try:
        with open(_CRYPTO008_BOOK, newline="") as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return None


def _crypto008_day(day):
    """(valid minutes, max high, min low) for a UTC day from its minute file, or None if there is no file. Written independently of
    range_question.py on purpose, so the check recomputes what the tool decided instead of echoing it."""
    p = f"{_CRYPTO008_MINUTES}/BTC-USD_{day}.csv"
    if not os.path.exists(p):
        return None
    n, hi, lo = 0, None, None
    with open(p, newline="") as fh:
        for r in csv.DictReader(fh):
            if not (r.get("minute_utc") or "").startswith(day):
                continue
            try:
                h, l = Decimal(r["high"]), Decimal(r["low"])
            except Exception:
                continue
            if not (h.is_finite() and l.is_finite()) or l <= 0 or h < l:
                continue
            n += 1
            hi = h if hi is None or h > hi else hi
            lo = l if lo is None or l < lo else lo
    return n, hi, lo


def _crypto008_tool():
    spec = importlib.util.spec_from_file_location("_crypto008_rq", _CRYPTO008_TOOL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _crypto008_mandate_declared():
    """CRYPTO-008. AGENT.md, the tool and the tape agree on the standing question, and the pre-declaration reproduces from the tape."""
    try:
        text = open(_CRYPTO008_AGENT, encoding="utf-8").read()
    except OSError:
        return False, "agent/AGENT.md is unreadable: the mandate cannot be verified"
    if "THE STANDING QUESTION (CRYPTO-008" not in text:
        return False, "AGENT.md has no 'THE STANDING QUESTION (CRYPTO-008' section: the flow agent is still on the retired question"
    try:
        rq = _crypto008_tool()
    except Exception as e:
        return False, f"range_question.py cannot be loaded ({type(e).__name__}: {e})"
    tmpl = rq.QUESTION.format(d="<D>", x="3.0")
    need = [tmpl, "X = 3.0, frozen", "1,300", "range_question.py resolve", "range_question.py reference", "range_question.py file",
            "THE RETIRED QUESTION", "(S8)"]
    missing = [t for t in need if t not in text]
    if missing:
        return False, "AGENT.md no longer states: " + "; ".join(missing)
    if rq.X_REGISTERED != (_CRYPTO008_X,) or rq.MIN_MINUTES != _CRYPTO008_MIN or rq.Q_RE.pattern != _CRYPTO008_Q:
        return False, (f"the tool and the registered question disagree: X_REGISTERED {rq.X_REGISTERED}, MIN_MINUTES {rq.MIN_MINUTES}, "
                       f"question pattern {'same' if rq.Q_RE.pattern == _CRYPTO008_Q else 'DIFFERENT'}")
    m = re.search(r"over the (\d+) eligible complete UTC days to\s+2026-10-01.*?exceeded 3\.0% on (\d+)", text, re.S)
    if not m:
        return False, "AGENT.md no longer carries the pre-declaration sentence (the eligible days and how many exceeded 3.0%)"
    n = k = 0
    for f in sorted(os.listdir(_CRYPTO008_MINUTES)):
        mm = re.match(r"BTC-USD_(\d{4}-\d{2}-\d{2})\.csv$", f)
        if not mm or not ("2026-08-22" <= mm.group(1) <= "2026-10-01"):
            continue
        st = _crypto008_day(mm.group(1))
        if st and st[0] >= _CRYPTO008_MIN:
            n += 1
            k += 1 if 100 * (st[1] - st[2]) > _CRYPTO008_X * st[2] else 0
    if (int(m.group(1)), int(m.group(2))) != (n, k):
        return False, f"AGENT.md declares {m.group(1)} eligible days / {m.group(2)} above 3.0%, the tape reproduces {n} / {k}"
    return True, (f"AGENT.md, range_question.py and the tape agree: the canonical question, X = 3.0 frozen, {_CRYPTO008_MIN} minutes, the run order, "
                  f"and the pre-declaration reproduces ({k} of {n} eligible UTC days to 2026-10-01 exceeded 3.0%, base {k / n:.3f})")


def _crypto008_rows_conform():
    """CRYPTO-008. Every row filed from 2026-10-02 is the one standing question, filed once per run and once per resolving day, S8-clean."""
    rows = _crypto008_book()
    if rows is None:
        return False, "agent/forecasts.csv is unreadable"
    bad, seen_day, seen_date, n = [], {}, {}, 0
    for i, r in enumerate(rows):
        q = (r.get("question") or "").strip()
        m = re.match(_CRYPTO008_Q, q)
        if i < _CRYPTO008_LEGACY_N:
            continue                                   # the pre-CRYPTO-008 rows are judged by crypto008_legacy_rows_immutable
        if not m:
            bad.append(f"row {i} ({r.get('date')}) is not the standing question: {q[:60]!r}")
            continue
        n += 1
        day, xs, filed = m.group(1), m.group(2), (r.get("date") or "")
        notes = r.get("notes") or ""
        if filed < _CRYPTO008_FIRST_DAY:
            bad.append(f"row {i}: a standing-question row dated {filed}, before the form existed")
        if Decimal(xs) != _CRYPTO008_X:
            bad.append(f"row {i}: asks {xs}%, the registered bar is {_CRYPTO008_X}%")
        if r.get("check_date") != day:
            bad.append(f"row {i}: check_date {r.get('check_date')} != target day {day}")
        try:
            gap = (dt.date.fromisoformat(day) - dt.date.fromisoformat(filed)).days
        except ValueError:
            bad.append(f"row {i}: unparseable date {filed!r} or target {day!r}")
            continue
        if gap < 1 or str(gap) != (r.get("horizon_days") or ""):
            bad.append(f"row {i}: horizon_days {r.get('horizon_days')!r} but target is {gap} day(s) after the filing date")
        st = re.search(r"Filed [^=]*= (\d{4}-\d{2}-\d{2})T\d{2}:\d{2}Z", notes)
        if not st:
            bad.append(f"row {i}: no filing stamp in the notes (the row was not filed by range_question.py)")
        elif day <= st.group(1):
            bad.append(f"row {i}: target {day} had begun at filing ({st.group(1)} UTC): S8")
        try:
            p = Decimal(r.get("p") or "")
            if not (Decimal(0) < p < Decimal(1)) or p.as_tuple().exponent < -3:
                bad.append(f"row {i}: p {r.get('p')!r} outside (0,1) or finer than 3 decimals")
        except Exception:
            bad.append(f"row {i}: p {r.get('p')!r} is not a number")
        low = notes.lower()
        for tok in ("[flow]", "[tech]", "[p_cal=", "resolves check_date+1 (standing, sched-001)"):
            if tok not in low:
                bad.append(f"row {i}: notes lack {tok}")
        if day in seen_day:
            bad.append(f"row {i}: target {day} already has row {seen_day[day]} (one row per resolving day)")
        if filed in seen_date:
            bad.append(f"row {i}: {filed} already has row {seen_date[filed]} (one row per run)")
        seen_day.setdefault(day, i)
        seen_date.setdefault(filed, i)
    if bad:
        return False, f"{len(bad)} problem(s): " + "; ".join(bad[:5])
    return True, f"{n} standing-question row(s) filed since {_CRYPTO008_FIRST_DAY}, all canonical, once per run and per resolving day" + ("" if n else " (none filed yet: the first is due at the next sweep)")


def _crypto008_resolutions_recompute():
    """CRYPTO-008. Every scored row was scored by the tool and its outcome equals an independent recomputation; void rows are thin or
    provably unrecorded; a due row left blank with its file present 3+ days on is red."""
    rows = _crypto008_book()
    if rows is None:
        return False, "agent/forecasts.csv is unreadable"
    today = dt.datetime.now(dt.timezone.utc).date()
    have = {f[8:18] for f in os.listdir(_CRYPTO008_MINUTES) if re.match(r"BTC-USD_\d{4}-\d{2}-\d{2}\.csv$", f)}
    bad, scored, void, wait = [], 0, 0, 0
    for i, r in enumerate(rows):
        m = re.match(_CRYPTO008_Q, (r.get("question") or "").strip())
        if not m or i < _CRYPTO008_LEGACY_N:
            continue
        day, out = m.group(1), (r.get("outcome") or "").strip()
        st = _crypto008_day(day)
        late = (today - dt.date.fromisoformat(day)).days
        if out in ("0", "1"):
            scored += 1
            if not re.search(r"RESOLVED \d{4}-\d{2}-\d{2} by range_question\.py", r.get("notes") or ""):
                bad.append(f"row {i}: scored without the tool's RESOLVED stamp (hand-edited?)")
            elif st is None or st[0] < _CRYPTO008_MIN:
                bad.append(f"row {i}: scored {out} but {day} has {'no file' if st is None else str(st[0]) + ' valid minutes'}")
            elif ("1" if 100 * (st[1] - st[2]) > Decimal(m.group(2)) * st[2] else "0") != out:
                bad.append(f"row {i}: recorded {out} but the minute file says {100 * (st[1] - st[2]) / st[2]:.3f}% vs {m.group(2)}%")
        elif out == "void":
            void += 1
            if not re.search(r"VOID \d{4}-\d{2}-\d{2} by range_question\.py", r.get("notes") or ""):
                bad.append(f"row {i}: void without the tool's VOID stamp (hand-edited?)")
            thin = st is not None and st[0] < _CRYPTO008_MIN
            unrecorded = st is None and any(d > day for d in have) and late >= 3
            if not (thin or unrecorded):
                bad.append(f"row {i}: void but {day} is neither thin (<{_CRYPTO008_MIN} minutes) nor provably unrecorded")
        elif out == "":
            wait += 1
            if late >= _CRYPTO008_GRACE_DAYS and st is not None:
                bad.append(f"row {i}: {day} ended {late} days ago and its minute file is present, but the row is unresolved (range_question.py resolve is not running)")
            elif late >= _CRYPTO008_GRACE_DAYS + 2 and st is None and any(d > day for d in have):
                bad.append(f"row {i}: {day} has no minute file {late} days on while later files exist: it should have voided")
        else:
            bad.append(f"row {i}: outcome {out!r} is none of 0 / 1 / void / blank")
    if bad:
        return False, f"{len(bad)} problem(s): " + "; ".join(bad[:4])
    return True, f"standing-question rows: {scored} scored (each recomputed from its minute file), {void} void (each justified), {wait} waiting within grace"


def _crypto008_legacy_rows_immutable():
    """CRYPTO-008 + BENCH-002. The 42 rows filed before the re-aim keep their immutable fields and the 40 outcomes already scored; the two
    still-pending rows may be scored once, by the retired question's own rule, and nothing else about any of them may change."""
    rows = _crypto008_book()
    if rows is None:
        return False, "agent/forecasts.csv is unreadable"
    if len(rows) < _CRYPTO008_LEGACY_N:
        return False, f"the book has {len(rows)} rows, fewer than the {_CRYPTO008_LEGACY_N} filed before CRYPTO-008: rows were deleted"
    h = hashlib.sha256()
    for r in rows[:_CRYPTO008_LEGACY_N]:
        h.update(("\x1f".join(r[k] for k in _CRYPTO008_IMM) + "\x1e").encode("utf-8"))
    h2 = hashlib.sha256()
    for i in _CRYPTO008_LEGACY_SCORED:
        h2.update(f"{i}:{rows[i]['outcome']}\x1e".encode())
    bad = []
    if h.hexdigest() != _CRYPTO008_LEGACY_IMM_SHA:
        bad.append("an immutable field (date, instrument, horizon_days, question, p, check_date) of a pre-CRYPTO-008 row changed")
    if h2.hexdigest() != _CRYPTO008_LEGACY_SCORED_SHA:
        bad.append("an outcome already scored on 2026-10-02 changed (BENCH-002)")
    if bad:
        return False, "; ".join(bad)
    open_ = [i for i in range(40, _CRYPTO008_LEGACY_N) if not (rows[i]["outcome"] or "").strip()]
    return True, (f"the {_CRYPTO008_LEGACY_N} pre-CRYPTO-008 rows are byte-stable in their immutable fields and the 40 scored outcomes; "
                  f"{len(open_)} of the 2 retired-question rows still open")


def _crypto008_executed():
    """CRYPTO-008 as a whole: the mandate is declared and reproducible, the old rows are untouched, every row filed since conforms."""
    legs = [("mandate", _crypto008_mandate_declared), ("legacy", _crypto008_legacy_rows_immutable), ("rows", _crypto008_rows_conform)]
    fails, oks = [], []
    for name, fn in legs:
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"raised {type(e).__name__}: {e}"
        (oks if ok else fails).append(f"{name}: {msg}")
    if fails:
        return False, " | ".join(fails)
    return True, "CRYPTO-008 executed: " + " | ".join(oks)


def _crypto008_controls():
    """Negative controls on COPIES in a temp dir (BOOK-001: a scratch book, never a shared one): each bad book must turn the right leg red."""
    global _CRYPTO008_BOOK
    real, results = _CRYPTO008_BOOK, []
    tmp = tempfile.mkdtemp()
    try:
        rq = _crypto008_tool()
        with open(real, newline="") as fh:
            rows = list(csv.DictReader(fh))
        cols = list(rows[0].keys())

        made = []

        def book(extra=None, mutate=None):
            rr = [dict(r) for r in rows]
            if mutate:
                mutate(rr)
            rr += extra or []
            p = os.path.join(tmp, f"forecasts_{len(made)}.csv")        # one scratch file per case: the case list is built up front
            made.append(p)
            with open(p, "w", newline="") as fh:                  # temp-dir scratch copy, never a shared book (BOOK-001)
                w = csv.DictWriter(fh, fieldnames=cols)
                w.writeheader()
                w.writerows(rr)
            return p

        def good(day, filed, outcome="", notes=None):
            return {"date": filed, "instrument": "BTC", "horizon_days": str((dt.date.fromisoformat(day) - dt.date.fromisoformat(filed)).days),
                    "question": rq.QUESTION.format(d=day, x="3.0"), "p": "0.43", "check_date": day, "outcome": outcome,
                    "notes": notes or (f"[flow] [tech] [p_cal=0.43] Resolves check_date+1 (standing, SCHED-001) Filed {filed} 08:30 PDT = {filed}T15:30Z "
                                       f"by range_question.py")}

        cases = [
            ("untouched copy", book(), "legacy_rows_immutable", True),
            ("a standing row filed correctly", book([good("2026-10-06", "2026-10-05")]), "rows_conform", True),
            ("a paraphrased question filed after CRYPTO-008", book([dict(good("2026-10-06", "2026-10-05"), question="BTC range tomorrow above 3%")]), "rows_conform", False),
            ("X moved to 3.5", book([dict(good("2026-10-06", "2026-10-05"), question=rq.QUESTION.format(d="2026-10-06", x="3.5"))]), "rows_conform", False),
            ("target day already begun at filing", book([good("2026-10-05", "2026-10-05",
                                                             notes="[flow] [tech] [p_cal=0.4] Resolves check_date+1 (standing, SCHED-001) Filed 2026-10-05 08:30 PDT = 2026-10-05T15:30Z")]), "rows_conform", False),
            ("two rows for one target day", book([good("2026-10-06", "2026-10-04"), good("2026-10-06", "2026-10-05")]), "rows_conform", False),
            ("an old outcome flipped", book(mutate=lambda rr: rr[3].update(outcome="1" if rr[3]["outcome"] == "0" else "0")), "legacy_rows_immutable", False),
            ("an old question reworded", book(mutate=lambda rr: rr[5].update(question=rr[5]["question"] + " ")), "legacy_rows_immutable", False),
            ("a due row left blank beside its file", book([good("2026-09-20", "2026-09-19")]), "resolutions_recompute", False),
            ("a hand-resolved row (no tool stamp)", book([good("2026-09-20", "2026-09-19", outcome="0")]), "resolutions_recompute", False),
        ]
        fns = {"legacy_rows_immutable": _crypto008_legacy_rows_immutable, "rows_conform": _crypto008_rows_conform,
               "resolutions_recompute": _crypto008_resolutions_recompute}
        for name, path, leg, want_ok in cases:
            _CRYPTO008_BOOK = path
            ok, msg = fns[leg]()
            results.append((name, leg, want_ok, ok, msg))
    finally:
        _CRYPTO008_BOOK = real
        shutil.rmtree(tmp, ignore_errors=True)
    return results


def _crypto008_run_all():
    ok_all = True
    for name, fn in (("crypto008_mandate_declared", _crypto008_mandate_declared), ("crypto008_legacy_rows_immutable", _crypto008_legacy_rows_immutable),
                     ("crypto008_rows_conform", _crypto008_rows_conform), ("crypto008_resolutions_recompute", _crypto008_resolutions_recompute),
                     ("crypto008_executed", _crypto008_executed)):
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"raised {type(e).__name__}: {e}"
        ok_all &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}\n      {msg}")
    return ok_all


if __name__ == "__main__":
    if "--controls" in sys.argv:
        bad = 0
        for name, leg, want_ok, ok, msg in _crypto008_controls():
            right = (ok == want_ok)
            bad += 0 if right else 1
            print(f"{'as expected' if right else 'WRONG'}  {name}: {leg} -> {'PASS' if ok else 'FAIL'}" + ("" if ok else f"  ({msg[:110]})"))
        sys.exit(1 if bad else 0)
    sys.exit(0 if _crypto008_run_all() else 1)
