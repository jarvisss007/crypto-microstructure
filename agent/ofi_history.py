#!/usr/bin/env python3
"""ofi_history.py — recompute session OFI for EVERY recorded session, from the files.

CRYP-006 (council directive 2026-08-27, built 2026-08-28). The lab enumerated a
residual honestly rather than declaring the question settled: sessions with a data
file and no brief, plus briefs that carry no numeric OFI. Ten of them carried no
OFI anywhere the desk could read. The `.csv.gz` archives exist for all of them, so
the number can be RECOMPUTED rather than re-run — nothing here re-enacts a past
session or invents a value that was never measured.

What it does: for each research/data/BTC-USD_<date>.csv[.gz], read the `trade` rows
and compute the pre-registered session imbalance

    OFI = (buyVol - sellVol) / totalVol      over qty_or_spread / extra1

using the schema the README documents (CRYP-004's correction: qty_or_spread and
extra1, NOT the `qty, isBuy` shorthand that matched zero rows). Writes
agent/ofi_history.csv — one row per session, machine-readable, so no future run
has to grep prose for a number.

This file REPORTS. It writes no ledger row, makes no call, and changes no bar:
the |OFI| >= 0.10 trigger is untouched and the 1-day ledger unit stays RETIRED
under CRYP-002. A recomputed OFI is a measurement of a past session, never a
retroactive call on it.

Run:  /opt/anaconda3/bin/python agent/ofi_history.py
"""
import csv, glob, gzip, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "ofi_history.csv")


def session_ofi(path):
    op = gzip.open if path.endswith(".gz") else open
    buy = sell = 0.0
    n = 0
    last = ""
    with op(path, "rt") as f:
        for row in csv.reader(f):
            if not row or row[0] != "trade":
                continue
            try:
                q = float(row[3]); b = float(row[4])
            except (IndexError, ValueError):
                continue
            n += 1
            last = row[2]
            if b >= 0.5:
                buy += q
            else:
                sell += q
    tot = buy + sell
    return n, buy, sell, ((buy - sell) / tot if tot else None), last


def main():
    files = {}
    for p in glob.glob(os.path.join(ROOT, "research/data/BTC-USD_*.csv*")):
        d = re.search(r"_(\d{4}-\d{2}-\d{2})", os.path.basename(p)).group(1)
        # prefer the plain .csv when both exist (the .gz is its archive)
        if d not in files or not p.endswith(".gz"):
            files[d] = p
    briefs = {os.path.basename(f)[:10] for f in glob.glob(os.path.join(HERE, "briefs/*.md"))}

    rows = []
    for d in sorted(files):
        n, buy, sell, ofi, last = session_ofi(files[d])
        rows.append({
            "date": d,
            "trade_rows": n,
            "buy_vol": f"{buy:.6f}",
            "sell_vol": f"{sell:.6f}",
            "ofi": "" if ofi is None else f"{ofi:+.6f}",
            "abs_ofi_ge_0.10": "" if ofi is None else ("yes" if abs(ofi) >= 0.10 else "no"),
            "last_trade_px": last,
            "source": "gz-archive" if files[d].endswith(".gz") else "live-csv",
            "had_brief": "yes" if d in briefs else "no",
        })
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    cleared = [r for r in rows if r["abs_ofi_ge_0.10"] == "yes"]
    print(f"OFI history -> {OUT}")
    print(f"  {len(rows)} sessions, {sum(1 for r in rows if r['had_brief']=='no')} of them with no brief")
    print(f"  sessions clearing the |OFI| >= 0.10 trigger: {len(cleared)}"
          + (f" ({', '.join(r['date'] for r in cleared)})" if cleared else ""))
    vals = [float(r["ofi"]) for r in rows if r["ofi"]]
    print(f"  |OFI| range {min(abs(v) for v in vals):.4f} .. {max(abs(v) for v in vals):.4f}")


if __name__ == "__main__":
    main()
