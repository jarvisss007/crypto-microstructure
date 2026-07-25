#!/usr/bin/env python3
"""
Tests ONE principled, pre-registered hypothesis from forecast.html's own
documentation: "order-flow signals decay in seconds... they'd matter far
more on a 1-minute forecast than 15." Sweeps the forecast horizon (1/5/15
min) through the exact same walk-forward online-SGD pass as backtest_all.py
— same features, same LR/L2, same no-lookahead guarantee — changing only H.

This is NOT a grid search for whatever looks best after the fact. The bar
for "this horizon is a real improvement" is fixed BEFORE running, in code,
below (PASS_BAR) — not chosen by eyeballing results:
    1. overall_skill > 0            (actually beats random walk, not just
                                      "less negative than 15-min")
    2. hit-rate z-score >= 1.96     (directionally distinguishable from a
                                      coin flip at 95% confidence, given n)
    3. overall_net_bps > 0          (net of the same 60bps cost assumption
                                      used everywhere else in this account —
                                      significant ≠ tradeable, both must hold)
A horizon that fails any one of these is reported as "no improvement", full
stop — this script does not keep trying variants until something clears the
bar, because that IS the multiple-testing trap the rest of this account's
tooling exists to catch.

Does not modify backtest_all.py, learned_weights.json, or forecast.html —
read-only experiment. Run: /opt/anaconda3/bin/python horizon_sweep.py
"""
import math
import backtest_all as B

CANDIDATE_HORIZONS = [1, 5, 15]  # minutes; 15 = current live forecast.html value
PASS_BAR = dict(min_skill=0.0, min_hit_z=1.96, min_net_bps=0.0)


def hit_rate_z(hit_series):
    """z-score of the observed hit-rate against a 50% coin-flip null."""
    n = len(hit_series)
    if n == 0:
        return 0.0, 0
    phat = hit_series.mean()
    se = math.sqrt(0.5 * 0.5 / n)
    return (phat - 0.5) / se, n


def main():
    print('Loading data (shared across all horizons)...')
    df = B.load_all(B.os.path.join(B.HERE, 'data'))
    m = B.build_minute_series(df)
    print(f'{len(m):,} minute bars.\n')
    print(f'Pass bar (fixed before running): skill > {PASS_BAR["min_skill"]}, '
          f'hit-rate z >= {PASS_BAR["min_hit_z"]}, net_bps > {PASS_BAR["min_net_bps"]}\n')

    print(f'{"horizon":>9} {"n":>6} {"skill":>8} {"hit%":>7} {"hit_z":>7} {"net_bps":>9}  verdict')
    any_pass = False
    for h in CANDIDATE_HORIZONS:
        B.H = h  # backtest_all's run_online_pass reads the module-level H at call time
        w, results = B.run_online_pass(m, cost_bps=60.0)
        if results.empty:
            print(f'{h:>8}m {"(no resolved predictions)":>40}')
            continue

        skill = 1 - results['sq_err'].sum() / results['sq_base'].sum()
        z, n = hit_rate_z(results['hit'])
        net = results['net_bps'].mean()

        passed = (skill > PASS_BAR['min_skill'] and z >= PASS_BAR['min_hit_z']
                  and net > PASS_BAR['min_net_bps'])
        any_pass = any_pass or passed
        verdict = 'PASSES pre-set bar' if passed else 'no improvement'
        print(f'{h:>8}m {n:>6} {skill:>8.4f} {results["hit"].mean()*100:>6.1f}% '
              f'{z:>7.2f} {net:>9.2f}  {verdict}')

    print()
    if any_pass:
        print('At least one horizon cleared the pre-set bar — this is a real finding, '
              'worth a second look before touching the live model (out-of-sample re-check, '
              'not just this single pass).')
    else:
        print('VERDICT: no horizon in {1, 5, 15} min clears the pre-set bar. The documented '
              'hypothesis ("order-flow matters more at 1 min") does not hold up when actually '
              'tested — same honest-null pattern as everything else in this account. '
              'The live 15-min model in forecast.html is unchanged.')


if __name__ == '__main__':
    main()
