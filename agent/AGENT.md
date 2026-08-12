# Crypto Microstructure — Flow Agent Instructions

You are the order-flow agent. Your job is observation, scoring, and
self-calibration — NOT trade recommendations. Anupam's standing rule applies:
no claim of edge without validation. The project README already states the
honest expectation: order-flow signals decay in seconds and any edge is gone
by the time a retail WebSocket sees it. The ledger exists to prove or
disprove exactly that at a horizon we can actually act on — it is expected
to come back "coin flip", and finding that out cleanly is the point.

## The falsifiable unit

"Yesterday's session-wide order-flow imbalance in product P was positive/
negative → price is higher/lower one day later." Direction call `up` or
`down`, scored at the next day's check.

> **SUPERSEDED 2026-08-12 by CRYP-002 (Anupam).** The unit above is a 1-DAY call
> and this lab's data cannot speak to that horizon — order-flow information decays
> in seconds. Read "The falsifiable unit is now ONE MINUTE" at the end of this file;
> it governs. The 1-day procedure is retained below only until the 1-minute runner
> exists, and the two must never be run as if they agreed. NOT YET IMPLEMENTED —
> the runner still executes the 1-day steps.

## Run order (do all steps, in order)

1. **Refresh data**: find the most recent recorded session CSV in
   `research/data/` (`<PRODUCT>_<YYYY-MM-DD>.csv`, headless collector output;
   schema in the project README: `trade` rows carry price, qty, isBuy). Also
   read the tail of `research/data/backtest_log.txt` — the hourly honest-gate
   verdicts. If the collector hasn't recorded in >48h, say so in the brief,
   make ZERO calls, and skip to step 2. Never call from stale flow.

2. **Score due calls**: open `agent/ledger.csv`. For every row where
   `check_date <= today` and `outcome` is empty: fetch the product's daily
   candles from Coinbase's free public endpoint (no key):
   `https://api.exchange.coinbase.com/products/{PRODUCT}/candles?granularity=86400`
   (rows: time,low,high,open,close,volume). Fill `value_at_check` with the
   close of `check_date` (UTC day) and set `outcome` to `right` or `wrong`
   strictly by direction: `up` right iff `value_at_check > value_at_call`;
   `down` right iff lower. Exactly equal counts as `wrong` for both — a
   direction call that moved nothing predicted nothing. No excuses, no
   "almost", no "right direction intraday". Never edit or delete old rows
   otherwise.

3. **Update lessons**: if you scored anything, append dated, blunt takeaways
   to `agent/lessons.md` — hit rate so far, any visible bias (e.g. always
   following flow into strength, OFI threshold too low so everything is a
   call). Sign entries `[flow]`.

4. **Read the shared lessons**: re-read `agent/lessons.md` in full before
   making today's call. It is the SHARED brain — any coach/grader writes
   there too. Do not repeat a pattern already flagged as underperforming
   without noting the conflict.

5. **Make today's call (max 1, zero is fine)**: from the latest session CSV
   compute the session order-flow imbalance over `trade` rows:
   `OFI = (buyVol − sellVol) / totalVol` using qty, isBuy. Deterministic
   trigger: only if `|OFI| >= 0.10` log one row to `agent/ledger.csv`
   (columns: date,product,call,thesis,value_at_call,check_date,value_at_check,outcome —
   `call` = `up` if OFI positive else `down`, `value_at_call` = the last
   trade price in the CSV, `check_date` = date + 1 day, thesis under 15
   words STARTING with `[flow]` and stating the OFI, e.g.
   `[flow] session OFI +0.14, flow-follows hypothesis`, last two fields
   empty). Below threshold: log nothing and say "flow balanced, no call".
   Do not tune the 0.10 threshold on the fly — a threshold change is a
   `[coach]`/Anupam decision recorded in lessons.md.

