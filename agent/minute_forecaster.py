#!/usr/bin/env python3
"""minute_forecaster.py — the 1-minute unit CRYP-002 ruled into existence.

Anupam, 2026-08-12: move the flow agent's falsifiable unit from a 1-DAY call to a
1-MINUTE one. The old unit asked this lab to forecast a horizon its own data
cannot speak to — it records sub-second order flow, and that information decays in
seconds. n=5 resolved at Brier skill -0.0588 with every thesis reading as a
deferral to the senior gate, which is what a horizon mismatch looks like.

THIS IS A CALIBRATION INSTRUMENT AND IS BARRED FROM TRADING.

    1-min direction edge   +1.38pp vs a base-rate-matched null, z = 5.21  (REAL)
    worth                  +0.05 bps per trade
    Coinbase retail taker  60 bps
    ratio                  about 1/1,183rd of the fee

The edge is real and survives Bonferroni over the four horizons swept. It is also
permanently smaller than the cost of acting on it. Never present this output as a
strategy, never size it, never let a good run read as tradeable. The ratio above is
printed on every run so it cannot quietly fall out of the story.

WHY IT IS WORTH RUNNING ANYWAY — with the authorising arithmetic CORRECTED.

CRYP-002 was ruled on "~1,440 scoreable predictions a day". Observed: 589 on
08-12 and 542 on 08-13. The shortfall is NOT gaps — while the process runs,
coverage is 99.0% with no gap over 3 minutes. It is that the job only runs about
9 hours of 24, because com.anupam.crypto-minute.plist is KeepAlive and the laptop
sleeps. That is the same sleep constraint the 0DTE cloud leg exists for, and I
should have priced it in rather than quoting the theoretical maximum.

The honest figure is ~550/day, not 1,440. The decision still holds — 550 is about
100x the unit it replaced, and the estate was ~25 resolved forecasts short — but
it holds on a number 2.6x smaller than the one that authorised it, and a decision
argued on an inflated figure deserves to have the real one written where the
claim was made.

Calibration is the product; the direction call is raw material.

HOW IT STAYS HONEST
  · A forecast is written BEFORE its minute elapses and is never edited afterwards.
    The scorer only ever fills `outcome` on a row whose target minute is complete.
  · The model is the SAME online SGD as research/backtest_all.py — same features,
    same LR/L2 — so the live record and the backtest measure one algorithm, not two.
    THIS BECAME TRUE ON 2026-08-20, and was false for the 9,645 rows before it.
    `features()` hard-coded `ofi` and `book_imb` to 0.0 while the backtest fed both
    from the recording, so the live instrument was a FOUR-feature model claiming
    six-feature parity, and its two microstructure inputs — the only reason a
    microstructure lab runs a minute unit at all — never left zero across eight
    days and 9,243 weight updates. `flow_features()` now derives both from the
    same recorded `trade`/`book` rows the closes come from, matching
    build_minute_series() to 4e-16 over a 61-minute cross-check.
  · Every row carries `fv` in its note: rows WITHOUT it are the four-feature era
    and are not comparable to rows with `fv: 2`. `book_live` records whether the
    book imbalance was measured inside the minute or forward-filled to zero.
    Scoring the two eras as one series would restate the instrument's own history,
    which is the thing this file exists not to do.
  · Ties (a minute closing exactly unchanged) are recorded as `tie` and excluded
    from direction scoring. That is CRYP-001's lesson: scoring ties as misses is
    what produced a 34% hit rate out of thin air.
  · If the collector is stale the run writes NOTHING and says so. A forecast made
    from an old book is not a forecast.

Run:  /opt/anaconda3/bin/python agent/minute_forecaster.py          # one tick
      /opt/anaconda3/bin/python agent/minute_forecaster.py --loop   # every 60s
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import time
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "research", "data")
BOOK = os.path.join(HERE, "minute_forecasts.csv")
STATE = os.path.join(HERE, "minute_state.json")

PRODUCT = "BTC-USD"
LR, L2 = 0.02, 0.001            # identical to research/backtest_all.py
OFI_WINDOW_S = 60               # identical to research/backtest_all.OFI_WINDOW_S
FEATS = ["bias", "r1", "r5", "rev", "ofi", "book_imb"]
STALE_SEC = 180                 # a book older than this is not a live book
# `up` is 1/0 for "the minute closed higher", which is what a calibration scorer
# needs — `outcome` records whether the CALL was right, which is a different
# question and cannot be paired with p. A tie leaves `up` blank rather than 0:
# a minute that did not move did not happen either way.
COLS = ["made_at_utc", "target_minute_utc", "product", "p_up", "px_at_call",
        "px_at_target", "up", "outcome", "note"]


def minute_closes(path, n=400):
    """(minute_iso, last_trade_px) for the most recent `n` complete minutes."""
    by_min = {}
    with open(path) as f:
        for row in csv.reader(f):
            if len(row) < 3 or row[0] != "trade":
                continue
            try:
                ts, px = int(row[1]), float(row[2])
            except ValueError:
                continue
            m = datetime.fromtimestamp(ts / 1000, timezone.utc).replace(
                second=0, microsecond=0)
            by_min[m] = px                      # last trade in the minute wins
    keys = sorted(by_min)
    return [(k, by_min[k]) for k in keys[-n:]]


def flow_features(path, minute):
    """(ofi, book_imb, live) at `minute`, derived exactly as
    research/backtest_all.build_minute_series does — so the live model and the
    backtest really are one algorithm.

      ofi       trailing-OFI_WINDOW_S-seconds signed/total trade volume, the
                window ENDING at the first second of `minute`. Matches the
                backtest's `ofi_sec.reindex(full * 60)`: strictly past data.
      book_imb  last top-20 book imbalance stamped inside `minute`, forward-filled
                from earlier minutes when the book went quiet (the backtest's
                `.groupby(min).last().ffill()`).

    `live` is False when no book row was ever seen, i.e. book_imb is a
    stand-in zero rather than a measurement. The caller records which it got.
    """
    m_start_s = int(minute.timestamp())
    m_start_ms, m_end_ms = m_start_s * 1000, (m_start_s + 60) * 1000
    lo_ms = (m_start_s - OFI_WINDOW_S + 1) * 1000   # rolling(60, min_periods=1)
    hi_ms = (m_start_s + 1) * 1000                  # inclusive of second m_start_s

    signed = total = 0.0
    book_imb, book_ts, seen_book = 0.0, -1, False
    with open(path) as fh:
        for row in csv.reader(fh):
            if len(row) < 3:
                continue
            try:
                ts = int(row[1])
            except ValueError:
                continue
            if row[0] == "trade":
                if lo_ms <= ts < hi_ms:
                    try:
                        qty, isbuy = float(row[3]), float(row[4])
                    except (IndexError, ValueError):
                        continue
                    signed += qty if isbuy > 0.5 else -qty
                    total += qty
            elif row[0] == "book" and ts < m_end_ms and ts > book_ts:
                try:
                    book_imb = float(row[6])
                except (IndexError, ValueError):
                    continue
                book_ts, seen_book = ts, True

    ofi = signed / total if total else 0.0
    return ofi, book_imb, seen_book


def features(closes, flow=(0.0, 0.0)):
    """Same six features as backtest_all.run_online_pass, in the same order."""
    c = [p for _, p in closes]
    if len(c) < 21:
        return None, None
    rets = [math.log(c[i] / c[i - 1]) for i in range(1, len(c))]
    win = rets[-60:] if len(rets) >= 60 else rets
    mu = sum(win) / len(win)
    sig = (sum((x - mu) ** 2 for x in win) / max(1, len(win) - 1)) ** 0.5 or 1e-6
    p = c[-1]
    r1 = max(-4, min(4, math.log(p / c[-2]) / sig))
    r5 = max(-4, min(4, math.log(p / c[-6]) / (sig * 5 ** 0.5)))
    ma = sum(c[-15:]) / 15
    rev = max(-4, min(4, math.log(ma / p) / (sig * 15 ** 0.5)))
    # Until 2026-08-20 these two rode at a hard 0.0 — the comment here said they
    # were "not reconstructible from minute closes alone", which was true and
    # beside the point: the recorder writes `book` and `trade` rows to the same
    # file these closes come from, so they ARE reconstructible from the recording.
    # 9,645 live rows were written with a four-feature model while the docstring
    # claimed six-feature parity with the backtest. `flow_features` closes that.
    ofi, book_imb = flow
    return [1.0, r1, r5, rev, ofi, book_imb], sig


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"w": [0.0] * len(FEATS), "n_updates": 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true", help="run every 60s until stopped")
    args = ap.parse_args()
    while True:
        tick()
        if not args.loop:
            return
        time.sleep(60)


def tick():
    # collector.py names its file with datetime.date.today() — the LOCAL date.
    # This looked for the UTC date, so between 17:00 PT and midnight (00:00-07:00
    # UTC) the two disagree, the file "did not exist", and the run reported
    # "collector down" while the collector was demonstrably alive. Seven hours a
    # day of silence from a timezone mismatch, on top of the laptop sleep that
    # CRYP-003 correctly identified. Local first, UTC as a fallback so a machine
    # set to UTC still works.
    cands = [datetime.now().strftime("%Y-%m-%d"),
             datetime.now(timezone.utc).strftime("%Y-%m-%d")]
    path = next((q for q in (os.path.join(DATA, f"{PRODUCT}_{d}.csv") for d in cands)
                 if os.path.exists(q)), None)
    if path is None:
        print(f"no recording for {cands[0]} (or {cands[1]} UTC) — collector down. "
              f"Nothing written.")
        return
    closes = minute_closes(path)
    if not closes:
        print("no trades parsed. Nothing written.")
        return
    last_min, last_px = closes[-1]
    age = (datetime.now(timezone.utc) - last_min).total_seconds()
    if age > STALE_SEC:
        print(f"book is {age:.0f}s old (> {STALE_SEC}s) — stale. Nothing written.")
        return

    rows = list(csv.DictReader(open(BOOK))) if os.path.exists(BOOK) else []
    px_by_min = {m.strftime("%Y-%m-%dT%H:%M"): p for m, p in closes}

    # ── score anything whose target minute is now complete ────────────────────
    st = load_state()
    scored = 0
    for r in rows:
        if (r.get("outcome") or "").strip():
            continue
        tgt = r["target_minute_utc"]
        if tgt not in px_by_min:
            continue                              # minute not complete yet
        px0, px1 = float(r["px_at_call"]), px_by_min[tgt]
        r["px_at_target"] = f"{px1:.2f}"
        if px1 == px0:
            r["outcome"] = "tie"                  # CRYP-001: never a miss
            r["up"] = ""
        else:
            up = px1 > px0
            r["up"] = "1" if up else "0"
            r["outcome"] = "right" if (float(r["p_up"]) > 0.5) == up else "wrong"
            # online SGD update, same rule as backtest_all
            f = json.loads(r["note"])["f"]
            z = float(r["p_up"]) * 2 - 1
            z_act = 1.0 if up else -1.0
            err = z - z_act
            st["w"] = [w * (1 - LR * L2) - LR * err * fi for w, fi in zip(st["w"], f)]
            st["n_updates"] += 1
        scored += 1

    # ── emit one forecast for the NEXT minute, before it exists ───────────────
    ofi, book_imb, book_live = flow_features(path, last_min)
    f, sig = features(closes, flow=(ofi, book_imb))
    wrote = 0
    if f is not None:
        z = max(-4.0, min(4.0, sum(w * fi for w, fi in zip(st["w"], f))))
        p_up = 1 / (1 + math.exp(-z))
        p_up = min(0.95, max(0.05, p_up))
        target = (last_min + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M")
        if not any(r["target_minute_utc"] == target for r in rows):
            rows.append({
                "made_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "target_minute_utc": target, "product": PRODUCT,
                "p_up": f"{p_up:.4f}", "px_at_call": f"{last_px:.2f}",
                "px_at_target": "", "up": "", "outcome": "",
                "note": json.dumps({"f": f, "sig": round(sig, 8),
                                    "fv": 2, "book_live": int(book_live)}),
            })
            wrote = 1

    with open(BOOK, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    json.dump(st, open(STATE, "w"), indent=1)

    done = [r for r in rows if r["outcome"] in ("right", "wrong")]
    ties = sum(1 for r in rows if r["outcome"] == "tie")
    print(f"{wrote} forecast written, {scored} scored · book {len(rows)} rows "
          f"({len(done)} scoreable, {ties} ties excluded)")

    # Report BY FEATURE ERA and never pooled. Rows without `fv` were written by
    # the four-feature model (ofi and book_imb hard zero); rows with fv:2 by the
    # six-feature one. Pooling them reports a hit rate for an algorithm that
    # never existed, and the fv:2 record would be buried under 9,645 rows of a
    # different model for months.
    eras = {}
    for r in done:
        try:
            fv = json.loads(r["note"]).get("fv", 1)
        except Exception:
            fv = 1
        eras.setdefault(fv, []).append(r)
    for fv in sorted(eras):
        g = eras[fv]
        hit = 100 * sum(1 for r in g if r["outcome"] == "right") / len(g)
        brier = sum((float(r["p_up"]) - (1.0 if r["outcome"] == "right" else 0.0)) ** 2
                    for r in g) / len(g)
        days = len({r["target_minute_utc"][:10] for r in g})
        tag = "4-feature (ofi/book pinned at 0)" if fv == 1 else "6-feature (live flow)"
        prov = " — PROVISIONAL" if days < 30 else ""
        print(f"  fv{fv} {tag}: hit {hit:.2f}%  Brier {brier:.4f}  "
              f"n={len(g)} over {days} day(s){prov}")
        if days < 30:
            print(f"       effective sample is nearer {days} than {len(g)}: minutes "
                  f"inside one session share a regime.")
    print("  NOT TRADEABLE: the 1-min edge is worth ~+0.05 bps against a 60 bps "
          "retail fee, about 1/1,183rd of cost.")


if __name__ == "__main__":
    main()
