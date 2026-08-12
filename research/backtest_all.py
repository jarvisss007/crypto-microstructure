#!/usr/bin/env python3
"""
Cumulative honest backtest for the forecast.html 15-min online model.

Unlike backtest.py (which grades raw signals on ONE day's file), this replays
forecast.html's exact online-SGD algorithm — same features, same update rule,
same learning rate — over EVERY recorded day in chronological order. Because
online SGD only ever updates from pairs resolved strictly in the past, this
single pass is already walk-forward / out-of-sample at every prediction: no
day-split bookkeeping needed, the causality is structural.

Output: research/data/learned_weights.json — the fully-trained weight vector
(what a browser tab would have learned had it been open continuously all week)
plus per-day and overall out-of-sample skill, for forecast.html to warm-start
fresh sessions from instead of zero.

Usage:
    python backtest_all.py                      # all data/*.csv, cost 60bps
    python backtest_all.py --cost-bps 60 --data-dir data
"""
import argparse, glob, json, math, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

H = 15            # forecast horizon, minutes — must match forecast.html
# LR was 0.02 originally; a full-week cumulative backtest showed that value lets the
# online model wander into a confidently WRONG state (skill -0.60, some days <30% hit
# rate) instead of the "shrinks toward zero" behavior the README describes. LR=0.002
# (validated here) tracks that expectation much more faithfully (skill -0.03) — see
# research/README.md "cumulative backtest" section. Keep in sync with forecast.html's LR.
LR, L2 = 0.002, 0.002
FEATS = ['bias', '1-min mom', '5-min mom', '15-min revert', 'order-flow imb', 'book imb']
NF = len(FEATS)
SIGMA_WINDOW = 300   # minutes — mirrors Coinbase's default ~300-candle response
OFI_WINDOW_S = 60    # seconds — mirrors liveOFI()'s trailing window
BOOK_LEVELS = 20     # mirrors liveBookImb()'s top-20-level depth


def load_all(data_dir):
    files = sorted(glob.glob(os.path.join(data_dir, 'BTC-USD_*.csv')))
    if not files:
        sys.exit(f'no BTC-USD_*.csv files in {data_dir}')
    frames = []
    for f in files:
        df = pd.read_csv(f, header=0, names=['type', 'ts', 'a', 'b', 'c', 'd', 'e'])
        df['ts'] = pd.to_numeric(df['ts'], errors='coerce')
        df = df.dropna(subset=['ts'])
        df['day'] = os.path.basename(f).split('_', 1)[1].removesuffix('.csv')
        frames.append(df)
    return pd.concat(frames, ignore_index=True).sort_values('ts').reset_index(drop=True)


