"""PROPOSED resolver changes for CRYPTO-006 — handed to the session that owns council/resolver.py. NOT wired.

Ruled by Anupam ('go ahead', 2026-10-02 10:24 PT), adopting the recommended option (a) STOP: the two crypto direction
forecasters (com.anupam.crypto-minute, com.anupam.crypto-horizons) are turned off, every book and score is kept exactly as
recorded, the question is marked answered (no skill), and the order-flow recorder (com.anupam.crypto-collector) and the paper
crypto desk (com.anupam.crypto-desk) keep running. Executed 2026-10-02: crypto-minute at 12:11:20 PT, crypto-horizons at 12:17:53 PT (see ~/crypto-microstructure/README.md).

resolver.py and issues.json were NOT edited. This file holds everything the owner of resolver.py has to paste:

  1. TWO REPLACEMENTS for checks that go RED only because the three forecast books stop growing. Both are closed register rows
     whose checks keep running as regression guards, so a red would REOPEN them:
       - check_unwatched_books_sane (CHK-026): forecasts_5m.csv / forecasts_15m.csv newest row <= 3 days. First red: the first
         run on or after 2026-10-06 (the newest row is dated 2026-10-02).
       - check_no_lab_flat_across_history (FCST-004): a lab is FLAT when its first and last snapshot in the 6-day window of
         ~/.claude/forecast_counts.json carry the same resolved count; crypto-1min/5min/15min freeze, so the first red is about
         2026-10-08 or 10-09 (the first snapshot day on which the 6-day window holds only post-stop snapshots).
     Each replacement is the ORIGINAL function text plus marked CRYPTO-006 lines (diff it against resolver.py). The exemption
     hangs on _crypto006_stopped(), so it lives only while the stop REALLY holds (both jobs unloaded, both plists under
     ~/Library/LaunchAgents/retired/): restore the jobs and the age and growth tests apply again. Every integrity rule of
     CHK-026 still runs on the two frozen books, and funnel_log / ofi_history keep their freshness limits.
  2. NEW CHECKS, all read-only, every name carries the _crypto006_ prefix. Suggested registry lines:

         "crypto006_jobs_stay_unloaded": _crypto006_jobs_stay_unloaded,
         "crypto006_plists_retired": _crypto006_plists_retired,
         "crypto006_books_frozen": _crypto006_books_frozen,
         "crypto006_recorder_and_desk_kept": _crypto006_recorder_and_desk_kept,
         "crypto006_executed": _crypto006_executed,        # attach to CRYPTO-006's `check` field; ANDs jobs, plists, books and the launchd half of 'kept'

     and re-point the existing keys "unwatched_books_sane" and "no_lab_flat_across_history" at the replacements below.
  Paste the _CRYPTO006_ constants and helpers above the functions that use them; the two replacements go over the originals.

  CHK-001 (a check no register row names never runs): register a MONITOR row for crypto006_jobs_stay_unloaded and
  crypto006_books_frozen (suggested id CRYPTO-007, type monitor, lab crypto-microstructure, check crypto006_executed once wired) as
  well as closing CRYPTO-006 with it. INTEGRATE BEFORE Tue 2026-10-06 15:30 PT (the Resolver's first run that would turn CHK-026 red
  and reopen it); until then the replacements and the pins are only proposed and the books are frozen by the stop, not by a check.
  The exemptions never cover crypto-microstructure (the flow agent's own forecasts.csv) and read their label set from
  ~/bin/score_forecasts.py RETIRED, capped at the three labels CRYPTO-006 names. Negative controls (a changed pin, a plist put back,
  a job reloaded) must be run on COPIES, never on the real frozen books; --simulate only reads.

  Left alone on purpose: check_labs_still_forecasting and the rest of the flow agent's own forecasts.csv. Its standing daily
  forecast is about the stopped minute forecaster and can no longer resolve for a new day: whether to retire or re-aim it is
  Anupam's ruling (agent/AGENT.md is a mandate), not a check to loosen. The CRYP-007 scoreboard check and CAL-003 stay green on
  frozen books (verified live), so they need no change.

Run live:        /opt/anaconda3/bin/python PROPOSED_resolver_changes_CRYPTO-006.py
Show old vs new: /opt/anaconda3/bin/python PROPOSED_resolver_changes_CRYPTO-006.py --simulate     (reads resolver.py, writes nothing)
"""
import csv
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

