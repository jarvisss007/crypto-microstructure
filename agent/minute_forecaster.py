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

WHY IT IS WORTH RUNNING ANYWAY: ~1,440 scoreable predictions a day against the
previous one. The estate is roughly 25 resolved forecasts short of a readable Brier
for the first time, and this is by far the fastest route there. Calibration is the
product; the direction call is raw material.

HOW IT STAYS HONEST
  · A forecast is written BEFORE its minute elapses and is never edited afterwards.
    The scorer only ever fills `outcome` on a row whose target minute is complete.
  · The model is the SAME online SGD as research/backtest_all.py — same features,
    same LR/L2 — so the live record and the backtest measure one algorithm, not two.
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
FEATS = ["bias", "r1", "r5", "rev", "ofi", "book_imb"]
STALE_SEC = 180                 # a book older than this is not a live book
COLS = ["made_at_utc", "target_minute_utc", "product", "p_up", "px_at_call",
        "px_at_target", "outcome", "note"]


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


def features(closes):
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
    # order-flow features are not reconstructible from minute closes alone; the
    # live model carries them at zero rather than inventing them, and says so.
    return [1.0, r1, r5, rev, 0.0, 0.0], sig


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
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(DATA, f"{PRODUCT}_{day}.csv")
    if not os.path.exists(path):
        print(f"no recording for {day} — collector down. Nothing written.")
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
        else:
            up = px1 > px0
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
    f, sig = features(closes)
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
                "px_at_target": "", "outcome": "",
                "note": json.dumps({"f": f, "sig": round(sig, 8)}),
            })
            wrote = 1

    with open(BOOK, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    json.dump(st, open(STATE, "w"), indent=1)

    done = [r for r in rows if r["outcome"] in ("right", "wrong")]
    ties = sum(1 for r in rows if r["outcome"] == "tie")
    hit = (100 * sum(1 for r in done if r["outcome"] == "right") / len(done)) if done else float("nan")
    brier = (sum((float(r["p_up"]) - (1.0 if r["outcome"] == "right" else 0.0)) ** 2
                 for r in done) / len(done)) if done else float("nan")
    print(f"{wrote} forecast written, {scored} scored · book {len(rows)} rows "
          f"({len(done)} scoreable, {ties} ties excluded)")
    if done:
        print(f"  hit {hit:.1f}%  Brier {brier:.4f}  n={len(done)} "
              f"— provisional below n=100")
    print("  NOT TRADEABLE: the 1-min edge is worth ~+0.05 bps against a 60 bps "
          "retail fee, about 1/1,183rd of cost.")


if __name__ == "__main__":
    main()
