#!/usr/bin/env python3
"""scoreboard.py — one scoreboard for the 1 / 5 / 15-minute instrument.

Reads the three on-disk forecast books (minute_forecasts.csv for 1m;
forecasts_5m.csv, forecasts_15m.csv for the other rungs) and publishes, per horizon:
filed, resolved, ties excluded, days covered, hit rate vs the up-base-rate, Brier vs
climatology, Brier skill, and a 10-bin reliability table. Writes agent/scoreboard.json
and ../scoreboard.html (self-contained, no feeds — the Pages site can serve it).

The win rule it scores is the one Anupam stated: a row frozen at T says p_up for T+H;
at T+H the real last trade of that minute decides; direction obeyed = right. Nothing
else counts, and a row is never edited after it is written.

Reads only. Says n out loud. NOT a strategy.
"""
import csv, json, os, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BOOKS = {1: os.path.join(HERE, "minute_forecasts.csv"),
         5: os.path.join(HERE, "forecasts_5m.csv"),
         15: os.path.join(HERE, "forecasts_15m.csv")}


def stats(path):
    if not os.path.exists(path):
        return {"filed": 0, "resolved": 0, "note": "no book yet"}
    rows = list(csv.DictReader(open(path)))
    done = [r for r in rows if r.get("outcome") in ("right", "wrong")]
    ties = sum(1 for r in rows if r.get("outcome") == "tie")
    out = {"filed": len(rows), "resolved": len(done), "ties_excluded": ties,
           "pending": sum(1 for r in rows if not (r.get("outcome") or "").strip())}
    if not done:
        return out
    ps = [(float(r["p_up"]), 1 if r["up"] == "1" else 0) for r in done]
    hit = sum(1 for r in done if r["outcome"] == "right") / len(done)
    base = sum(u for _, u in ps) / len(ps)
    bs = sum((p - u) ** 2 for p, u in ps) / len(ps)
    clim = base * (1 - base)
    days = sorted({r["target_minute_utc"][:10] for r in done})
    bins = []
    for k in range(10):
        lo, hi = k / 10, (k + 1) / 10
        sel = [(p, u) for p, u in ps if lo <= p < hi or (k == 9 and p == 1.0)]
        if sel:
            bins.append({"lo": lo, "hi": hi, "n": len(sel),
                         "said": round(sum(p for p, _ in sel) / len(sel), 3),
                         "happened": round(sum(u for _, u in sel) / len(sel), 3)})
    out.update({"hit_rate": round(100 * hit, 2), "up_base_rate": round(100 * base, 2),
                "edge_vs_base_pp": round(100 * (hit - max(base, 1 - base)), 2),
                "brier": round(bs, 4), "climatology": round(clim, 4),
                "brier_skill": round(1 - bs / clim, 4) if clim else None,
                "days": len(days), "first_day": days[0], "last_day": days[-1],
                "bins": bins,
                "verdict": ("no skill vs base rate" if bs >= clim else "beats base rate")
                           + (" — PROVISIONAL, <30 days" if len(days) < 30 else "")})
    return out