HOME = os.path.expanduser("~")

# ── constants (built from expanduser, not from HOME, so a test that re-points HOME cannot re-point the launchd paths) ─────────
_CRYPTO006_LABELS = ("com.anupam.crypto-minute", "com.anupam.crypto-horizons")        # stopped
_CRYPTO006_KEPT = ("com.anupam.crypto-collector", "com.anupam.crypto-desk")             # must keep running
_CRYPTO006_LA = os.path.expanduser("~/Library/LaunchAgents")
_CRYPTO006_RETIRED_DIR = _CRYPTO006_LA + "/retired"
_CRYPTO006_LAB = os.path.expanduser("~/crypto-microstructure")
_CRYPTO006_SCRIPTS = ("minute_forecaster.py", "horizon_forecaster.py")
_CRYPTO006_BOOK_LABEL = {"forecasts_5m.csv": "crypto-5min", "forecasts_15m.csv": "crypto-15min"}   # the two books CHK-026 watched
_CRYPTO006_SCORER_LABELS = ("crypto-1min", "crypto-5min", "crypto-15min")               # the ONLY labels an exemption may ever cover
_CRYPTO006_SCORER_PATH = os.path.expanduser("~/bin/score_forecasts.py")                 # its RETIRED dict is the single source of truth
# sha256 + bytes of the books, state files and plists at the stop, taken AFTER both jobs were dead (paths relative to agent/)
_CRYPTO006_PINS = {
    "forecasts_15m.csv": [
        "2d5b04632bbc35d3aa6368c1f76c99d6804bec466175435e4d4f19835287d605",
        9476280
    ],
    "forecasts_5m.csv": [
        "5dd85b0b12272336d3823b605fd287c7fde0f883bf9ffff9563ce03b0536890c",
        9436742
    ],
    "minute_forecasts.csv": [
        "4878c4a97d389707181b51d7d52f18f6dbaf57d05bcbcfc80d581c1f758a695a",
        11321970
    ],
    "minute_state.json": [
        "46c6958c63d8c6d632b51410187aac37c572330aec53e54329ae531330e5d9f4",
        142
    ],
    "state_15m.json": [
        "3e17978ce1aca2bdc8a8eae38714ca88ea1858ceabf4f6ad06cdb0276ef552d2",
        141
    ],
    "state_5m.json": [
        "25b318bf16f9ba3123151a8983ceb4263bfb52418ce919de88bd0428ab9d3c49",
        139
    ]
}
_CRYPTO006_PLIST_PINS = {
    "com.anupam.crypto-horizons": [
        "9c7410b8618c3efe0e7de5a2ab2e68738922d69c395955e7d15bac03d35cb495",
        649
    ],
    "com.anupam.crypto-minute": [
        "cad366ed6b58019304827635cdb8efd1271f4d5edb22b8a8fd3097033d75c406",
        641
    ]
}
_CRYPTO006_STOP_SNAPSHOT = "crypto-minute at 12:11:20 PT, crypto-horizons at 12:17:53 PT"


def _crypto006_sha256(path):
    import hashlib      # local: this block is pasted into resolver.py, which may not import it at module level
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _crypto006_loaded():
    """{label: pid-or-'-'} for every job in `launchctl list`, or None when launchctl cannot be read. Unreadable is reported as
    unreadable, never as 'not loaded': a guard that guesses one way is the estate's commonest failure."""
    import subprocess   # local, as above
    try:
        p = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=20)
    except Exception:
        return None
    if p.returncode != 0:
        return None
    out = {}
    for line in p.stdout.splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) == 3:
            out[parts[2].strip()] = parts[0].strip()
    return out


def _crypto006_forecaster_procs():
    """Command lines of running python processes whose script is one of the two stopped forecasters; None if ps cannot be read."""
    import subprocess   # local, as above
    try:
        p = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True, timeout=20)
    except Exception:
        return None
    if p.returncode != 0:
        return None
    me, hits = str(os.getpid()), []
    for line in p.stdout.splitlines():
        pid, _, cmd = line.strip().partition(" ")
        toks = cmd.split()
        if pid == me or not toks or not os.path.basename(toks[0]).startswith("python"):
            continue
        if any(os.path.basename(t) in _CRYPTO006_SCRIPTS for t in toks[1:]):
            hits.append(f"{pid} {cmd[:120]}")
    return hits


