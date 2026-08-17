# Short-horizon crypto direction is not forecastable from this desk's features — a null result

**Anupam Patil · Leo's Trading Firm · 2026-08-17 · status: concluded**

This is the writeup the build queue said was owed instead of more UI
("the headline finding is already converged — consider a short null-result
writeup"). It closes the question the lab was built to answer.

## Claim

An online linear model over price momentum, mean-reversion, order-flow imbalance
and book imbalance, learning by gradient descent and scored against a random-walk
baseline, shows **no forecasting skill for BTC-USD direction at the 1-minute or
15-minute horizon** — and its probabilities are mildly *anti-informative*:
writing 0.50 on every row would have scored better.

## Evidence, in declining order of weight

**Live 1-minute instrument** (the desk's largest sample, forecasts logged before
outcomes existed, scored automatically):

| | |
|---|---|
| resolved forecasts | **5,424** across 6 UTC days |
| direction hit rate | 50.17% vs 47.94% base — indistinguishable from a coin |
| Brier | 0.2539 vs 0.2500 climatology |
| **Brier skill** | **−0.0154, and negative on every single day** (−0.0075 · −0.0180 · −0.0093 · −0.0273 · …) |

Negative skill every day is the sharper statement than the pooled number: no
single lucky or unlucky session produced the verdict.

**Cumulative replay** of the identical algorithm over 38 days of continuously
recorded data: 53,311 predictions, skill −0.031, no edge found
(`research/learned_weights.json`, `backtest_all.py`).

**The 15-minute browser instrument**: the model's learned drift is ~$1–2 while
the 95% band spans ~$139 — the band is 100–200× the prediction. The honest
forecast at this horizon is the band, not the line.

## The one true positive, and why it is still a null

The 2026-08-12 horizon sweep found a real direction edge at 1 minute:
**+1.38pp over the base rate, z = 5.21**. It is worth roughly **1/1,183rd of the
retail taker fee** at Coinbase. A real signal that cannot survive its own costs
is a measurement, not a strategy — which is why the instrument was authorized as
a calibration device *explicitly barred from trading in its own law* (CRYP-002,
ruled 2026-08-12).

## Caveats, stated rather than buried

- 6 live days is 6 observations of market regime; the per-day negative-skill
  pattern is the defensible claim, not any pooled t-statistic (5,424 rows over
  6 days is a 791× row-to-day inflation; see `command-center/independence.py`).
- Features tested are simple and linear. This result convicts *these features at
  these horizons under these costs* — not market microstructure research at
  large. Order-flow information demonstrably exists at seconds; it decays before
  a 1-minute close can capture it at retail cost.
- One venue (Coinbase), one asset primarily (BTC-USD), no fee tiers below retail.

## What this desk does with a null

Keeps it. The instrument stays running as a calibration device — it produces
falsifications fast, which is worth more than a 55% hit rate on n=9 — and the
finding joins the estate's other honest nulls (0DTE r17, mean-reversion, AAII
sentiment, DC-ML). No further UI is owed on this question.

*Working paper convention: cite as Leo's Trading Firm null result #5, code and
data at the crypto-microstructure repo. Not advice; nothing here is a strategy.*