def render(d):
    rows = ""
    for h in (1, 5, 15):
        s = d["horizons"][str(h)]
        if s.get("resolved"):
            rows += (f"<tr><td><b>+{h} min</b></td><td class=m>{s['filed']:,}</td><td class=m>{s['resolved']:,}</td>"
                     f"<td class=m>{s['days']}</td><td class=m>{s['hit_rate']:.1f}%</td><td class=m>{s['up_base_rate']:.1f}%</td>"
                     f"<td class=m>{s['edge_vs_base_pp']:+.2f}pp</td><td class=m>{s['brier']:.4f}</td><td class=m>{s['climatology']:.4f}</td>"
                     f"<td class='m {'ok' if s['brier_skill']>0 else 'bad'}'>{s['brier_skill']:+.4f}</td>"
                     f"<td>{s['verdict']}<br><span class=den>{s['days']} day{'' if s['days']==1 else 's'} — <b>days are the denominator, not rows</b>; "
                     f"{s['resolved']:,} rows inside {s['days']} session{'' if s['days']==1 else 's'} is {s['days']} observation{'' if s['days']==1 else 's'} of regime, not {s['resolved']:,}.</span></td></tr>")
        else:
            rows += f"<tr><td><b>+{h} min</b></td><td class=m>{s.get('filed',0):,}</td><td class=m>0</td><td colspan=8 style='text-align:left;opacity:.7'>{s.get('note','filed, nothing resolved yet')} — {s.get('pending',0)} pending</td></tr>"
    # CAL-001 (council directive, crypto-microstructure, 2026-09-01): publish the
    # calibration curve so the finding is VISIBLE while it waits for Anupam's ruling.
    # This block renders a diagnostic and nothing else. It adjusts no probability, sets
    # no threshold and is read by no forecaster — `minute_forecaster.py:196` still sets
    # p_up from the raw logistic and has never read calibration_table.json. That gap is
    # the finding, so it is stated on the page rather than quietly closed.
    act = []
    for h in (1, 5, 15):
        s = d["horizons"][str(h)]
        for b in s.get("bins") or []:
            if b["n"] >= 30 and abs(b["happened"] - b["said"]) > 0.10:
                act.append((h, b))
    cal = ""
    if act:
        lo_side = [b for h, b in act if b["said"] < 0.5]
        hi_side = [b for h, b in act if b["said"] >= 0.5]
        cal += ("<h3>Calibration finding (CAL-001) \u2014 published, not applied</h3>"
                "<div class=law><b>" + str(len(act)) + " actionable bins</b> (n\u2265" "30 and |gap|&gt;0.10) across the three clocks: "
                + ", ".join(f"+{h}min {b['lo']:.1f}\u2013{b['hi']:.1f} (n={b['n']:,}, said {b['said']:.3f}, happened {b['happened']:.3f}, "
                            f"gap {b['happened']-b['said']:+.3f})" for h, b in act)
                + ". <b>The pattern is not noise at these counts:</b> " + str(len(lo_side)) + " low bins run <b>UNDER-confident</b> "
                  "(the market went up far more often than the row said) and " + str(len(hi_side)) + " high bins run <b>OVER-confident</b> \u2014 "
                  "stated probabilities are compressed toward the tails while outcomes sit near the base rate. "
                  "<b>Nothing here has been applied.</b> The desk's calibration rule says adjust an actionable bin halfway toward "
                  "<i>happened</i>; this lab holds almost every actionable bin on the desk and its forecaster "
                  "(<code>minute_forecaster.py:196</code>, <code>p_up = 1/(1+exp(-z))</code>) does not read the calibration table at all. "
                  "That decision is Anupam's (CAL-001), not this lab's. The curve is published here so the cost of not applying it is "
                  "on the record while it waits.</div>")
    for h in (1, 5, 15):
        s = d["horizons"][str(h)]
        if s.get("bins"):
            cal += f"<h3>+{h} min reliability</h3><table><tr><th>said</th><th>n</th><th>happened</th><th>gap</th><th>actionable</th></tr>"
            for b in s["bins"]:
                gap = b["happened"] - b["said"]
                a = b["n"] >= 30 and abs(gap) > 0.10
                cal += (f"<tr><td class=m>{b['lo']:.1f}\u2013{b['hi']:.1f}</td><td class=m>{b['n']:,}</td><td class=m>{b['happened']:.3f}</td>"
                        f"<td class='m {'bad' if abs(gap)>0.1 else ''}'>{gap:+.3f}</td>"
                        f"<td class=m>{'<b>yes</b>' if a else ('\u2014' if b['n']>=30 else 'n&lt;30')}</td></tr>")
            cal += "</table>"
    return f"""<!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>BTC 1 / 5 / 15-minute scoreboard</title>
<style>:root{{--bg:#0d1117;--panel:#161b22;--line:#21262d;--ink:#e6edf3;--muted:#8b949e;--ok:#2a9d8f;--bad:#e76f51;--accent:#58a6ff}}
@media(prefers-color-scheme:light){{:root{{--bg:#f4f6f9;--panel:#fff;--line:#d9dee5;--ink:#0f1419;--muted:#5b6675}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}.wrap{{max-width:1000px;margin:0 auto;padding:28px 20px 60px}}
h1{{font-size:22px;margin:0 0 6px}}h3{{font-size:14px;margin:22px 0 6px}}p{{max-width:80ch;color:var(--muted)}}.m{{font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums;text-align:right}}
table{{border-collapse:collapse;width:100%;background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:13px}}th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left}}th{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.den{{display:block;font-size:11px;color:var(--muted);margin-top:3px}}.ok{{color:var(--ok)}}.bad{{color:var(--bad)}}.law{{border-left:3px solid var(--accent);background:rgba(88,166,255,.08);padding:10px 14px;border-radius:0 8px 8px 0;margin:14px 0}}.tscroll{{overflow-x:auto}}</style></head><body><div class=wrap>
<h1>BTC-USD · 1 / 5 / 15-minute forecast scoreboard</h1>
<p>Generated {d['generated']}. One instrument, three clocks: at time T a row is frozen saying p(up) for T+H; at T+H the real last trade of that minute decides. Direction obeyed = right. Rows are never edited. Ties (unchanged minute) are excluded, never counted as misses.</p>
<div class=law><b>Read this first.</b> This is a calibration instrument and is barred from trading. The lab's published result is a null: short-horizon BTC direction is not forecastable from these features, and the only real edge found (1 minute, +1.38pp, z=5.2) is worth ~+0.05 bps against a 60 bps retail fee — about 1/1,183rd of the cost of acting on it. A good run here is calibration, not money.</div>
<div class=tscroll><table><tr><th>horizon</th><th>filed</th><th>resolved</th><th>days</th><th>hit</th><th>up base</th><th>edge vs base</th><th>Brier</th><th>climatology</th><th>skill</th><th>verdict</th></tr>{rows}</table></div>
{cal}
<p style="margin-top:26px;font-size:12px">Minutes inside one session share a regime — the effective sample is nearer the day count than the row count. Source: agent/minute_forecasts.csv, agent/forecasts_5m.csv, agent/forecasts_15m.csv · built by agent/scoreboard.py · paper research, not advice.</p>
</div></body></html>"""