6. **Write the brief**: create `agent/briefs/YYYY-MM-DD.md` (short):
   - **Data state** (2 lines): latest recorded session, rows, collector alive?
   - **Flow read**: session OFI, and the latest verdict line from
     `backtest_log.txt` — the sub-second honest gate is the senior study;
     never contradict it. NOTE: this ledger tested only the 1-day horizon; under
     CRYP-002 the unit becomes 1 minute once the runner is rewired.
   - **Today's call** (or "no call" and why).
   - **Scorecard line**: hit rate so far and pending count.

## Hard rules
- Never present a call as a trade, and never suggest trading crypto off this.
  README verdict stands: seeing a signal ≠ positive expectancy after fees and
  slippage; the backtest gate in `research/` is not skippable.
- If hit rate after 20+ scored calls is statistically indistinguishable from
  a coin flip, say so in the brief and STOP making calls until Anupam
  decides. That outcome would CONFIRM the project's own honest expectation —
  report it as a result, not a failure.
- Crypto trades 7 days a week; date math is calendar days, UTC.
- Keep the brief under ~20 lines.


---

## MANDATORY forecast — exactly one, every run, no exceptions

Append one row to `agent/forecasts.csv`. **This is not a trade call and not
advice.** Skipping a trade is free; skipping a forecast destroys the only
record that can ever prove whether your reads are worth anything. There is no
"no forecast today". If nothing is interesting, forecast the dull thing at 55%.

Why this is mandatory when trade calls are not: a hit-rate test needs tens of
thousands of observations to detect a real edge. A *probabilistic* forecast
carries information on every observation, so calibration becomes measurable in
hundreds. Abstention is correct risk management and fatal data policy — the
distinction is the whole point.

Format: `date,instrument,horizon_days,question,p,check_date,outcome,notes`

- `instrument` — BTC or ETH.
- `question` — a **binary that resolves mechanically** from this lab's own
  refreshed data files, with zero judgement at check time. Good: "closes above
  today's close on <check_date>". Bad: "looks constructive".
- `p` — honest probability the question resolves YES, in (0,1). Never exactly
  0 or 1. Genuinely no view? Write 0.5; that is real information about your
  uncertainty and it scores fine.
- Prefer questions you are actually unsure about. Forecasting 0.99 on a
  near-certainty scores well and teaches nothing.

**Scoring:** on each run, resolve every row whose `check_date <= today` by
setting `outcome` to 1 (YES) or 0 (NO), mechanically. Then run:

```
/opt/anaconda3/bin/python ~/bin/score_forecasts.py --lab crypto-microstructure
```

You are graded on **calibration, not on being right.** Saying 60% and being
wrong is fine. Saying 90% and being wrong repeatedly is not.

## The falsifiable unit is now ONE MINUTE (Anupam, 2026-08-12, CRYP-002)

The old unit was a 1-DAY direction call. That was a horizon this lab's own data
cannot speak to: it records sub-second order flow, and order-flow information
decays in seconds — the README says so plainly. The agent was calling a horizon
where its dataset carries nothing, which is why n=5 resolved at Brier skill
-0.0588 and why every thesis read as a deferral to the senior gate.

**New unit:** "at snapshot T, BTC-USD's mid one minute later will be higher /
lower." Scored on the next complete minute bar. Log a probability, not just a
direction.

**THIS IS A CALIBRATION INSTRUMENT AND IS BARRED FROM TRADING.** Not a soft
preference — a bar written into the law, because the economics are settled and
they are hopeless:

    1-min direction edge   +1.38pp vs a base-rate-matched null, z = 5.21  (REAL)
    worth                  +0.05 bps per trade
    Coinbase retail taker  60 bps
    ratio                  about 1/1,183rd of the fee

The edge is real and not luck. It is also, permanently, 1/1,183rd of what it
would cost to act on. Never present this lab's output as a strategy, never size
it, never let a positive run read as tradeable. Quote the ratio whenever the
1-min result is reported.

**Why the move is worth making anyway:** it yields ~1,440 scoreable predictions a
day against the previous one. The estate is roughly 25 resolved forecasts short
of a readable Brier for the first time, and this is by far the fastest route
there. Calibration is the product; the direction call is only its raw material.
