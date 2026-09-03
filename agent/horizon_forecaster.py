#!/usr/bin/env python3
"""horizon_forecaster.py — the 5- and 15-minute rungs of the minute instrument.

Anupam, 2026-08-21: "I wanted to build a crypto where it gives a fifteen-minute
prediction. After fifteen minutes, this will be the price, and it doesn't change.
For one minute, five minutes and fifteen minutes — and test its prediction level.
If it takes a trade at 8:00 and the prediction for 8:15 was obeyed, it's a win."

That instrument already existed at ONE minute (minute_forecaster.py, 10k rows) and
at fifteen minutes only inside a browser page whose scoreboard lives in
localStorage, where the desk's resolver cannot audit it. This file puts the 5- and
15-minute rungs on disk, under the same rules as the 1-minute one, so the three
horizons are ONE instrument with three clocks and one scoreboard (scoreboard.py).

THIS IS A CALIBRATION INSTRUMENT AND IS BARRED FROM TRADING. The lab's published
result (research/NULL_RESULT.md) is that short-horizon direction is not
forecastable from these features, and the only real edge found (1 minute) is worth
about 1/1,183rd of the retail fee. Nothing here changes that; it measures it.

SAME INSTRUMENT, DIFFERENT CLOCK — what is deliberately identical to the 1-minute file:
  · the six features, the online SGD, LR/L2, the clamp to [0.05, 0.95]
  · a forecast is written BEFORE its target minute and is NEVER edited; the scorer
    fills `outcome` only on a row whose target minute is complete
  · a minute that closes exactly unchanged is a `tie`, excluded from direction
    scoring (CRYP-001: scoring ties as misses manufactures a bad hit rate)
  · a stale book (collector older than STALE_SEC) writes NOTHING and says so
The win rule, stated plainly: at time T the row says p_up for the price at T+H.
At T+H the real last trade of that minute is read. Direction obeyed = right.

Files: agent/forecasts_5m.csv, agent/forecasts_15m.csv (+ state_5m.json, state_15m.json).
Run:  /opt/anaconda3/bin/python agent/horizon_forecaster.py          # one tick
      /opt/anaconda3/bin/python agent/horizon_forecaster.py --loop   # every 60s
"""
from __future__ import annotations

import argparse, csv, json, math, os, time
import sys as _s; _s.path.insert(0, "/Users/anupampatil/command-center"); from calibrate import calibrate as _cal  # CAL-001 consumer
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "research", "data")
PRODUCT = "BTC-USD"
HORIZONS = (5, 15)              # minutes; the 1-minute rung is minute_forecaster.py
LR, L2 = 0.02, 0.001            # identical to research/backtest_all.py and the 1-min rung
FEATS = ["bias", "r1", "r5", "rev", "ofi", "book_imb"]
STALE_SEC = 180
COLS = ["made_at_utc", "target_minute_utc", "horizon_min", "product", "p_up", "p_cal", "pred_px",
        "px_at_call", "px_at_target", "up", "outcome", "note"]


def book_path(h):  return os.path.join(HERE, f"forecasts_{h}m.csv")
def state_path(h): return os.path.join(HERE, f"state_{h}m.json")


def minute_closes(path, n=400):
    by_min = {}
    with open(path) as f:
        for row in csv.reader(f):
            if len(row) < 3 or row[0] != "trade":
                continue
            try:
                ts, px = int(row[1]), float(row[2])
            except ValueError:
                continue
            m = datetime.fromtimestamp(ts / 1000, timezone.utc).replace(second=0, microsecond=0)
            by_min[m] = px
    keys = sorted(by_min)
    return [(k, by_min[k]) for k in keys[-n:]]


def features(closes):
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
    return [1.0, r1, r5, rev, 0.0, 0.0], sig


def load_state(h):
    p = state_path(h)
    return json.load(open(p)) if os.path.exists(p) else {"w": [0.0] * len(FEATS), "n_updates": 0}


