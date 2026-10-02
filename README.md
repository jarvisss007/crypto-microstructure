# Crypto Microstructure Lab

> ## STATUS 2026-10-02 — the 1/5/15-minute direction forecasters are RETIRED (CRYPTO-006)
>
> **Ruling.** Anupam, 2026-10-02 10:24 PT, "go ahead", adopting the recommended option (a) STOP.
> `ruled_by`: Anupam ('go ahead', 2026-10-02 10:24 PT), adopting the recommended option. Register row CRYPTO-006
> (`~/command-center/council/issues.json`).
>
> **The question is ANSWERED: no skill.** *Does a self-learning online model call the direction of the next 1, 5 or 15 minutes of
> BTC better than the base rate?* No. Precisely: the live forecasters were price-only (momentum and mean-reversion features; the
> order-flow and book-imbalance inputs are carried at zero in `minute_forecaster.py` and `horizon_forecaster.py`), so this answers
> that model, not the offline order-flow backtest (`research/NULL_RESULT.md`, untouched). The three books, frozen at the stop
> (crypto-minute at 12:11:20 PT, crypto-horizons at 12:17:53 PT):
>
> | horizon | scored (ties excluded) | UTC days | hit rate | up base rate | Brier | climatology | Brier skill | resolution |
> |---|---|---|---|---|---|---|---|---|
> | +1 min | 55,939 | 52 | 49.99% | 49.83% | 0.2534 | 0.2500 | -0.0135 | 0.0001 |
> | +5 min | 46,185 | 43 | 49.91% | 49.53% | 0.2593 | 0.2500 | -0.0374 | 0.0000 |
> | +15 min | 45,695 | 43 | 48.49% | 50.36% | 0.2727 | 0.2500 | -0.0908 | 0.0003 |
>
> 147,819 scored forecasts in all, the largest samples in the firm, and every Brier skill is below zero (worse than always
> saying the base rate) with resolution about 0: the forecasts carry no information about direction. Days are the
> denominator, not rows (`scoreboard.html` says so on every line); the verdict is the same read either way. Not answered here: the
> point-forecast (`pred_px`) question, which the ruling does not cover; `research/exact_minute_study.py` can still be run on the
> frozen books.
>
> **What was turned off.** The two always-on launchd jobs that wrote those books: `com.anupam.crypto-minute` (the 1-minute book)
> and `com.anupam.crypto-horizons` (the 5- and 15-minute books, and the scoreboard rebuild). Both were `launchctl bootout`-ed on 2026-10-02
> (crypto-minute at 12:11:20 PT, crypto-horizons at 12:17:53 PT), each in the quiet window right after a tick (the tick's last file 3 to 40 s old, no child process, the job
> asleep; the 5/15-minute job right after a scoreboard rebuild) so no write was cut short: every book re-parsed as a complete CSV
> with its exact header and was byte-unchanged across each kill. Their plists were then moved to
> `~/Library/LaunchAgents/retired/`.
>
> **What keeps running.** `com.anupam.crypto-collector` (the order-flow recorder: the tape), `com.anupam.crypto-rotate` (nightly
> minute files + archive) and the paper crypto desk `com.anupam.crypto-desk` (`~/crypto-desk`), which reads only the recorded tape
> and minute files, never these books.
>
> **The gap, counted (Firm Brain 24).** While the Mac was awake the forecasters filed about 1,000 to 1,400 rows per UTC day per
> horizon (the 1-minute book's observed range was 140 to 1,390 rows a day). None of that is written from now on, and nothing
> back-fills it.
>
> **What is frozen, exactly as recorded (BENCH-002).** The three books and their state files are history. Their bytes at the stop
> (sha256). The same pins are held by the `_crypto006_books_frozen` check in `PROPOSED_resolver_changes_CRYPTO-006.py` (proposed,
> not yet wired into `resolver.py`):
>
> | file | bytes | data rows | sha256 |
> |---|---|---|---|
> | `agent/minute_forecasts.csv` | 11,321,970 | 57,004 | `4878c4a97d389707181b51d7d52f18f6dbaf57d05bcbcfc80d581c1f758a695a` |
> | `agent/forecasts_5m.csv` | 9,436,742 | 46,618 | `5dd85b0b12272336d3823b605fd287c7fde0f883bf9ffff9563ce03b0536890c` |
> | `agent/forecasts_15m.csv` | 9,476,280 | 46,618 | `2d5b04632bbc35d3aa6368c1f76c99d6804bec466175435e4d4f19835287d605` |
> | `agent/minute_state.json` | 142 |  | `46c6958c63d8c6d632b51410187aac37c572330aec53e54329ae531330e5d9f4` |
> | `agent/state_5m.json` | 139 |  | `25b318bf16f9ba3123151a8983ceb4263bfb52418ce919de88bd0428ab9d3c49` |
> | `agent/state_15m.json` | 141 |  | `3e17978ce1aca2bdc8a8eae38714ca88ea1858ceabf4f6ad06cdb0276ef552d2` |
> | `~/Library/LaunchAgents/retired/com.anupam.crypto-minute.plist` | 641 | | `cad366ed6b58019304827635cdb8efd1271f4d5edb22b8a8fd3097033d75c406` |
> | `~/Library/LaunchAgents/retired/com.anupam.crypto-horizons.plist` | 649 | | `9c7410b8618c3efe0e7de5a2ab2e68738922d69c395955e7d15bac03d35cb495` |
>
> `scoreboard.json` / `scoreboard.html` are frozen at the last build (`built_utc` 2026-10-02T19:17:48Z), made by the 5/15-minute job after
> the 1-minute job had stopped and seconds before it stopped itself; they will not refresh. Rows filed in the last minutes before
> each stop never reached their target minute under a running scorer, so they stay unpriced (past due by construction, excluded
> from every score): the 1-minute book's last row, and the last few rows of the 5- and 15-minute books, which the frozen
> scoreboard still lists as `pending` (0 / 5 / 15 rows at +1 / +5 / +15 min) although none will ever resolve.
>
> **Restore** — only with Anupam's ruling. Reverses the stop; the roster, the retired markers and the resolver exemptions below go
> back with it, and the gap between the stop and a restart stays unforecast (a forecast is written before its minute; nothing back-fills).
>
> ```bash
> mv ~/Library/LaunchAgents/retired/com.anupam.crypto-minute.plist   ~/Library/LaunchAgents/
> mv ~/Library/LaunchAgents/retired/com.anupam.crypto-horizons.plist ~/Library/LaunchAgents/
> launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.anupam.crypto-minute.plist
> launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.anupam.crypto-horizons.plist
> launchctl list | grep -E 'crypto-(minute|horizons)'      # expect both, with a PID
> ```
>
> Then: (1) re-add `launchd:com.anupam.crypto-minute` and `launchd:com.anupam.crypto-horizons` to Garuda's `automations` in
> `~/command-center/council/roster.json` and delete their entries from its `retired` map (else `roster_names_every_automation` goes red); (2) empty the `RETIRED` dicts in
> `~/bin/score_forecasts.py` and `~/command-center/calibrate.py`; (3) drop the `_crypto006_` checks and the CRYPTO-006 exemptions
> from `resolver.py` if they were wired; (4) move `~/claude-config/launchd/retired/*.plist` back up one level; (5) revert the two RETIRED rows in
> `~/command-center/caretaker/agent_registry.md` and the Garuda row in `~/command-center/council/THE_COURT.md`.
>
> **Open consequence, not decided here.** The flow agent's standing daily forecast (`agent/AGENT.md`: "minute forecaster directional
> hit rate on <day> UTC scored rows exceeds ...") has no new rows to resolve against after 2026-10-02. Retiring or re-aiming it is
> Anupam's ruling; `agent/AGENT.md` was deliberately not edited.

A single-file, live crypto order-flow dashboard + data recorder. No backend, no
API key, no dependencies. Streams real trades and full order-book depth from
**Coinbase's public WebSocket** and computes microstructure metrics in real time.

## Folder map

- **`forecast.html`** — simple 15-min self-learning forecast (start here).
- **`index.html`** — the microstructure lab (order book, tape, order-flow metrics, recorder).
- **`research/`** — Python backtest harness that validates recorded CSVs (the honest gate:
  information coefficient, permutation p-value, cost-aware strategy backtest). See
  `research/README.md`.

## Two views

- **`forecast.html`** — the simple one. A 60-minute price chart plus a 15-minute-ahead
  **forecast cone**. Start here if you just want "where's price headed."
- **`index.html`** — the microstructure lab (order book, tape, order-flow metrics, recorder).

## Run it

Either:

- **Double-click a file** — opens in your browser, connects immediately
  (the Coinbase feed is `wss://`, which works from a local file).
- Or serve it: `python3 -m http.server 8777` in this folder, then open
  <http://localhost:8777/forecast.html> or `/index.html`.

## The self-learning 15-min forecast (`forecast.html`)

Gives an **approximate point price** for 15 minutes out (the gold "Approx price in 15 min"
card) and a probability **cone**, and it **learns online** from its own track record.

**How the learning works**
- Every minute it makes a real point forecast: `price_now × (1 + drift)`, where `drift`
  comes from an **online linear model** over standardized features — 1-min momentum,
  5-min momentum, 15-min mean-reversion, **plus live microstructure**: order-flow imbalance
  (buy vs sell volume, from Coinbase `matches`) and book imbalance (bid vs ask depth over the
  top 20 levels, from `level2_batch`). The order-flow features are captured live at prediction
  time and stored with the pending record, so scoring stays consistent across reloads.
- **Watch the weight bars** to see what the model actually leans on. Honest expectation: the
  order-flow weights stay near zero at a 15-min horizon — those signals decay in seconds, so
  they matter far more on a ~1-min forecast than 15 min out. If an order-flow weight grows and
  Skill turns positive, that's a real lead for a proper backtest.
- 15 minutes later it looks up the actual price (from Coinbase 1-min candles, so missed
  predictions are **backfilled on reload**), measures error, and updates the weights by
  gradient descent (`w ← w(1−LR·L2) − LR·(ẑ−z)·f`). LR=0.02, small L2 shrinkage.
- It keeps score vs the **random-walk baseline** (predict "no change") and persists
  weights + stats in `localStorage`, keyed per symbol — so it keeps learning across
  sessions. "Reset learning" wipes it for the selected market.

**Scoreboard**
- **Skill vs Random Walk** = `1 − MSE_model / MSE_baseline`. >0 means it's beating "no change".
- **Direction hit-rate** — % of forecasts that got the sign right (50% = coin flip).
- **Model MAE vs baseline MAE**, resolved count, live weight bars.

**The cone** is sized by recent volatility: per-minute return σ scaled √time
(σ₁₅ = σ_min·√15). Price lands in the **68%** band ~2/3 of the time, the **95%** band ~19/20.

**Honest expectation.** At a 15-min horizon returns are near-unpredictable, so the model
will most likely **learn to shrink its weights toward zero** and forecast ≈ current price —
i.e. it discovers there's no edge, and the scoreboard hovers around Skill≈0 / hit-rate≈50%.
That's the honest outcome and a genuine online-ML demo. If Skill goes meaningfully positive
over many resolved predictions, that's a real signal worth taking to a proper backtest —
**not** something to trade off directly.

Pick a market from the dropdown (BTC, ETH, SOL, XRP, DOGE — all vs USD).

## What it shows

| Panel | Metric | How it's computed |
|---|---|---|
| **Order book** | Top-15 bids/asks with depth bars | Local book maintained from Coinbase `level2_batch` (snapshot + incremental updates) — the same way a real trading system tracks a book |
| | Mid, spread (abs + bps) | From best bid/ask |
| | Book imbalance | bidVol / (bidVol + askVol) over top 15 levels |
| **Trade tape** | Live prints, colored by aggressor | Coinbase `matches`; trades > $25k notional highlighted |
| **Metrics** | Realized vol (annualized) | Std of 1-second log returns over trailing 60s, × √(31.5M s/yr) |
| | Order-flow imbalance | (buyVol − sellVol) / totalVol, trailing 60s |
| | Aggressor ratio | Buy-volume share, trailing 30s |
| | Trades/sec, vol/sec | Trailing-60s throughput |

Aggressor side is inferred from Coinbase's `match.side` field (which reports the
**maker's** side): a sell-side maker means the taker *bought* (lifted the ask).

## The recorder — your research dataset

Click **Start Recording** to log every trade and a 1-per-second book snapshot to
an in-browser buffer, then **Download CSV**. This is the point: it turns the live
feed into a dataset you can mine offline.

CSV schema (one file per session):

```
type, ts_ms, px_or_mid, qty_or_spread, extra1, extra2, extra3
trade, <epoch ms>, price, qty, isBuy(1/0), , 
book,  <epoch ms>, mid,   spread, bidVol,  askVol, bookImbalance
```

Load in pandas: `df = pd.read_csv('btc-usd_micro_....csv')`, then
`df[df.type=='trade']` for the tape and `df[df.type=='book']` for the book series.

## Honest note on trading edge

This is a **learning + data-collection tool, not a strategy.** Order-flow and
book-imbalance signals are real but heavily arbitraged at sub-second scale by
co-located players; on a retail WebSocket feed (~100ms+ latency) any edge is
usually gone by the time you see it. Seeing a signal ≠ having positive expectancy
after fees and slippage.

Correct workflow: **record data → mine for a candidate signal → validate it in a
proper backtest before risking a dollar** — the same discipline the `~/spy-trading`
verdict came from. Don't skip the backtest gate.

## Self-learning agent

`agent/` holds a self-calibrating flow agent (same pattern as `~/stock-radar`):
it reads the latest recorded session, and only when session order-flow imbalance
clears a fixed threshold logs one falsifiable next-day direction call to
`agent/ledger.csv`, scored the next day from Coinbase daily candles with no
excuses; blunt takeaways accumulate in `agent/lessons.md`. **Honesty note:**
calibration, not trades — no claim of edge; a coin-flip hit rate would confirm
this README's own expectation, and the ledger exists to find out. Procedure:
`agent/AGENT.md`.

## Why Coinbase

Binance.US trade streams are effectively dead (thin liquidity — 0 trades in
testing). Kraken's book is great but its tape is sparse (~3 trades / 13s).
Coinbase has real US-legal volume *and* a public `level2_batch` depth feed, so a
single venue powers every panel with no API key.


## The 1 / 5 / 15-minute scoreboard (2026-08-21) — RETIRED 2026-10-02 (CRYPTO-006), see the status block at the top

One instrument, three clocks. Every minute a row is frozen stating p(up) for the price 1, 5
and 15 minutes ahead; at the target minute the real last trade decides; direction obeyed =
right; rows are never edited; unchanged minutes are ties and excluded. The three books are
`agent/minute_forecasts.csv`, `agent/forecasts_5m.csv`, `agent/forecasts_15m.csv`; the
scoreboard is [`scoreboard.html`](scoreboard.html) (rebuilt every ~10 minutes by the running
job until the 2026-10-02 stop; now frozen at its last build) with per-horizon hit rate vs base rate, Brier skill and a reliability table, n and day
count said out loud. **Calibration instrument, barred from trading** — see
`research/NULL_RESULT.md` for why the only real short-horizon edge is ~1/1,183rd of the fee.


## How the tape is stored (2026-08-21)

The collector records every trade and a book snapshot per second (~50 MB/day raw). The
research runs on the 1-minute series it derives from that tape, so — like the stock desk —
the derived series is what we keep and the raw feed is a rolling buffer:

- `research/minutes/BTC-USD_<day>.csv` — nightly, per complete UTC day: the research's own
  minute series (`close`, `book_imb`, `ofi`, from `backtest_all.build_minute_series`) plus
  trades, volume, buy share, high, low. ~150 KB/day, tracked in git.
- `research/data/BTC-USD_<day>.csv.gz` — raw days older than today, gzipped (~5×) after a
  row-count check; the readers open `.gz` transparently. Kept 30 days locally.
- GitHub Releases `data-YYYY-MM` — each complete month's gz files, tarred, as a release
  asset (public Coinbase data). `research/archive_manifest.json` is the record; a local gz is
  pruned only after its month is in that manifest.

`research/rotate.py` does all four steps (launchd `com.anupam.crypto-rotate`, daily 00:40 UTC)
and never touches the day the collector is writing.
