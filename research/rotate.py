#!/usr/bin/env python3
"""rotate.py — keep the ingot, stop hoarding the ore.

Anupam, 2026-08-21: "Where is it even recording and why is it getting bigger? Don't we
have anything like how we built the trading firm with the stocks?" The collector writes
every trade plus one book snapshot a second (~1.2M rows, ~50 MB a day) and nothing ever
summarised it, while every piece of research here runs on the 1-MINUTE series that
backtest_all.build_minute_series() re-derives from the raw tape each time. The stock
desk keeps derived daily data in git and treats feeds as feeds. This file applies the
same convention to the crypto lab, nightly:

  1. DERIVE  — for every complete UTC day, write research/minutes/BTC-USD_<day>.csv:
               the research's own minute series (close, book_imb, ofi — identical code
               path, imported from backtest_all) plus per-minute trade count, volume,
               buy share, high and low. ~150 KB/day. Tracked in git = backed up.
  2. COMPRESS — raw CSVs older than today become .csv.gz (≈5×), after the row count of
               the gz is verified equal to the raw. Readers open .gz transparently.
  3. ARCHIVE  — once a calendar month is complete and fully compressed, its gz files are
               tarred and attached to a GitHub Release `data-YYYY-MM` on this (public)
               repo — public market data, off-machine, free. The manifest records it.
  4. PRUNE    — a gz older than KEEP_DAYS is deleted ONLY if its month is in the manifest
               as released. Nothing is ever deleted that exists nowhere else.

Nothing here touches today's file (the collector is writing it) and nothing edits a
minute file once written. Run: python3 research/rotate.py [--dry] [--no-release]
"""
import argparse, csv, datetime as dt, glob, gzip, json, os, shutil, subprocess, sys, tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
MIN = os.path.join(HERE, "minutes")
MANIFEST = os.path.join(HERE, "archive_manifest.json")
PRODUCT = "BTC-USD"
KEEP_DAYS = 30
REPO = "jarvisss007/crypto-microstructure"
sys.path.insert(0, HERE)


def day_of(path):
    b = os.path.basename(path)
    return b.split("_", 1)[1].replace(".csv.gz", "").replace(".csv", "")


