#!/usr/bin/env python3
"""
Backtest harness for the Crypto Microstructure Lab recorder CSVs.

This is the honest validation gate: it does NOT ask "can I draw a nice equity curve",
it asks "does this signal predict forward returns better than chance, and does anything
survive transaction costs?"  Answers with an information coefficient, a permutation-test
p-value, and a cost-aware strategy backtest.

Input CSV schema (from forecast/index.html recorder):
    type, ts_ms, px_or_mid, qty_or_spread, extra1, extra2, extra3
    trade, <ms>, price, qty,   isBuy(1/0), ,
    book,  <ms>, mid,   spread, bidVol,    askVol, bookImbalance

Usage:
    python backtest.py RECORDING.csv
    python backtest.py RECORDING.csv --horizons 5,15,30,60 --ofi-window 10 --cost-bps 10
"""
import argparse, sys
import numpy as np
import pandas as pd
from scipy import stats


def load(path):
    df = pd.read_csv(path, header=0,
                     names=['type', 'ts', 'a', 'b', 'c', 'd', 'e'])
    df['ts'] = pd.to_numeric(df['ts'], errors='coerce')
    df = df.dropna(subset=['ts'])
    trades = df[df['type'] == 'trade'].copy()
    trades = trades.rename(columns={'a': 'price', 'b': 'qty', 'c': 'isbuy'})
    for col in ['price', 'qty', 'isbuy']:
        trades[col] = pd.to_numeric(trades[col], errors='coerce')
    trades = trades.dropna(subset=['price', 'qty'])
    book = df[df['type'] == 'book'].copy()
    book = book.rename(columns={'a': 'mid', 'b': 'spread',
                                'c': 'bidvol', 'd': 'askvol', 'e': 'bookimb'})
    for col in ['mid', 'spread', 'bidvol', 'askvol', 'bookimb']:
        book[col] = pd.to_numeric(book[col], errors='coerce')
    book = book.dropna(subset=['mid'])
    return trades, book