def _crypto006_jobs_stay_unloaded():
    """CRYPTO-006. Neither forecaster job is loaded and no forecaster process runs. Red the moment anyone (a session, a
    liveness 'fix', a restore script) brings one back: the ruling stopped them and only Anupam can start them again."""
    loaded = _crypto006_loaded()
    if loaded is None:
        return False, "launchctl list could not be read: cannot say the two forecasters are unloaded (unreadable, not assumed stopped)"
    back = [f"{lab} (pid {loaded[lab]})" for lab in _CRYPTO006_LABELS if lab in loaded]
    if back:
        return False, "the CRYPTO-006 stop was undone: loaded again: " + ", ".join(back)
    procs = _crypto006_forecaster_procs()
    if procs is None:
        return False, "ps could not be read: cannot say no forecaster process is running (unreadable, not assumed stopped)"
    if procs:
        return False, "a forecaster process is running although both jobs are unloaded: " + "; ".join(procs[:2])
    return True, "com.anupam.crypto-minute and com.anupam.crypto-horizons are not loaded and no minute_forecaster.py / horizon_forecaster.py process is running"


def _crypto006_plists_retired():
    """CRYPTO-006. Each plist sits under ~/Library/LaunchAgents/retired/ with the exact bytes pinned at the stop (so the README's
    restore commands restore what was stopped) and is NOT directly under ~/Library/LaunchAgents/ (it would load at the next login)."""
    bad = []
    for lab in _CRYPTO006_LABELS:
        top, kept = f"{_CRYPTO006_LA}/{lab}.plist", f"{_CRYPTO006_RETIRED_DIR}/{lab}.plist"
        if os.path.exists(top):
            bad.append(f"{lab}.plist is back in LaunchAgents/ and would load at the next login")
        if not os.path.exists(kept):
            bad.append(f"retired/{lab}.plist is missing: the restore commands have nothing to restore")
            continue
        want = _CRYPTO006_PLIST_PINS.get(lab)
        if not want:
            bad.append(f"retired/{lab}.plist has no pinned sha256 in this check")
        elif _crypto006_sha256(kept) != want[0]:
            bad.append(f"retired/{lab}.plist changed since the stop (sha256 {_crypto006_sha256(kept)[:12]} != pinned {want[0][:12]})")
    if bad:
        return False, "; ".join(bad)
    return True, "both plists are under LaunchAgents/retired/ with their pinned bytes and neither is directly in LaunchAgents/"


def _crypto006_books_frozen():
    """CRYPTO-006 (BENCH-002: every book and score kept exactly as recorded). The three forecast books and their three state
    files are byte-identical to the stop snapshot. Red on any append, edit, re-score, void, truncation or deletion."""
    if not _CRYPTO006_PINS:
        return False, "no sha256 pins are loaded in this check: the stop snapshot cannot be verified"
    bad, n = [], 0
    for name, (want, size) in sorted(_CRYPTO006_PINS.items()):
        p = f"{_CRYPTO006_LAB}/agent/{name}"
        if not os.path.exists(p):
            bad.append(f"{name} is missing")
            continue
        n += 1
        got = _crypto006_sha256(p)
        if got != want:
            bad.append(f"{name} differs from the stop snapshot ({os.path.getsize(p):,} bytes now, {size:,} pinned; sha256 {got[:12]} != {want[:12]})")
    if bad:
        return False, "; ".join(bad)
    return True, f"{n} forecast books / state files are byte-identical to the 2026-10-02 stop snapshot ({_CRYPTO006_STOP_SNAPSHOT})"


