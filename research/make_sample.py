#!/usr/bin/env python3
"""
Generate sample recorder CSVs to validate backtest.py.

Produces two files in the recorder's exact schema:
  sample_random.csv   — pure random walk, sides random  → harness must find NO edge
  sample_planted.csv  — order-flow imbalance genuinely predicts the next return
                        → harness must DETECT it (significant IC, positive gross)

A backtester you can't trust is worse than none. If it can't find a planted edge, it's
blind; if it "finds" edge in the random file, it's a liar. Both files test that.
"""
import numpy as np

T = 3600                 # seconds (1 hour)
BASE = 1_700_000_000_000 # arbitrary epoch ms
PX0 = 60000.0
SIG = 3.0                # per-second price noise, bps
rng = np.random.default_rng(42)


def write(path, planted):
    beta = 6.0 if planted else 0.0      # bps of next-return per unit latent signal
    rows = []
    u = 0.0
    price = PX0
    for t in range(T):
        u = 0.9 * u + rng.normal(0, 1)                 # AR(1) latent signal
        p_buy = np.clip(0.5 + (0.18 * np.tanh(u) if planted else 0.0), 0.05, 0.95)
        # this second's trades — sides biased by u when planted, so OFI ~ tracks u
        k = rng.integers(3, 12)
        ts_ms = BASE + t * 1000
        for _ in range(k):
            isbuy = 1 if rng.random() < p_buy else 0
            qty = float(rng.exponential(0.05))
            off = int(rng.integers(0, 1000))
            rows.append(('trade', ts_ms + off, round(price, 2), round(qty, 6), isbuy, '', ''))
        # book snapshot — book imbalance also tracks u a little when planted
        bimb = float(np.clip((0.3 * np.tanh(u) if planted else 0.0) + rng.normal(0, 0.15), -1, 1))
        bidvol = round(5 * (1 + bimb), 4)
        askvol = round(5 * (1 - bimb), 4)
        rows.append(('book', ts_ms, round(price, 2), 0.02, bidvol, askvol, round(bimb, 4)))
        # advance price: next return depends on current u when planted
        ret_bps = beta * u + rng.normal(0, SIG)
        price *= np.exp(ret_bps / 1e4)

    rows.sort(key=lambda r: r[1])
    with open(path, 'w') as f:
        f.write('type,ts_ms,px_or_mid,qty_or_spread,extra1,extra2,extra3\n')
        for r in rows:
            f.write(','.join(str(x) for x in r) + '\n')
    print(f"wrote {path}  ({len(rows):,} rows, planted={planted})")


if __name__ == '__main__':
    import os
    d = os.path.dirname(os.path.abspath(__file__))
    write(os.path.join(d, 'sample_random.csv'), planted=False)
    write(os.path.join(d, 'sample_planted.csv'), planted=True)