def build_minute_series(df):
    """1-minute closes (proxy for Coinbase REST candles) + causal OFI / book-imbalance
    at each minute mark, all computed from data at-or-before that minute — no lookahead."""
    trades = df[df['type'] == 'trade'].copy()
    trades = trades.rename(columns={'a': 'price', 'b': 'qty', 'c': 'isbuy'})
    for c in ['price', 'qty', 'isbuy']:
        trades[c] = pd.to_numeric(trades[c], errors='coerce')
    trades = trades.dropna(subset=['price', 'qty'])

    book = df[df['type'] == 'book'].copy()
    book = book.rename(columns={'a': 'mid', 'b': 'spread', 'c': 'bidvol', 'd': 'askvol', 'e': 'bookimb'})
    for c in ['mid', 'bidvol', 'askvol', 'bookimb']:
        book[c] = pd.to_numeric(book[c], errors='coerce')
    book = book.dropna(subset=['mid'])

    book['min'] = (book['ts'] // 60000).astype(int)
    mid = book.groupby('min')['mid'].last()
    bookimb = book.groupby('min')['bookimb'].last()   # already (bidvol-askvol)/(bidvol+askvol), top-20
    day = df.groupby((df['ts'] // 60000).astype(int))['day'].first()

    t0, t1 = mid.index.min(), mid.index.max()
    full = pd.RangeIndex(t0, t1 + 1)
    closes = mid.reindex(full).ffill()
    bookimb = bookimb.reindex(full).ffill().fillna(0.0)
    day = day.reindex(full).ffill()

    # trailing-60s OFI evaluated AT each minute boundary (causal: only trades <= that ts)
    trades['sec'] = trades['ts'] // 1000
    signed = trades['qty'] * np.where(trades['isbuy'] > 0.5, 1.0, -1.0)
    sv = signed.groupby(trades['sec']).sum()
    tv = trades['qty'].groupby(trades['sec']).sum()
    sec_full = pd.RangeIndex(int(t0 * 60), int(t1 * 60) + 1)
    sv = sv.reindex(sec_full).fillna(0.0)
    tv = tv.reindex(sec_full).fillna(0.0)
    roll_sv = sv.rolling(OFI_WINDOW_S, min_periods=1).sum()
    roll_tv = tv.rolling(OFI_WINDOW_S, min_periods=1).sum()
    ofi_sec = (roll_sv / roll_tv.replace(0, np.nan)).fillna(0.0)
    ofi = ofi_sec.reindex(np.asarray(full) * 60).values

    return pd.DataFrame({'close': closes.values, 'book_imb': bookimb.values,
                          'ofi': ofi, 'day': day.values}, index=full)


def run_online_pass(m, cost_bps):
    """Sequential online SGD pass — identical algorithm to forecast.html's
    maybePredict()/resolvePending(). Every prediction uses only strictly-past
    weights, so this is walk-forward by construction."""
    closes = m['close'].values
    n = len(closes)
    w = np.zeros(NF)
    pending = {}          # made_idx -> (f, z, price, sig)
    rows = []              # per-resolved-prediction records for reporting
    logret = np.full(n, np.nan)
    logret[1:] = np.log(closes[1:] / closes[:-1])

    for i in range(n):
        # resolve anything maturing now
        tgt = i - H
        if tgt in pending:
            f, z, price, sig = pending.pop(tgt)
            actual = closes[i]
            z_act = float(np.clip(np.log(actual / price) / (sig * np.sqrt(H)), -6, 6))
            err = z - z_act
            w = w * (1 - LR * L2) - LR * err * f
            pred_ret = z * sig * np.sqrt(H)
            pred_px = price * (1 + pred_ret)
            act_ret_bps = (actual / price - 1) * 1e4
            pred_ret_bps = pred_ret * 1e4
            net_bps = np.sign(pred_ret_bps) * act_ret_bps - cost_bps if pred_ret_bps != 0 else 0.0
            # A bar is SCORABLE for direction only if a position was actually
            # taken (pred != 0) and the outcome was not flat (act != 0).
            #
            # Until 2026-08-12 `hit` was int(sign(pred) == sign(act)), which
            # made every unchanged minute bar a forced miss: sign(act) is 0 and
            # no nonzero prediction can equal it. A third of 1-min BTC bars
            # close unchanged, so that alone dragged the reported hit rate to
            # 34% and produced a spurious z of -73 — and because flat bars
            # thin out as the horizon lengthens (17,808 at 1m vs 7,709 at 15m),
            # it manufactured a clean 34%->42% "trend" across horizons that was
            # pure tie density. It also disagreed with net_bps one line up,
            # which already treats pred==0 as no-trade rather than as wrong.
            scorable = pred_ret_bps != 0 and act_ret_bps != 0
            rows.append(dict(day=m['day'].values[i], z=z, z_act=z_act,
                              sq_err=(z - z_act) ** 2, sq_base=z_act ** 2,
                              scorable=int(scorable),
                              hit=int(np.sign(pred_ret_bps) == np.sign(act_ret_bps)) if scorable else 0,
                              up=int(act_ret_bps > 0) if scorable else 0,
                              long=int(pred_ret_bps > 0) if scorable else 0,
                              net_bps=net_bps))

        if i < 20:
            continue
        # rolling causal sigma over trailing SIGMA_WINDOW minutes of log-returns
        lo = max(1, i - SIGMA_WINDOW + 1)
        window = logret[lo:i + 1]
        window = window[~np.isnan(window)]
        if len(window) < 10:
            continue
        sig = float(np.std(window)) or 1e-6

        p = closes[i]
        r1 = np.clip(np.log(p / closes[i - 1]) / sig, -4, 4)
        r5 = np.clip(np.log(p / closes[i - 5]) / (sig * np.sqrt(5)), -4, 4) if i >= 5 else 0.0
        win15 = closes[max(0, i - 14):i + 1]
        ma = win15.mean()
        rev = np.clip(np.log(ma / p) / (sig * np.sqrt(15)), -4, 4)
        f = np.array([1.0, r1, r5, rev, m['ofi'].values[i], m['book_imb'].values[i]])
        z = float(np.clip(w @ f, -4, 4))
        pending[i] = (f, z, p, sig)

    return w, pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-dir', default=os.path.join(HERE, 'data'))
    ap.add_argument('--out', default=os.path.join(HERE, 'learned_weights.json'),
                     help='tracked (non-gitignored) path so it publishes to GitHub Pages')
    ap.add_argument('--cost-bps', type=float, default=60.0)
    args = ap.parse_args()

    print(f'Loading all recorded days from {args.data_dir} ...')
    df = load_all(args.data_dir)
    days = sorted(df['day'].unique())
    print(f'{len(df):,} raw rows across {len(days)} day(s): {days[0]} .. {days[-1]}')

    m = build_minute_series(df)
    print(f'{len(m):,} minute bars built ({(len(m)/1440):.1f} days of continuous grid)')

    w, results = run_online_pass(m, args.cost_bps)

    if results.empty:
        sys.exit('not enough data to resolve any 15-min predictions yet')

    overall_skill = 1 - results['sq_err'].sum() / results['sq_base'].sum()
    overall_net = results['net_bps'].mean()

    # Direction is scored ONLY over scorable bars, and ONLY against the base
    # rate of that same subset. A model that is simply long more often than
    # short earns the up-move base rate with no skill at all; comparing its
    # hit rate to a flat 50% would bank that as an edge. `naive` is what a
    # skill-free model with this model's exact long/short mix would score, so
    # edge_pp is the only number here that can support a claim.
    sc = results[results['scorable'] == 1]
    n_sc = len(sc)
    n_tie = len(results) - n_sc
    overall_hit = sc['hit'].mean() if n_sc else float('nan')
    base_up = sc['up'].mean() if n_sc else float('nan')
    long_share = sc['long'].mean() if n_sc else float('nan')
    naive = long_share * base_up + (1 - long_share) * (1 - base_up)
    edge_pp = (overall_hit - naive) * 100
    edge_z = (overall_hit - naive) / math.sqrt(0.25 / n_sc) if n_sc else float('nan')
    gross_bps = overall_net + args.cost_bps

    per_day = results.groupby('day').agg(
        n=('z', 'size'),
        skill=('sq_err', lambda s: 1 - s.sum() / results.loc[s.index, 'sq_base'].sum()),
        # hit over that day's SCORABLE bars only — same tie rule as the overall
        # figure. Averaging the raw flag would divide by every bar including
        # ties, which is what made quiet days look catastrophic (2026-08-09
        # read 27.4% purely because it was a flat tape).
        hit=('hit', 'sum'),
        n_scorable=('scorable', 'sum'),
        net_bps=('net_bps', 'mean'),
    ).reset_index()
    per_day['hit'] = per_day['hit'] / per_day['n_scorable'].replace(0, np.nan)

    print(f'\n  {len(results):,} resolved 15-min predictions, walk-forward (online, no lookahead)\n')
    print(f'  {"day":>12} {"n":>6} {"skill":>8} {"hit%":>6} {"net_bps":>8}')
    for _, r in per_day.iterrows():
        print(f'  {r.day:>12} {int(r.n):>6} {r.skill:>8.4f} {r.hit*100:>5.1f} {r.net_bps:>8.2f}')
    print(f'\n  {"OVERALL":>12} {len(results):>6} {overall_skill:>8.4f} {overall_hit*100:>5.1f} {overall_net:>8.2f}\n')

    print(f'  direction scored on {n_sc:,} bars; {n_tie:,} dropped as ties '
          f'(outcome exactly flat — a tie predicted nothing either way)')
    print(f'  hit {overall_hit*100:.1f}%  vs base-rate-matched naive '
          f'{naive*100:.1f}%  (up-moves {base_up*100:.1f}%, model long '
          f'{long_share*100:.1f}% of the time)')
    print(f'  EDGE {edge_pp:+.2f}pp  z={edge_z:+.2f}   '
          f'gross {gross_bps:+.2f} bps/trade before costs\n')

    # Both tests must hold. Significance without economics is the trap this
    # account's tooling exists to catch: at 1-min the direction edge is real
    # at z>5 and worth 0.07 bps against a 60 bps cost.
    edge = overall_skill > 0.01 and overall_net > 0
    verdict = ('a genuine edge survives — skill beats random walk AND clears '
               f'{args.cost_bps:.0f}bps costs. Validate further before trusting it.') if edge else \
        ('no edge — matches every prior finding in this account. Weights below are '
         'the honest zero-ish baseline the online model converges to, not a trading signal.')
    print(f'  VERDICT: {verdict}\n')

    out = dict(
        generated_from_days=days,
        n_minute_bars=int(len(m)),
        n_resolved_predictions=int(len(results)),
        cost_bps=args.cost_bps,
        weights=dict(zip(FEATS, [float(x) for x in w])),
        overall_skill_vs_random_walk=float(overall_skill),
        overall_hit_rate=float(overall_hit),
        n_scorable=int(n_sc),
        n_ties_dropped=int(n_tie),
        base_rate_up=float(base_up),
        model_long_share=float(long_share),
        naive_hit_rate=float(naive),
        edge_pp_vs_base=float(edge_pp),
        edge_z=float(edge_z),
        gross_bps_per_trade=float(gross_bps),
        overall_net_bps=float(overall_net),
        per_day=per_day.to_dict(orient='records'),
        verdict=verdict,
        edge_found=bool(edge),
    )
    with open(args.out, 'w') as fh:
        json.dump(out, fh, indent=2)
    print(f'  wrote {args.out}')


if __name__ == '__main__':
    main()