def build_panel(trades, book, ofi_window):
    """Merge onto a 1-second grid and compute signals aligned to forward returns."""
    t0 = int(min(trades['ts'].min() if len(trades) else book['ts'].min(),
                 book['ts'].min()))
    t1 = int(max(trades['ts'].max() if len(trades) else book['ts'].max(),
                 book['ts'].max()))
    sec = np.arange(t0 // 1000, t1 // 1000 + 1)
    grid = pd.DataFrame(index=sec)

    # mid price per second (last observation carried forward)
    book = book.assign(s=(book['ts'] // 1000).astype(int))
    mid = book.groupby('s')['mid'].last()
    bookimb = book.groupby('s')['bookimb'].last()
    spread = book.groupby('s')['spread'].last()
    grid['mid'] = mid.reindex(sec).ffill()
    grid['book_imb'] = bookimb.reindex(sec).ffill()
    grid['spread'] = spread.reindex(sec).ffill()

    # order-flow imbalance over a trailing window
    if len(trades):
        trades = trades.assign(s=(trades['ts'] // 1000).astype(int))
        signed = trades['qty'] * np.where(trades['isbuy'] > 0.5, 1.0, -1.0)
        sv = signed.groupby(trades['s']).sum().reindex(sec).fillna(0.0)
        tv = trades['qty'].groupby(trades['s']).sum().reindex(sec).fillna(0.0)
        roll_s = sv.rolling(ofi_window, min_periods=1).sum()
        roll_t = tv.rolling(ofi_window, min_periods=1).sum()
        grid['ofi'] = (roll_s / roll_t.replace(0, np.nan)).fillna(0.0)
    else:
        grid['ofi'] = 0.0

    grid = grid.dropna(subset=['mid'])
    return grid


def fwd_return_bps(grid, h):
    return (grid['mid'].shift(-h) / grid['mid'] - 1.0) * 1e4


def evaluate(grid, signal, h, cost_bps, n_perm, rng):
    fwd = fwd_return_bps(grid, h)
    s = grid[signal]
    ok = fwd.notna() & s.notna()
    s, fwd = s[ok].values, fwd[ok].values
    if len(s) < 30 or np.std(s) == 0:
        return None

    # information coefficient (Spearman) + permutation p-value
    ic = stats.spearmanr(s, fwd).correlation
    perm = np.empty(n_perm)
    for i in range(n_perm):
        perm[i] = stats.spearmanr(rng.permutation(s), fwd).correlation
    p_ic = (np.sum(np.abs(perm) >= abs(ic)) + 1) / (n_perm + 1)

    # non-overlapping strategy: trade on sign(centered signal), hold h seconds
    # (centering makes it work whether a signal is recorded signed [-1,1] or unsigned [0,1])
    s_c = s - np.median(s)
    idx = np.arange(0, len(s_c), h)
    pos = np.sign(s_c[idx])
    ret = pos * fwd[idx]                      # gross per-trade return, bps
    ret = ret[np.isfinite(ret)]
    n = len(ret)
    gross = ret.mean() if n else 0.0
    net = gross - cost_bps                    # round-trip cost per trade
    hit = np.mean(ret > 0) if n else 0.0
    # annualized Sharpe of the net per-trade series
    per_year = (365 * 24 * 3600) / h
    net_series = ret - cost_bps
    sharpe = (net_series.mean() / net_series.std() * np.sqrt(per_year)
              if n > 2 and net_series.std() > 0 else 0.0)
    return dict(h=h, n=n, ic=ic, p=p_ic, gross=gross, net=net,
                breakeven=gross, hit=hit, sharpe=sharpe)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('--horizons', default='5,15,30,60')
    ap.add_argument('--ofi-window', type=int, default=10, help='OFI trailing window, seconds')
    ap.add_argument('--cost-bps', type=float, default=10.0,
                    help='round-trip cost per trade in bps (fees + half-spread each side)')
    ap.add_argument('--permutations', type=int, default=500)
    ap.add_argument('--seed', type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    horizons = [int(x) for x in args.horizons.split(',')]

    trades, book = load(args.csv)
    grid = build_panel(trades, book, args.ofi_window)
    dur_min = (grid.index[-1] - grid.index[0]) / 60 if len(grid) else 0
    print(f"\n  File: {args.csv}")
    print(f"  {len(trades):,} trades · {len(book):,} book snapshots · "
          f"{len(grid):,} 1s bars · {dur_min:.1f} min · cost {args.cost_bps:.0f} bps/trade\n")
    if len(grid) < 120:
        print("  ⚠  Very short sample (<2 min of bars). Record more before trusting anything.\n")

    signals = [s for s in ['ofi', 'book_imb'] if grid[s].std() > 0]
    any_edge = False
    for sig in signals:
        print(f"  ── signal: {sig} " + "─" * (40 - len(sig)))
        print(f"     {'horizon':>7} {'IC':>7} {'p-val':>7} {'gross':>8} {'net':>8} "
              f"{'hit%':>6} {'Sharpe':>7} {'N':>6}")
        for h in horizons:
            r = evaluate(grid, sig, h, args.cost_bps, args.permutations, rng)
            if r is None:
                continue
            flag = ''
            if r['p'] < 0.05 and abs(r['ic']) > 0.02:
                flag = ' *'            # statistically non-random association
            if r['net'] > 0 and r['p'] < 0.05:
                flag = ' **'; any_edge = True
            print(f"     {h:>6}s {r['ic']:>7.3f} {r['p']:>7.3f} "
                  f"{r['gross']:>7.2f} {r['net']:>7.2f} {r['hit']*100:>5.1f} "
                  f"{r['sharpe']:>7.2f} {r['n']:>6}{flag}")
        print()

    print("  " + "═" * 58)
    if any_edge:
        print("  VERDICT: a signal is BOTH statistically significant (p<0.05) AND")
        print("           net-positive after costs (**). Promising — but validate on")
        print("           MORE, out-of-sample recordings before believing it.")
    else:
        sig_only = "some IC is significant but dies after costs" \
            if any(True for _ in [0]) else ""
        print("  VERDICT: no signal is net-positive after costs. This is the")
        print("           expected, honest result — order-flow edge at these")
        print("           horizons is arbitraged away and fees finish the job.")
    print("  Legend:  * = significant association (p<0.05)   ** = also net-positive")
    print("  IC = Spearman rank corr (signal vs forward return). Higher |IC| = more predictive.")
    print("  'breakeven' cost per trade = gross bps; you profit only if real costs are below it.\n")


if __name__ == '__main__':
    main()