def main():
    d = {"generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
         "win_rule": "row frozen at T states p_up for T+H; real last trade at T+H decides; direction obeyed = right; ties excluded",
         "denominator_caveat": ("DAYS ARE THE DENOMINATOR, NOT ROWS. Minutes inside one UTC day share a regime, so "
                                "N rows over D days is D observations, not N. Any hit_rate, edge_vs_base_pp or "
                                "brier_skill quoted from this file MUST be quoted with its `days` count beside it "
                                "(council directive, crypto-microstructure, 2026-08-21)."),
         "horizons": {str(h): stats(p) for h, p in BOOKS.items()}}
    json.dump(d, open(os.path.join(HERE, "scoreboard.json"), "w"), indent=1)
    open(os.path.join(ROOT, "scoreboard.html"), "w").write(render(d))
    for h in (1, 5, 15):
        s = d["horizons"][str(h)]
        if s.get("resolved"):
            print(f"+{h:>2}m: {s['resolved']:,} resolved / {s['days']}d · hit {s['hit_rate']:.1f}% vs base {s['up_base_rate']:.1f}% · skill {s['brier_skill']:+.4f} · {s['verdict']}")
        else:
            print(f"+{h:>2}m: {s.get('filed',0)} filed, nothing resolved yet")


if __name__ == "__main__":
    main()
