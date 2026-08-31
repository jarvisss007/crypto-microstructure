"""Exact-minute price-point study: 'at 9:15 it will be at THIS price' — did it work?

Anupam, 2026-08-31. Targets already land on exact minutes (every target_minute is
:00s). This judges the POINT forecast against the only honest null, the random walk
(pred = price now), at those exact minutes: MAE model vs MAE RW, by horizon and by
hour of day, plus direction hit for context. Rows without pred_px predate the
definition (frozen 2026-08-31 in minute_forecaster.py) and are reported as such,
never backfilled — a point forecast invented after the outcome is not a forecast.
"""
import csv, datetime as dt, os, statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run():
    out = []
    for name in ("forecasts_5m", "forecasts_15m", "minute_forecasts"):
        p = os.path.join(HERE, "agent", f"{name}.csv")
        if not os.path.exists(p):
            continue
        rows = [r for r in csv.DictReader(open(p))
                if (r.get("outcome") or "").strip() and (r.get("px_at_target") or "").strip()]
        withp = [r for r in rows if (r.get("pred_px") or "").strip()]
        out.append(f"{name}: {len(rows)} resolved, {len(withp)} carry pred_px "
                   f"(definition frozen 2026-08-31; earlier rows are direction-only)")
        if len(withp) < 30:
            out.append(f"  NOT READABLE: {len(withp)}/30 point-forecast rows.")
            continue
        mae_m = st.mean(abs(float(r["pred_px"]) - float(r["px_at_target"])) for r in withp)
        mae_rw = st.mean(abs(float(r["px_at_call"]) - float(r["px_at_target"])) for r in withp)
        out.append(f"  MAE model {mae_m:.2f} vs random-walk {mae_rw:.2f} "
                   f"-> skill {(1 - mae_m / mae_rw) * 100:+.2f}% "
                   f"({'model adds information' if mae_m < mae_rw else 'the walk wins — no point edge'})")
        byh = defaultdict(list)
        for r in withp:
            h = r["made_at_utc"][11:13]
            byh[h].append((abs(float(r["pred_px"]) - float(r["px_at_target"])),
                           abs(float(r["px_at_call"]) - float(r["px_at_target"]))))
        for h in sorted(byh):
            v = byh[h]
            out.append(f"    {h}:00 UTC  n={len(v)}  model {st.mean(a for a,_ in v):.2f}  "
                       f"rw {st.mean(b for _,b in v):.2f}")
    print("\n".join(out) if out else "no books found")

if __name__ == "__main__":
    run()