def _crypto006_tape_last_trade_utc():
    """The newest recorded trade's OWN timestamp from today's tape file (local-day name first, UTC-day name as the fallback, as
    the collector and the forecasters both named it), or None. Freshness is the data's stamp, never the file's mtime."""
    names = [f"BTC-USD_{dt.datetime.now():%Y-%m-%d}.csv", f"BTC-USD_{dt.datetime.now(dt.timezone.utc):%Y-%m-%d}.csv"]
    for nm in names:
        p = f"{_CRYPTO006_LAB}/research/data/{nm}"
        if not os.path.exists(p):
            continue
        with open(p, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            fh.seek(max(0, fh.tell() - 262144))
            tail = fh.read().decode("utf-8", "replace").splitlines()
        for line in reversed(tail):
            parts = line.split(",")
            # a complete trade row only: 7 fields and a 13-digit epoch-ms stamp (the last line of a live file can be cut mid-write)
            if len(parts) >= 5 and parts[0] == "trade" and parts[1].isdigit() and len(parts[1]) == 13:
                return dt.datetime.fromtimestamp(int(parts[1]) / 1000, dt.timezone.utc)
    return None


def _crypto006_recorder_and_desk_kept(fresh=True):
    """CRYPTO-006: the ruling keeps the order-flow recorder and the paper crypto desk running. Both are loaded and the recorder has a
    process; with fresh=True (the registry form) the tape's last trade is also under 10 minutes old by its own timestamp and the
    desk's newest heartbeat tick under 20 minutes old with its last trade within 10 minutes of the tick (the same bars as
    crypto_desk_heartbeat_fresh / _tape_is_live). _crypto006_executed calls it with fresh=False: an asleep Mac must not reopen a
    closed decision row, and the existing desk checks already watch the data stamps."""
    loaded = _crypto006_loaded()
    if loaded is None:
        return False, "launchctl list could not be read: cannot say the recorder and the desk are loaded"
    missing = [lab for lab in _CRYPTO006_KEPT if lab not in loaded]
    if missing:
        return False, "CRYPTO-006 kept these running and they are not loaded: " + ", ".join(missing)
    if not loaded["com.anupam.crypto-collector"].isdigit():
        return False, "com.anupam.crypto-collector is loaded but has no process (a KeepAlive job that is not running)"
    if not fresh:
        return True, f"recorder pid {loaded['com.anupam.crypto-collector']} and the desk are loaded"
    now = dt.datetime.now(dt.timezone.utc)
    last = _crypto006_tape_last_trade_utc()
    if last is None:
        return False, "no recorded trade found in today's tape file: the recorder is not writing"
    tape_age = (now - last).total_seconds() / 60
    if tape_age > 10:
        return False, f"the tape's last trade is {tape_age:.0f} min old by its own timestamp ({last:%H:%M:%SZ}): the recorder is not receiving Coinbase"
    hb = f"{HOME}/crypto-desk/agent/heartbeat.csv"
    rows = list(csv.DictReader(open(hb))) if os.path.exists(hb) else []
    if not rows:
        return False, "crypto-desk/agent/heartbeat.csv is missing or empty"
    try:
        tick = dt.datetime.strptime(rows[-1]["tick_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        trade = dt.datetime.strptime(rows[-1]["last_trade_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except (KeyError, ValueError, TypeError):
        return False, f"unparseable desk heartbeat row: {rows[-1]}"
    hb_age = (now - tick).total_seconds() / 60
    if hb_age > 20:
        return False, f"the crypto desk's newest heartbeat is {hb_age:.0f} min old (launchd com.anupam.crypto-desk is not ticking)"
    if (tick - trade).total_seconds() > 600:
        return False, f"the desk's tick at {tick:%H:%M:%SZ} saw a tape whose last trade was {trade:%H:%M:%SZ}: the tape is stale at the desk"
    return True, (f"recorder pid {loaded['com.anupam.crypto-collector']}, tape's last trade {last:%H:%M:%SZ} ({tape_age:.1f} min old); "
                  f"desk loaded, heartbeat tick {tick:%H:%M:%SZ} ({hb_age:.1f} min old), last trade within {(tick - trade).total_seconds():.0f}s of the tick")


def _crypto006_executed():
    """CRYPTO-006 as a whole: both forecasters stopped and retired, every book frozen as recorded, the recorder and the desk
    still loaded. Passes only when all four legs pass; the message names every failing leg."""
    legs = [("jobs", _crypto006_jobs_stay_unloaded), ("plists", _crypto006_plists_retired),
            ("books", _crypto006_books_frozen), ("kept", lambda: _crypto006_recorder_and_desk_kept(fresh=False))]
    fails, oks = [], []
    for name, fn in legs:
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"raised {type(e).__name__}: {e}"
        (oks if ok else fails).append(f"{name}: {msg}")
    if fails:
        return False, " | ".join(fails)
    return True, "CRYPTO-006 executed: " + " | ".join(oks)


def _crypto006_stopped():
    """True only while the stop REALLY holds: both jobs unloaded, both plists under retired/, and the books byte-identical to the stop
    snapshot (a book that is not the frozen history is not excused). The exemptions below hang on this, so an exemption cannot outlive
    its reason: restore the jobs, or touch a book, and the freshness / growth tests apply again."""
    return _crypto006_jobs_stay_unloaded()[0] and _crypto006_plists_retired()[0] and _crypto006_books_frozen()[0]


def _crypto006_exempt_labels():
    """The scorer labels a CRYPTO-006 exemption covers: what ~/bin/score_forecasts.py marks RETIRED (one source of truth, so the scorer
    and these checks cannot drift), intersected with the three labels the ruling names. crypto-microstructure, the flow agent's own
    forecasts.csv, is deliberately NOT here: it must keep being judged. Empty unless _crypto006_stopped(); a scorer that cannot be
    imported exempts nothing (red after the age limit, never a silent pass)."""
    if not _crypto006_stopped():
        return ()
    import importlib.util
    try:
        sp = importlib.util.spec_from_file_location("_crypto006_sf", _CRYPTO006_SCORER_PATH)
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        marked = set(getattr(m, "RETIRED", {}) or {})
    except Exception:
        return ()
    return tuple(lab for lab in _CRYPTO006_SCORER_LABELS if lab in marked)


# ── REPLACEMENT 1 of 2: resolver.py check_unwatched_books_sane (CHK-026) — the original text plus lines marked CRYPTO-006 ──
def check_unwatched_books_sane():
    """The four scored books nothing had ever read.

    COV-001 counted them for weeks: funnel_log.csv, ofi_history.csv, and the crypto
    5m/15m forecast books. A scored book with no check can stop being written, or
    start writing nonsense, and nothing on this desk would say a word — the ASIA-008
    failure mode applied to data instead of a scheduler.

    Deliberately falsifiable, not a coverage token. Each rule below can fail on real
    data: a book that stops updating, a forecast scored without the price that scored
    it, a probability outside [0,1], or a horizon column that disagrees with the file
    it lives in.

    CRYPTO-006 (Anupam 'go ahead', 2026-10-02 10:24 PT, option (a) STOP): forecasts_5m.csv and forecasts_15m.csv are frozen
    history once the forecasters are stopped, so the age limit is waived for exactly those two books, and ONLY while
    _crypto006_stopped() holds (both jobs unloaded, both plists under LaunchAgents/retired/, the books byte-identical to the
    stop snapshot) and score_forecasts.py marks their label RETIRED. Restore the jobs or touch a book and the age limit applies
    again. Every integrity rule below still runs on both books; funnel_log and ofi_history keep their limits.
    """
    import csv as _csv
    books = [
        (f"{HOME}/stock-radar/agent/funnel_log.csv", "date", 6),
        (f"{HOME}/crypto-microstructure/agent/ofi_history.csv", "date", 6),
        (f"{HOME}/crypto-microstructure/agent/forecasts_5m.csv", "made_at_utc", 3),
        (f"{HOME}/crypto-microstructure/agent/forecasts_15m.csv", "made_at_utc", 3),
    ]
    today = dt.date.today()
    bad = []
    exempt = []                          # CRYPTO-006
    exempt_labs = _crypto006_exempt_labels()   # CRYPTO-006: empty unless the stop really holds (jobs, plists, byte pins)
    for path, dcol, max_age_days in books:
        name = os.path.basename(path)
        if not os.path.exists(path):
            bad.append(f"{name} missing"); continue
        rows = list(_csv.DictReader(open(path)))
        if not rows:
            bad.append(f"{name} empty"); continue
        stamps = sorted((r.get(dcol) or "")[:10] for r in rows if (r.get(dcol) or "").strip())
        if not stamps:
            bad.append(f"{name} has no usable {dcol}"); continue
        try:
            age = (today - dt.date.fromisoformat(stamps[-1])).days
        except ValueError:
            bad.append(f"{name} newest {dcol} unparseable: {stamps[-1]!r}"); continue
        if age > max_age_days:
            if _CRYPTO006_BOOK_LABEL.get(name) in exempt_labs:      # CRYPTO-006 (a): frozen history, integrity rules below still apply
                exempt.append(f"{name} (newest row {stamps[-1]})")
            else:
                bad.append(f"{name} newest row is {age}d old (limit {max_age_days})")
        # forecast books carry their own integrity rules
        if "forecasts_" in name:
            want = name.split("forecasts_")[1].split("m.csv")[0]
            wrong_h = [r for r in rows if (r.get("horizon_min") or "").strip() != want]
            if wrong_h:
                bad.append(f"{name} holds {len(wrong_h)} row(s) with horizon_min != {want}")
            scored_no_px = [r for r in rows if (r.get("outcome") or "").strip()
                            and not (r.get("px_at_target") or "").strip()]
            if scored_no_px:
                bad.append(f"{name} has {len(scored_no_px)} row(s) scored with no target price")
            oob = []
            for r in rows:
                v = (r.get("p_up") or "").strip()
                if not v:
                    continue
                try:
                    if not 0.0 <= float(v) <= 1.0:
                        oob.append(v)
                except ValueError:
                    oob.append(v)
            if oob:
                bad.append(f"{name} has {len(oob)} p_up outside [0,1] (e.g. {oob[0]!r})")
    if bad:
        return False, "; ".join(bad)
    if exempt:                                                    # CRYPTO-006
        return True, ("all 4 previously-unwatched books internally consistent; funnel_log and ofi_history current; "
                      + ", ".join(exempt) + " retired by CRYPTO-006: frozen history, age limit waived, integrity rules still run")
    return True, ("all 4 previously-unwatched books current and internally consistent "
                  "(funnel_log, ofi_history, forecasts_5m, forecasts_15m)")


# ── REPLACEMENT 2 of 2: resolver.py check_no_lab_flat_across_history (FCST-004) — the original text plus lines marked CRYPTO-006 ──
def check_no_lab_flat_across_history():
    """FCST-004. A lab that resolves nothing must age in public, not print in a report.

    Registered 2026-08-31 from the caretaker's own build suggestion (report 2026-08-30):
    score_forecasts.py already detects NO GROWTH and prints it, and four labs carried
    that flag — but nothing turned the flag into an issue, so it stayed visible and
    unactioned. This is the abstention-drift failure mode that held the estate at 23
    predictions until August (the forecast-ledger finding); a printed warning nobody
    owns is how it survived.

    The snapshot history lives in ~/.claude/forecast_counts.json. A lab is FLAT when its
    resolved count is identical in its own first and last appearance across at least four
    snapshots. Labs missing from a partial sweep are not counted as flat — a lab the
    scorer did not read is unknown, not stalled, and calling it stalled would be the
    silent-zero sin this desk keeps convicting.

    CRYPTO-006 (Anupam 'go ahead', 2026-10-02 10:24 PT, option (a) STOP): crypto-1min, crypto-5min and crypto-15min are
    frozen history once the forecasters are stopped and are not expected to grow, so they are exempt from the FLAT test,
    and ONLY while _crypto006_stopped() holds and score_forecasts.py marks them RETIRED. Every other lab, crypto-microstructure
    included, is judged exactly as before.
    """
    p = f"{HOME}/.claude/forecast_counts.json"
    if not os.path.exists(p):
        return False, "forecast_counts.json missing — the growth flag has no history to read"
    try:
        snap = json.load(open(p))
    except Exception as e:
        return False, f"forecast_counts.json unreadable: {e}"
    hist = list(snap.get("history") or [])
    if snap.get("when") and snap["when"] not in [h.get("when") for h in hist]:
        hist.append({"when": snap["when"], "counts": snap.get("counts") or {}})
    if len(hist) < 4:
        return True, f"only {len(hist)} snapshot(s) on file — too short to call any lab flat"
    seen = {}
    for h in hist:
        for lab, n in (h.get("counts") or {}).items():
            seen.setdefault(lab, []).append((h.get("when"), n))
    flat = []
    exempt = []                          # CRYPTO-006
    exempt_labs = _crypto006_exempt_labels()   # CRYPTO-006: empty unless the stop really holds (jobs, plists, byte pins)
    for lab, pts in sorted(seen.items()):
        if len(pts) < 4:
            continue
        if lab in exempt_labs:     # CRYPTO-006 (a): retired, frozen history, not expected to grow
            exempt.append(lab)
            continue
        if pts[0][1] == pts[-1][1]:
            flat.append(f"{lab} flat at {pts[0][1]} across {len(pts)} snapshots "
                        f"({pts[0][0]} -> {pts[-1][0]})")
    if flat:
        return False, f"{len(flat)} lab(s) resolving nothing: " + "; ".join(flat)
    grew = [v for lab, v in seen.items() if len(v) >= 4 and lab not in exempt]      # CRYPTO-006
    return True, (f"every lab with {min((len(v) for v in grew), default=0)}+ snapshots "
                  f"grew its resolved count ({len(seen)} labs on file)"
                  + (f"; {', '.join(exempt)} retired by CRYPTO-006 and exempt" if exempt else ""))



def _crypto006_simulate():
    """Old vs new, read-only: loads resolver.py without running it, then (1) moves 'today' four days forward for CHK-026 and
    (2) feeds FCST-004 a synthetic six-day snapshot history in which the three crypto counts stopped growing."""
    import importlib.util
    import tempfile
    import types
    spec = importlib.util.spec_from_file_location("_r_old", f"{HOME}/command-center/council/resolver.py")
    R = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(R)
    me = sys.modules[__name__]
    real = dt

    def shifted(days):
        class _D(real.date):
            @classmethod
            def today(cls):
                return real.date.today() + real.timedelta(days=days)
        ns = types.SimpleNamespace(**{k: getattr(real, k) for k in dir(real) if not k.startswith("_")})
        ns.date = _D
        return ns

    print(f"stop holds right now (_crypto006_stopped): {_crypto006_stopped()}")
    print("\nCHK-026 check_unwatched_books_sane, newest forecasts_5m/15m row dated "
          f"{max((r['made_at_utc'][:10] for r in csv.DictReader(open(_CRYPTO006_LAB + '/agent/forecasts_15m.csv'))), default='?')}")
    for days in (0, 3, 4):
        R.dt, me.dt = shifted(days), shifted(days)
        o, n = R.check_unwatched_books_sane(), me.check_unwatched_books_sane()
        R.dt, me.dt = real, real
        print(f"  today +{days}d  ORIGINAL {'PASS' if o[0] else 'FAIL'}  {o[1][:110]}\n"
              f"            REPLACEMENT {'PASS' if n[0] else 'FAIL'}  {n[1][:150]}")
    # FCST-004 on a synthetic history
    days = ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09", "2026-10-12"]
    hist = [{"when": d, "counts": {"crypto-1min": 56000, "crypto-5min": 46200, "crypto-15min": 45700, "asia-radar": 270 + 3 * i}}
            for i, d in enumerate(days)]
    snap = {"when": days[-1], "counts": hist[-1]["counts"], "history": hist}
    tmp = tempfile.mkdtemp()
    os.makedirs(tmp + "/.claude")
    # BOOK-001 does not apply: the simulator writes a scratch copy inside a temp directory, never a shared book
    json.dump(snap, open(tmp + "/.claude/forecast_counts.json", "w"))
    keep_r, keep_m = R.HOME, me.HOME
    R.HOME, me.HOME = tmp, tmp
    o, n = R.check_no_lab_flat_across_history(), me.check_no_lab_flat_across_history()
    R.HOME, me.HOME = keep_r, keep_m
    print("\nFCST-004 check_no_lab_flat_across_history on a synthetic 6-snapshot history (three crypto counts flat, asia growing)")
    print(f"  ORIGINAL    {'PASS' if o[0] else 'FAIL'}  {o[1][:200]}\n  REPLACEMENT {'PASS' if n[0] else 'FAIL'}  {n[1][:200]}")


def _crypto006_run_all():
    ok_all = True
    for name, fn in (("crypto006_jobs_stay_unloaded", _crypto006_jobs_stay_unloaded),
                     ("crypto006_plists_retired", _crypto006_plists_retired),
                     ("crypto006_books_frozen", _crypto006_books_frozen),
                     ("crypto006_recorder_and_desk_kept", _crypto006_recorder_and_desk_kept),
                     ("crypto006_executed", _crypto006_executed),
                     ("unwatched_books_sane (replacement)", check_unwatched_books_sane),
                     ("no_lab_flat_across_history (replacement)", check_no_lab_flat_across_history)):
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"raised {type(e).__name__}: {e}"
        ok_all &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}\n      {msg}")
    return ok_all


if __name__ == "__main__":
    import sys
    if "--simulate" in sys.argv:
        _crypto006_simulate()
    else:
        sys.exit(0 if _crypto006_run_all() else 1)