def row_count(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as fh:
        return sum(1 for _ in fh)


def derive(path, day, dry):
    out = os.path.join(MIN, f"{PRODUCT}_{day}.csv")
    if os.path.exists(out):
        return "have"
    import pandas as pd, numpy as np
    from backtest_all import build_minute_series
    df = pd.read_csv(path, header=0, names=["type", "ts", "a", "b", "c", "d", "e"])
    df["ts"] = pd.to_numeric(df["ts"], errors="coerce"); df = df.dropna(subset=["ts"])
    df["day"] = day
    m = build_minute_series(df)
    tr = df[df["type"] == "trade"].copy()
    tr["price"] = pd.to_numeric(tr["a"], errors="coerce"); tr["qty"] = pd.to_numeric(tr["b"], errors="coerce")
    tr["isbuy"] = pd.to_numeric(tr["c"], errors="coerce"); tr = tr.dropna(subset=["price", "qty"])
    tr["min"] = (tr["ts"] // 60000).astype(int)
    g = tr.groupby("min")
    extra = pd.DataFrame({"trades": g.size(), "volume": g["qty"].sum(),
                          "buy_share": g.apply(lambda x: float((x["qty"] * (x["isbuy"] > 0.5)).sum() / x["qty"].sum()) if x["qty"].sum() else np.nan),
                          "high": g["price"].max(), "low": g["price"].min()})
    m = m.join(extra, how="left")
    m.index.name = "minute_epoch"
    m.insert(0, "minute_utc", [dt.datetime.fromtimestamp(int(i) * 60, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M") for i in m.index])
    if not dry:
        os.makedirs(MIN, exist_ok=True)
        m.to_csv(out, float_format="%.6f")
    return f"derived {len(m)} minutes"


def compress(path, dry):
    gz = path + ".gz"
    if os.path.exists(gz):
        return "gz exists"
    if dry:
        return "would gzip"
    with open(path, "rb") as fi, gzip.open(gz, "wb", compresslevel=6) as fo:
        shutil.copyfileobj(fi, fo)
    if row_count(gz) != row_count(path):
        os.remove(gz); return "VERIFY FAILED — raw kept"
    os.remove(path)
    return f"gzipped ({os.path.getsize(gz) // 1048576} MB)"


def release_month(month, files, manifest, dry):
    tag = f"data-{month}"
    if month in manifest:
        return "released"
    if dry:
        return f"would release {len(files)} files"
    tar = os.path.join(DATA, f"{PRODUCT}_{month}.tar")
    with tarfile.open(tar, "w") as t:
        for f in files: t.add(f, arcname=os.path.basename(f))
    size = os.path.getsize(tar) // 1048576
    r = subprocess.run(["gh", "release", "view", tag, "-R", REPO], capture_output=True, text=True)
    if r.returncode != 0:
        r = subprocess.run(["gh", "release", "create", tag, tar, "-R", REPO, "--title", f"Raw tape {month}",
                            "--notes", f"BTC-USD trades + 1/s book snapshots, {len(files)} days, gzip per day ({size} MB). Public Coinbase data. Derived minute series are tracked in research/minutes/."],
                           capture_output=True, text=True)
    else:
        r = subprocess.run(["gh", "release", "upload", tag, tar, "-R", REPO, "--clobber"], capture_output=True, text=True)
    os.remove(tar)
    if r.returncode != 0:
        return f"RELEASE FAILED: {r.stderr.strip()[:120]}"
    manifest[month] = {"tag": tag, "files": [os.path.basename(f) for f in files], "mb": size,
                       "released": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")}
    json.dump(manifest, open(MANIFEST, "w"), indent=1)
    return f"released {len(files)} files, {size} MB -> {tag}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true"); ap.add_argument("--no-release", action="store_true")
    a = ap.parse_args()
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    files = sorted(glob.glob(os.path.join(DATA, f"{PRODUCT}_*.csv")) + glob.glob(os.path.join(DATA, f"{PRODUCT}_*.csv.gz")))
    log = []
    for f in files:
        day = day_of(f)
        if day >= today:
            continue                                   # the collector owns today
        try:
            log.append(f"{day}: {derive(f, day, a.dry)}")
        except Exception as e:
            log.append(f"{day}: derive FAILED ({type(e).__name__}: {str(e)[:60]})")
        if f.endswith(".csv"):
            log.append(f"{day}: {compress(f, a.dry)}")
    # months complete and fully compressed -> release
    if not a.no_release:
        this_month = today[:7]
        by_month = {}
        for f in sorted(glob.glob(os.path.join(DATA, f"{PRODUCT}_*.csv.gz"))):
            by_month.setdefault(day_of(f)[:7], []).append(f)
        for month, fs in by_month.items():
            if month < this_month and not glob.glob(os.path.join(DATA, f"{PRODUCT}_{month}-*.csv")):
                log.append(f"{month}: {release_month(month, fs, manifest, a.dry)}")
    # prune: older than KEEP_DAYS AND released
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    for f in sorted(glob.glob(os.path.join(DATA, f"{PRODUCT}_*.csv.gz"))):
        day = day_of(f)
        if day < cutoff and day[:7] in manifest and os.path.basename(f) in manifest[day[:7]]["files"]:
            if not a.dry: os.remove(f)
            log.append(f"{day}: pruned local gz (released in {manifest[day[:7]]['tag']})")
    for line in log: print("  " + line)
    raw = sum(os.path.getsize(f) for f in glob.glob(os.path.join(DATA, "*.csv")))
    gzs = sum(os.path.getsize(f) for f in glob.glob(os.path.join(DATA, "*.csv.gz")))
    mins = sum(os.path.getsize(f) for f in glob.glob(os.path.join(MIN, "*.csv")))
    print(f"rotate {today}{' [DRY]' if a.dry else ''}: raw {raw/1048576:.0f} MB · gz {gzs/1048576:.0f} MB · minutes {mins/1048576:.1f} MB · released months {sorted(manifest)}")


if __name__ == "__main__":
    main()