def tick_horizon(h, closes, last_min, last_px, px_by_min):
    book = book_path(h)
    rows = list(csv.DictReader(open(book))) if os.path.exists(book) else []
    st = load_state(h)
    scored = 0
    for r in rows:
        if (r.get("outcome") or "").strip():
            continue
        tgt = r["target_minute_utc"]
        if tgt not in px_by_min:
            continue
        px0, px1 = float(r["px_at_call"]), px_by_min[tgt]
        r["px_at_target"] = f"{px1:.2f}"
        if px1 == px0:
            r["outcome"], r["up"] = "tie", ""
        else:
            up = px1 > px0
            r["up"] = "1" if up else "0"
            r["outcome"] = "right" if (float(r["p_up"]) > 0.5) == up else "wrong"
            f = json.loads(r["note"])["f"]
            err = (float(r["p_up"]) * 2 - 1) - (1.0 if up else -1.0)
            st["w"] = [w * (1 - LR * L2) - LR * err * fi for w, fi in zip(st["w"], f)]
            st["n_updates"] += 1
        scored += 1

    f, sig = features(closes)
    wrote = 0
    if f is not None:
        z = max(-4.0, min(4.0, sum(w * fi for w, fi in zip(st["w"], f))))
        p_up = min(0.95, max(0.05, 1 / (1 + math.exp(-z))))
        target = (last_min + timedelta(minutes=h)).strftime("%Y-%m-%dT%H:%M")
        if not any(r["target_minute_utc"] == target for r in rows):
            # pred_px — same frozen definition as the 1-minute book (2026-08-31), scaled
            # by sqrt(horizon) so the point forecast carries the model's own volatility
            # estimate at THIS horizon. His literal ask lives here: "at 9:00 it says the
            # 9:15 price"; the study judges it against the random walk at :00 exactly.
            pred_px = last_px * (1 + math.tanh(z) * sig * math.sqrt(h))
            rows.append({
                "made_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "target_minute_utc": target, "horizon_min": str(h), "product": PRODUCT,
                "p_up": f"{p_up:.4f}", "p_cal": f"{_cal('crypto-microstructure', p_up):.4f}", "pred_px": f"{pred_px:.2f}",
                "px_at_call": f"{last_px:.2f}",
                "px_at_target": "", "up": "", "outcome": "",
                "note": json.dumps({"f": f, "sig": round(sig, 8)}),
            })
            wrote = 1
    with open(book, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    json.dump(st, open(state_path(h), "w"), indent=1)
    done = [r for r in rows if r["outcome"] in ("right", "wrong")]
    hit = (100 * sum(1 for r in done if r["outcome"] == "right") / len(done)) if done else float("nan")
    print(f"  +{h:>2}m: {wrote} written, {scored} scored · {len(rows)} rows, {len(done)} scoreable"
          + (f", hit {hit:.1f}%" if done else ""))


def tick():
    cands = [datetime.now().strftime("%Y-%m-%d"), datetime.now(timezone.utc).strftime("%Y-%m-%d")]
    path = next((q for q in (os.path.join(DATA, f"{PRODUCT}_{d}.csv") for d in cands) if os.path.exists(q)), None)
    if path is None:
        print("no recording today — collector down. Nothing written."); return
    closes = minute_closes(path)
    if not closes:
        print("no trades parsed. Nothing written."); return
    last_min, last_px = closes[-1]
    age = (datetime.now(timezone.utc) - last_min).total_seconds()
    if age > STALE_SEC:
        print(f"book is {age:.0f}s old (> {STALE_SEC}s) — stale. Nothing written."); return
    px_by_min = {m.strftime("%Y-%m-%dT%H:%M"): p for m, p in closes}
    print(f"horizon_forecaster {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S}Z  spot {last_px:.2f}")
    for h in HORIZONS:
        tick_horizon(h, closes, last_min, last_px, px_by_min)
    print("  NOT TRADEABLE: calibration instrument; see research/NULL_RESULT.md.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true")
    args = ap.parse_args()
    n = 0
    while True:
        tick()
        n += 1
        if n % 10 == 0:                      # refresh the shared scoreboard every ~10 min
            try:
                import subprocess, sys
                subprocess.run([sys.executable, os.path.join(HERE, "scoreboard.py")],
                               check=False, timeout=120)
            except Exception as e:
                print(f"  scoreboard refresh failed: {type(e).__name__}")
        if not args.loop:
            return
        time.sleep(60)


if __name__ == "__main__":
    main()
