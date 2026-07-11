# Research — backtest harness

The honest validation gate for the Microstructure Lab. Before any signal counts as an
"edge", it has to pass here: predict forward returns better than chance **and** survive
transaction costs.

## Automatic mode (headless — no browser)

`collector.py` connects straight to Coinbase, records trades + 1/sec book snapshots to a
dated CSV, and **auto-runs the backtest every hour**, appending each verdict to
`data/backtest_log.txt`. This is the hands-off pipeline.

```
./run.sh --max-hours 72  # run 3 days, then AUTO-STOP + write a final summary (recommended)
./run.sh                 # run until stopped (BTC-USD, hourly backtest, 60 bps cost)
./run.sh --product ETH-USD --backtest-every 1800
tail -f data/collector.log        # watch it live
cat data/backtest_log.txt         # read accumulated verdicts (+ AUTO-STOP summary at the end)
./stop.sh                # stop it early
```

**Automation:** `--max-hours N` makes it self-terminate after N hours — it runs one final
backtest, appends an `AUTO-STOP` summary to `backtest_log.txt`, and exits cleanly. So you can
"fire and forget": start it, walk away, come back to a finished dataset + verdict. (It pauses
while the Mac sleeps and won't survive a reboot — restart if that happens.)

- Data lands in `data/<PRODUCT>_<YYYY-MM-DD>.csv` (rotates daily).
- **Start at login (optional, survives reboot):** see `com.anupam.crypto-collector.plist`
  for the two `launchctl` commands to enable/disable.
- It's a lightweight 24/7 WebSocket process — minor battery/network use. `./stop.sh` anytime.

## Manual workflow (browser recorder)

1. Open `../index.html`, click **Start Recording**, let it run (longer = better; aim for
   hours, not minutes), click **Stop**, then **Download CSV**.
2. Move the CSV into this folder (or point at it directly).
3. Run:
   ```
   /opt/anaconda3/bin/python backtest.py YOUR_RECORDING.csv
   ```
   Options: `--horizons 5,15,30,60` (seconds), `--ofi-window 10`, `--cost-bps 60`,
   `--permutations 500`.

## Cumulative backtest — validating the *live* forecast.html model itself

`backtest.py` grades raw signals (OFI, book imbalance) one day at a time. `backtest_all.py`
is different: it replays **forecast.html's actual online-learning algorithm** — identical
features, identical SGD update rule — over *every* recorded day in chronological order.
Because online SGD only ever updates from pairs resolved strictly in the past, this single
sequential pass is walk-forward / out-of-sample at every prediction by construction — no
train/test split bookkeeping needed.

```
/opt/anaconda3/bin/python backtest_all.py --cost-bps 60
```

Writes `research/learned_weights.json` (small, **git-tracked** — unlike `data/`, this one
publishes to GitHub Pages) with the fully-trained weight vector plus per-day and overall
skill/hit-rate/net-bps. `forecast.html` fetches this on any genuinely fresh session (nothing
learned locally yet, BTC-USD only) and **warm-starts** from it instead of zero — so a brand
new browser tab benefits from every day the 24/7 collector has recorded, instead of starting
blind. A scheduled task (`crypto-cumulative-backtest`) reruns this daily as more data lands.

**A real finding from the first week of continuous data (2026-07-05 → 07-11, 8,079 resolved
15-min predictions):** the original `LR=0.02` did NOT reliably shrink toward zero as the
README's own honest-expectation section predicted — it let the model wander into a
confidently *wrong* state (skill **-0.60** vs random walk, some days under 30% hit-rate).
Testing `LR=0.002` (10× lower) tracked the intended "no edge" behavior far more faithfully
(skill **-0.03**, much closer to the honest null). **Fixed in both `backtest_all.py` and
`forecast.html`** — this wasn't a fabricated edge, it was the safety mechanism itself not
holding up under continuous real-world operation. Stronger L2 alone (tested up to 150×)
barely helped; the learning rate was the actual lever.

## What it reports (per signal × horizon)

| Column | Meaning |
|---|---|
| **IC** | Spearman rank correlation between the signal and the forward return. Higher \|IC\| = more predictive. |
| **p-val** | Permutation-test p-value — probability of an IC this large from a *shuffled* (meaningless) signal. `< 0.05` = a real association, not chance. |
| **gross** | Mean per-trade return before costs (bps). |
| **net** | gross − `cost-bps`. This is what you'd actually keep. |
| **hit%** | Share of trades that were profitable (gross). |
| **Sharpe** | Annualized Sharpe of the net per-trade series. |
| **N** | Number of non-overlapping trades tested. |

Flags: `*` = statistically significant association; `**` = significant **and** net-positive.

## Why there's a sample generator

`make_sample.py` writes two files:
- `sample_random.csv` — pure noise → the harness must find **nothing**.
- `sample_planted.csv` — order-flow genuinely predicts the next return → the harness must
  **detect** it.

A backtester you can't trust is worse than none: if it misses a planted edge it's blind; if
it "finds" edge in noise it's a liar. Regenerate and check anytime:
```
/opt/anaconda3/bin/python make_sample.py
/opt/anaconda3/bin/python backtest.py sample_planted.csv   # expect ** flags
/opt/anaconda3/bin/python backtest.py sample_random.csv    # expect no flags
```

## The lesson baked into the output

On the *planted* file at realistic Coinbase retail taker cost (`--cost-bps 60`), even a
strong signal (IC 0.5–0.7) survives at only **one** horizon (~15s) and barely — the 5-second
version has the best IC but trades so often that fees bleed it deeply negative. Takeaways:

- **Significance ≠ profit.** A real, significant signal can still lose money after costs.
- **Trade frequency is a cost multiplier.** Faster signals pay more fees.
- On real recordings, expect the *honest* verdict: no net-positive edge. That is not a
  failure — it's the same finding as `~/spy-trading`. Only promote a signal to real money if
  it clears costs on **multiple, out-of-sample** recordings.
