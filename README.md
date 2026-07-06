# Crypto Microstructure Lab

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

## Why Coinbase

Binance.US trade streams are effectively dead (thin liquidity — 0 trades in
testing). Kraken's book is great but its tape is sparse (~3 trades / 13s).
Coinbase has real US-legal volume *and* a public `level2_batch` depth feed, so a
single venue powers every panel with no API key.
