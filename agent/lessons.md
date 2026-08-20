# Lessons — the flow agent's self-calibration log

2026-07-15: File created. The agent appends dated, blunt takeaways here after
scoring its own direction calls in `ledger.csv`, and must re-read this file in
full before every brief. This is the SHARED brain — every agent or coach that
writes here signs its entries with a tag (`[flow]`, `[coach]`, ...).
Empty sections mean no scored history yet — earn the opinions.

## Standing priors (set at file creation, 2026-07-15)
- [flow] Default assumption: my direction calls are noise until the ledger
  proves otherwise. The project's own README predicts order-flow signals are
  arbitraged away before a retail feed sees them — a ~50% hit rate here would
  CONFIRM the house view, and that is a valid result.
- [flow] The `research/` backtest gate (IC, permutation p-value, cost-aware
  backtest) is the senior study. This ledger only probes the 1-day horizon;
  it never overrides a backtest_log.txt verdict.
- [flow] OFI call threshold is fixed at |OFI| >= 0.10. Changing it mid-stream
  is curve-fitting; any change gets recorded here as a signed decision.

## Scored-call takeaways
(none yet)

## Process lessons
(none yet)

## 2026-07-31 — first scored call
- [flow] 1/1 right (100%, n=1). BTC-USD `down` from OFI −0.17 on 2026-07-26;
  07-27 close 63694.43 vs 65347.92 call price. One call is NOTHING — n=1 is a
  coin that landed heads. No inference permitted, and the standing prior
  (calls are noise until proven otherwise) is untouched.
- [flow] Process failure worth recording: this row sat unscored for 4 days
  (2026-07-27 → 2026-07-31) because the sweep did not fire while the Mac slept,
  and no calls were logged 07-27 through 07-30 despite the collector recording
  every one of those sessions. Missed calls are missing data, not neutral —
  a ledger that only logs on days the laptop was awake is a biased sample.
- [flow] Today's logging convention, recorded so it is not silently changed:
  OFI is computed from the last COMPLETE UTC session (07-30), while
  `value_at_call` is the price at logging time from the in-progress file. Using
  the partial day's own close would leak 8 hours of already-known move into
  the call. Threshold stays fixed at |OFI| >= 0.10.

## 2026-08-03 — second scored call, and the coin landed tails
- [flow] 1/2 (50%, n=2). BTC-USD `up` from OFI +0.20 logged 07-31 at 63834.93;
  08-01 UTC close 62764.20 — lower, so WRONG. Exactly the shape the standing
  prior predicts: the flow-follows hypothesis is 1-for-1 in each direction and
  is currently a coin flip, which is what the project expects to find.
- [flow] Note the symmetry worth watching: the `down` call from OFI −0.17 was
  right and the `up` call from OFI +0.20 was wrong. If a directional asymmetry
  is real it will take dozens of calls to see; naming it now would be exactly
  the pattern-invention this ledger exists to catch. Recording it as a thing to
  check later, not as a finding.
- [flow] COLLECTOR OUTAGE: trade data stops at 2026-08-03 04:55 UTC and does
  not resume until 2026-08-04 03:18 UTC — a ~22.4-hour hole. Today's file is a
  16-minute stub (4,857 trades). Its OFI is +0.18, above the 0.10 threshold,
  and it was NOT used: the falsifiable unit is a session-wide imbalance, and
  16 minutes of tape dressed up as a session would be a fabricated call. The
  threshold stays fixed; the fix is the collector, not the rule.
- [flow] Last two COMPLETE sessions: 08-01 OFI −0.0706 (298,423 trades, full
  24h), 08-02 OFI −0.0660 (90,883 trades, 21.9h — truncated by the outage).
  Both below threshold, so no call today on the honest reading either.

## 2026-08-04 — nothing scored, collector partly recovered
- [flow] No rows came due (both ledger rows closed 08-01/07-27). Abstention
  logged against a named bar per the council rule: |OFI| on the last complete
  session is 0.024 versus the fixed 0.10 trigger. No call.
- [flow] The 08-03 outage flagged yesterday is now measurable in full. The
  `BTC-USD_2026-08-03.csv` session spans only 03:18-06:59 UTC on 08-04 —
  **3.7 of 24 hours, ~20.3h lost**. The collector has since recovered (08-04 is
  writing normally, ~20.8h and 90,619 trades so far), so this is a bounded
  outage rather than a dead recorder. Per the council's flag-don't-work-around
  rule, the 08-03 session is recorded as unusable and is not being treated as a
  session-wide imbalance no matter what its OFI reads.
- [flow] Sign instability worth noting only as noise: 08-03 reads -0.024 and
  the in-progress 08-04 reads +0.061. Two sub-threshold numbers flipping sign
  is what no-signal looks like; it is not a turn in flow and is not being
  narrated as one.
- [flow] Today's auto-backtest keeps reproducing the null cleanly, and the
  detail is worth carrying: `book_imb` has a genuinely *significant*
  association (IC 0.191 at 5s, p=0.002) and it is still net ~-60 bps, because
  gross is ~0.08 bps against 60 bps of cost. That is the single best
  illustration this lab has of why statistical significance and edge are
  different things. A signal can be real and worthless at the same time.

2026-08-05 [flow] — Nothing scored (ledger 0 pending; forecasts check 08-06 and 08-08).
Abstention logged against the named 0.10 OFI bar: last COMPLETE session (08-04) OFI
+0.0644, below threshold, no call.

RECORDING THE TEMPTATION, BECAUSE IT WAS REAL. Two OFI numbers were available this run:
the complete 08-04 session at +0.0644 (no call) and the in-progress 08-05 session at
+0.1217 (clears the bar). Choosing the second would have been threshold-fishing by the
back door — not tuning the 0.10 number, which AGENT.md explicitly forbids, but quietly
changing the WINDOW the number is computed over until one of them crosses. Same violation,
harder to spot in a diff. Rule for future runs: the window is the last COMPLETE session,
full stop, and if two candidate windows disagree that fact goes in the brief rather than
being resolved in favour of a call.

FOUND A MISALIGNMENT IN THE FALSIFIABLE UNIT ITSELF. `BTC-USD_2026-08-04.csv` spans
07:00 UTC to 06:59 UTC the next day. The collector names files by LOCAL date
(research/collector.py `_ensure_file`, timestamps from `time.time()`), so a "session" file
is a PDT day. But AGENT.md specifies UTC calendar days for date math, and step 2 scores
against Coinbase UTC daily candles. So the OFI window is offset ~7 hours from the return
window it is supposed to predict: roughly a third of the flow being measured happens
during the return period rather than before it. At n=2 this has not cost anything yet, but
it is a lookahead leak baked into the unit, and it would flatter the flow-follows
hypothesis rather than hurt it. Needs an `[anupam]`/`[coach]` decision — either the
collector rolls files at UTC midnight, or scoring uses PDT-day returns. Do not paper over
it by continuing to log calls as if the windows lined up.

Third, on forecast design: the previous two forecast rows both used a completed daily
close as reference and were written mid-session, which imports a few hours of known tape.
Today's row is framed as "08-06 UTC close above 08-05 UTC close" — both endpoints unknown
at write time — so it is uncontaminated, and it happens to test the ledger's actual 1-day
flow-follows hypothesis rather than a drift prior. Cheap fix, worth keeping.

Unchanged and worth restating: the hourly honest gate re-ran at 08:15 with 145,237 trades
and again returned no net-positive signal at any horizon after 60bps, with real
associations (ofi IC 0.089 at 5s, p=0.002) that die entirely on costs. Association is not
edge. This ledger tests only whether anything survives to a 1-day horizon; it does not get
to overrule that.

2026-08-06 [flow] — Nothing scored. Both existing ledger rows closed long ago (1/2, and
n=2 is not a hit rate). One new call logged: the 08-05 session OFI came in at +0.1247,
which clears the 0.10 trigger, so `up` on BTC-USD, value_at_call 64,796.79, checks 08-07.
The threshold fired mechanically and I did not touch it.

Two findings, and the first one is a defect in this lab's own falsifiable unit.

(1) THE SESSION FILES ARE NOT UTC DAYS, AND THE LEDGER SCORES THEM AS IF THEY WERE.
Checked the timestamps directly instead of trusting the filename: every
`BTC-USD_<date>.csv` spans **07:00 UTC → 06:59 UTC the next day**. That is a local
midnight-to-midnight PDT day, not a UTC day. AGENT.md then says `value_at_call` = the last
trade price in that CSV — a **06:59 UTC** print — while step 2 scores `value_at_check`
off Coinbase's **UTC daily candle**, which closes at 00:00 UTC. So every row in this ledger
compares a price taken at 06:59 UTC against a close taken at 00:00 UTC: a seven-hour
mismatch baked into the unit. On a 1-day direction call, seven hours is not a rounding
error. Both prior rows (07-26 right, 07-31 wrong) carry it. I logged today's row to the
existing spec anyway rather than silently redefining the unit mid-stream — per AGENT.md,
a rule change is a [coach]/Anupam decision. Flagging it for that decision. The clean fix is
to take `value_at_call` from the same Coinbase daily-candle series used for scoring, so
both endpoints come from one clock.

(2) DID NOT RESOLVE TWO DUE FORECASTS, ON PURPOSE. The 08-03 and 08-05 rows both check
2026-08-06 and both need the **08-06 UTC daily close**. This run fired at 15:33 UTC — the
UTC day has ~8.5 hours left. Coinbase does return an 08-06 candle, and its `close` field
reads 64,782.39, which is exactly the trap: volume on that candle is 2,948.8 against
6,227-7,086 on the last four complete days, so the field is a live price wearing a close's
name. Marking those rows 1/0 off it would have been the same class of error the council
has now logged three times on this desk. Both rows carry a dated deferral note and resolve
on the next run off the completed candle. Nothing is lost; the alternative was a fabricated
observation in the only record this lab is graded on.

Senior study unchanged, and it re-ran today at 08:11 on 35,556 trades: **no signal is
net-positive after costs at any horizon**. Best net was -59.83 bps at 60s. OFI's IC decays
from 0.066 at 5s to 0.008 (p=0.176, not significant) at 60s — the association is real and
gone within a minute, which is the README's expectation stated in numbers. The 1-day
ledger is testing a different horizon and must never be read as contradicting that.

2026-08-07 [flow] — Two forecasts RESOLVED (the pair deferred yesterday), one new
ledger call logged, one ledger row correctly left pending. Brier 0.2550, skill
-0.0202 at n=2 — no skill vs base rate, and at n=2 that number means nothing.

(1) YESTERDAY'S DEFERRAL CHANGED AN ANSWER, and this is the strongest evidence this
desk has produced for the "never score off a live candle" rule. The 08-05 row asked
whether BTC's 08-06 UTC close beat its 08-05 close (64,603.03). Yesterday the LIVE
08-06 candle read 64,782.39 — that resolves YES. The SETTLED 08-06 close is
64,267.30 — that resolves NO. Scoring one run early would have written a 1 where the
truth is a 0, into the only record this lab is graded on, permanently and invisibly.
The other deferred row (08-03, threshold 63,466.51) resolved YES either way, so the
error rate on live-candle scoring here was 1 in 2. Previous entries argued the rule
from principle; this one has the counterfactual. Note the settled 08-06 volume is
4,520 vs 6,227-7,086 on 08-03/04/05 — a genuinely quiet day, not an incomplete one
(08-02 closed complete at 3,284), so low volume alone is not the completeness test.
Elapsed time is.

(2) TODAY'S LEDGER ROW IS PENDING FOR THE SAME REASON, not by oversight. The 08-06
row checks 2026-08-07 and needs the 08-07 UTC close; the run fired 15:33 UTC with
~8.5 hours of the UTC day left, and the live candle reads 65,033.30 on 3,428 volume.
It resolves on the next run off the completed candle. Recording this so a future run
does not read the skipped resolution as a missed one — the catch-up rule will take it.

(3) THE CLOCK-MISMATCH DEFECT IS UNCHANGED AND NOW HAS A THIRD ROW RIDING ON IT.
Today's call takes `value_at_call` = 64,254.40, the last trade in the 08-06 session
CSV, which is a ~06:59 UTC print; step 2 will score it against a 00:00 UTC daily
close. Same seven-hour mismatch flagged on 08-06. Logged to the existing spec again
rather than silently redefining the unit — that remains a [coach]/Anupam decision —
but three of four rows in this ledger now carry it, and the fix is unchanged: take
both endpoints from the Coinbase daily-candle series so one clock governs.

Senior study unchanged: re-ran today, VERDICT no signal net-positive after costs at
any horizon. The 1-day ledger tests a different horizon and never overrules it.

2026-08-10 [flow] — Scored 2 overdue ledger rows (both `right`) and resolved 2
overdue forecasts (both YES). Running ledger record 3/1 = 75%, n=4, 0 pending. No
new call: 08-09 session OFI +0.0939, below the 0.10 trigger.
Four findings:
(1) THE CATCH-UP RULE JUST PAID FOR ITSELF, TWICE OVER. Four rows were sitting
overdue — the 08-06 and 08-07 ledger calls (check 08-07 and 08-08) and the 08-04
and 08-06 forecasts (both check 08-08) — because crypto trades 7 days a week while
this sweep runs weekdays only. Every weekend will silently strand two days of
scoreable rows in this lab specifically. That is a structural property of a
7-day market on a 5-day scoring schedule, not an incident, and it is the one lab
where "score everything due or overdue" is load-bearing rather than a safety net.
(2) 75% AT n=4 IS NOISE AND I AM WRITING IT DOWN BEFORE ANYONE QUOTES IT. A fair
coin produces 3-or-better out of 4 about 31% of the time. Both today's wins came
from calls following buy-heavy flow into a market that drifted up anyway, which is
the `up`-bias the lab should be watching for: 3 of the 4 closed calls were `up`.
The AGENT.md bar is 20+ scored calls, the senior sub-second study already says any
association here is arbitraged away, and nothing in a 4-row sample touches either.
(3) THE THRESHOLD HELD UNDER GENUINE TEMPTATION. +0.0939 rounds to +0.09, sits 6%
short of the trigger, and would have been trivially reportable as "+0.10, call
logged". It is not logged. Recording the near-miss explicitly so a future run sees
that the boundary was tested and respected rather than quietly moved — a threshold
that only binds when it is far away is not a threshold.
(4) TWO DATA CAVEATS WORTH KNOWING BEFORE ANYONE TRUSTS THE OFI NUMBER. First, the
session files are NOT UTC-aligned: the 08-09 file spans 07:46 UTC to 06:59 UTC the
following day, i.e. the collector's day starts around 07:00 UTC. The ledger scores
against UTC daily closes, so the flow window and the scoring window are offset by
~7 hours. Second, the CSV schema is POSITIONAL (type,ts_ms,px_or_mid,qty_or_spread,
extra1,extra2,extra3) with isBuy living in `extra1` — AGENT.md's "trade rows carry
price, qty, isBuy" reads like named columns and a literal reading returns zero
trades and an undefined OFI. Both are documentation defects, not data defects.

2026-08-11 [flow] — Scored 1 overdue forecast (the 08-07 BTC row deliberately left
pending on 08-10 because the UTC day had not closed): 08-10 settled at 63,911.88
against the 08-07 close 64,891.61 -> lower -> NO, outcome 0. Forecast record 5
resolved, Brier skill **-0.0588, no skill vs base rate**, reliability 0.0085 on
n=5 — which is exactly the honest expectation and not a number to react to.
Ledger: no call. Deterministic no-trigger, not a judgement call.
Two findings.
(1) LEAVING THE ROW PENDING ON 08-10 WAS RIGHT, AND TODAY PROVES THE COST OF
GETTING IT WRONG WAS ZERO. The 08-10 run could see the in-progress candle at
64,322.57 and could have resolved NO a day early with the same verdict. It didn't,
and the settled close came in 410 points lower at 63,911.88 — same answer,
different number. The verdict was never in doubt; the discipline is that "the
in-progress candle already says NO" and "the candle closed NO" are different
claims, and only one of them is a resolution. Recording this because the temptation
recurs every time a check_date equals the run date in a 7-day market.
(2) THE INCOMPLETE SESSION CLEARS THE TRIGGER AND THE COMPLETE ONE DOES NOT — THE
CLEANEST THRESHOLD-SHOPPING TRAP THIS LAB HAS SEEN. Latest COMPLETE session 08-10
(333,851 trades, 07:00 UTC -> 06:59 UTC next day) ran **OFI -0.0805**, below the
0.10 trigger, so no call. The in-progress 08-11 file (138,044 trades, 8.6 of 24
hours) runs **OFI -0.1564**, which clears the trigger comfortably and would have
produced a tidy `down` call. Using it would have been wrong twice over: it is a
partial window, and picking the window that fires the trigger is the definition of
tuning a threshold on the fly, which AGENT.md reserves for a [coach]/Anupam
decision. Logged explicitly so a future run sees that the two numbers were both
computed and the complete one was the one that counted. The 07:00 UTC session
boundary noted on 08-10 still stands and is visible in the span above.

## 2026-08-12 [flow]
First run since CRYP-002 with the minute forecaster actually live. 91 minute
forecasts resolved today; the 1-day ledger has no open rows left and is closed.

(1) THE MINUTE UNIT IS PRODUCING DATA AND ITS FIRST NUMBER IS A COIN FLIP.
n=91 resolved, **46 right / 45 wrong = 50.5%**, up-rate 0.473, Brier 0.2533 against
a climatology of 0.2492 — **Brier skill -0.0162**. Negative, i.e. worse than just
predicting the base rate, and at n=91 that is noise, not a verdict. What matters is
that it took ONE morning to get 91 resolved observations; the old 1-day unit took
17 days to get 5. CRYP-002's entire justification was throughput and the throughput
is real.
(2) THE FORECASTER'S PROBABILITIES ARE ALMOST FLAT AND THAT IS THE HONEST SHAPE.
p_up spans 0.4145-0.5478 with a mean of 0.4846 — it never claims more than a 5pp
tilt off the coin. Given the standing economics (edge worth +0.05 bps against a
60 bps taker fee, about 1/1,183rd of the cost), a model that stayed near 0.5 is
the correct-looking model. Any future run where p_up starts printing 0.7s should
be treated as a bug before it is treated as a discovery.
(3) THE LOOP HAD A 335-MINUTE HOLE THIS MORNING AND IT WAS NOT A FAILURE.
Forecasts run 08:25 UTC (one row, written when the script was built at 01:25 PDT),
then nothing until 14:01 UTC, then continuously ~1/minute to 15:30. The gap is the
window before `crypto-minute.sh` was actually launched — PID 19507 started 07:01
PDT and has held since. Recording it so a future reader does not diagnose a dead
loop from the gap. What IS worth watching: at ~1,440 possible minutes a day the
lab is currently capturing whatever fraction the loop is up for, and the honest
denominator for any future rate is minutes-loop-was-alive, not minutes-in-the-day.
(4) TODAY'S FLOW WOULD HAVE TRIGGERED A RETIRED CALL. Partial UTC session OFI is
**-0.163** on 168,988 trade rows, sell-heavy and past the old 0.10 threshold — under
the retired procedure that is an automatic `down` row. Not logged. The horizon was
retired because this lab's data cannot speak to it, and the first session where the
old rule would have fired is exactly the session to prove the retirement is real
rather than nominal.
(5) THE COUNCIL'S TAG-INTO-LEDGER FIX HAS NOWHERE TO LAND HERE. The directive is
that `[flow] [tech]` must reach `ledger.csv` because the Observatory reads that
file. This lab's `ledger.csv` is now CLOSED — 4 rows, all scored, unit retired — so
there will never be another row to carry the tag. The live record is
`minute_forecasts.csv` plus `forecasts.csv`. Whatever the Observatory reads for
this lab needs to point somewhere other than a retired file.

## 2026-08-13 [flow] The minute forecaster is readable at last, and it says nothing

Three findings, one of them the most important number this lab has produced.

(1) 1,120 RESOLVED MINUTE FORECASTS, BRIER SKILL -0.0122, HIT RATE 0.4991. CRYP-002 was
adopted on 08-12 to get the estate to a readable n fast, and it worked — two days later
this lab has more resolved forecasts than every other lab combined by two orders of
magnitude. The answer is a coin flip. Base rate 0.5054, Brier 0.2530 against climatology
0.2500. **AGENT.md's +1.38pp / z=5.21 direction edge does not reproduce in forward
prediction.** That is not a contradiction to explain away: the claimed edge came from a
research study, and the forward book is the test, and the test says no. Report it as a
result, which is exactly what the README expected. The 1/1,183rd-of-fee ratio is quoted
anyway and is now doubly moot — an edge of zero is untradeable at any fee.

(2) THE LOOP IS HUNG, AND IT IS THE FAILURE MODE launchd CANNOT SEE. Last row targets
2026-08-14T00:00 UTC (17:00 PDT); the run at 03:25 UTC found nothing written for ~3.4
hours, and a 75-second watch showed the file flat. PID 19507 is alive and
`com.anupam.crypto-minute` shows status 0, so every liveness check the desk has says
healthy. `crypto-minute.sh` deliberately removed its pgrep guard because "singleton is
launchd's job" — correct, but launchd only guarantees ONE instance, never a WORKING one.
At ~200 forecasts/hour this is the estate's fastest route to a readable Brier, and it
has been silently off since 17:00. Needs a heartbeat check (row count advancing), not a
process check.

(3) THE SETTLED-BAR DISCIPLINE HELD AGAIN. Coinbase's candles endpoint returns the
in-progress 08-14 bar (63,504) first; the 08-10 forecast was resolved off the DATED
08-13 close (63,425.35) -> NO. This is the third consecutive run where the ordering of
that endpoint would have flipped or fudged a verdict if read carelessly.

Daily book now 6 resolved, Brier skill -0.0007 — also no skill, and honestly so. Today's
new row is ETH, not BTC: all 8 prior rows were BTC, so each additional BTC row is close
to a repeat draw on one asset. Instrument diversity, not a view on ETH.

**Same-run update [flow]:** `launchctl kickstart -k gui/501/com.anupam.crypto-minute` restarted
the hung loop at 20:36 PDT. New PID, and rows resumed immediately (target 2026-08-14T03:37 UTC
written within a minute). So the process was wedged, not blocked on the exchange — a restart
clears it. That makes the fix a heartbeat watchdog: if the last row's target minute is more
than ~3 minutes old, kickstart. Roughly 3.5 hours (~200 forecasts) were lost tonight before
anyone looked.

## 2026-08-14 [flow] The minute book is now large enough to argue with CRYP-002's own headline number

Nothing was due in either the retired 1-day ledger (4 rows, closed) or the daily
forecast book. The minute book, however, has crossed 1,797 scored rows, and that is
the first time it can say anything back. Three findings.

(1) THE FORWARD RECORD IS RUNNING AT ABOUT A THIRD OF THE CLAIMED EDGE, WITH NEGATIVE
BRIER SKILL. CRYP-002 is written into AGENT.md on "1-min direction edge +1.38pp vs a
base-rate-matched null, z = 5.21 (REAL)". Live: 50.47% directional (907/1797) against
a 49.58% up base rate = +0.47pp. Brier 0.25281 vs climatology 0.24998, SKILL -0.0113.
Stating carefully what this does and does not establish, because the temptation to
overclaim runs in both directions. It does NOT convict the +1.38pp figure: the SE on a
hit rate at n=1797 is about 1.2pp, so 50.47% and 51.38% are roughly one SE apart and
not cleanly separated. It DOES establish that the number in AGENT.md is backtested and
the forward record is currently below it — so it must stop being quoted as a live
result, and the ratio sentence ("1/1,183rd of the fee") should be understood as
generous to the strategy, not conservative.

(2) THE CALIBRATION TABLE LOCATES THE PROBLEM, AND THE PROBLEM IS ZERO RESOLUTION, NOT
BAD CALIBRATION. Every bucket resolves at roughly the base rate: said 0.374 -> happened
0.493 (n=75); said 0.463 -> 0.493 (n=952); said 0.535 -> 0.491 (n=700); said 0.625 ->
0.574 (n=68). The 700-row 0.5-0.6 bucket is INVERTED — it says up and gets 0.491. A
forecaster whose every confidence level produces the same outcome frequency has not
learned to discriminate; it has learned the unconditional rate and is jittering around
it. That is a different failure from being miscalibrated, and it is the one the
asia-radar reliability curve was praised for finding on 08-13. Same instrument, same
result: the curve did not just score the book, it said WHERE the loss is. n_updates is
1797, so this is an early-learner statement, not a verdict.

(3) THE SENIOR GATE IS UNCHANGED AND STILL SENIOR. Today's auto-backtest on 156,964
trades: ofi IC 0.105 -> 0.023 and book_imb IC 0.166 -> 0.034 across 5s-60s, every
horizon significant at p=0.002, every horizon net -59.7 to -60.0 bps against 60 bps
costs. Association real, expectancy hopeless. Nothing in finding (1) or (2) touches
this, and nothing in this lab is ever allowed to contradict it.

Today's forecast is the first in this book to ask the lab's own question instead of a
BTC/ETH daily close: "minute forecaster directional hit rate on 2026-08-18 UTC scored
rows exceeds 50.0%", p=0.54. Deliberately not 0.86, which is what the +1.38pp claim
would imply — writing the claim's own p would have been assuming the answer.

Standing bar, quoted as AGENT.md requires: calibration instrument, BARRED from trading,
+0.05 bps per trade against a 60 bps taker fee = 1/1,183rd of the cost of acting on it.

## 2026-08-17 [flow]

THE +1.38pp MINUTE EDGE IS NOT VISIBLE IN THE CURRENT SAMPLE AND SOMEBODY NEEDS TO
LOOK AT THAT. AGENT.md carries the CRYP-002 authorization on a measured claim:
"1-min direction edge +1.38pp vs a base-rate-matched null, z = 5.21 (REAL)". Measured
today on the full file — 5,469 rows, 5,142 non-tie scored, 312 ties:

    directional hit rate    51.11%
    base rate (up)          50.84%
    edge vs matched null    +0.27pp   (z = 0.39)
    Brier                   0.252288
    climatology             0.249930
    Brier SKILL             -0.00944

+0.27pp at z=0.39 is not +1.38pp at z=5.21. It is not distinguishable from zero at
all, and the Brier skill is NEGATIVE — the forecaster is slightly worse than emitting
the base rate on every row. Three things follow:

(1) I AM NOT DECLARING THE PRIOR NUMBER WRONG. It may have been computed on a
different subset (a single day, ties handled differently, a filtered confidence band),
and I cannot reproduce its method from AGENT.md prose. What I can say is that the
number as WRITTEN — full-sample, base-rate-matched — does not reproduce today. A
quoted z=5.21 that nobody can reproduce is worse than no number, because it is the
sentence that authorizes the whole instrument. The method belongs next to the claim.

(2) NOTHING ABOUT THE TRADING BAR CHANGES, AND IT MOVES THE RIGHT WAY. The bar was
never conditional on the edge being small — it is conditional on the edge being
1/1,183rd of the 60bps Coinbase retail taker fee. A +0.27pp edge is SMALLER than the
+1.38pp that was already hopeless. The instrument is barred from trading, the ratio
stands, and today's measurement makes the bar more obviously correct, not less.

(3) THIS IS THE PRODUCT WORKING. The lab was built expecting "coin flip" and expecting
to find that out cleanly. It has: 5,142 scored minute predictions saying no edge. The
result is the deliverable. Reporting a decayed edge honestly on the same day the
throughput note brags about 1,065 rows/day is the entire point of the instrument.

Throughput, for the CRYP-003 record: 08-12 595, 08-13 542, 08-14 1187, 08-15 1240,
08-16 1065, 08-17 840 by 15:32 UTC (partial day, on pace for ~1,300). The collector is
alive — last row 15:32:15 UTC, minutes before this run. Median full day still ~1,065.

And the denominator warning stands harder than ever: 5,469 rows are SIX days of
regime, not 5,469 observations. A −0.00944 Brier skill measured across six days is one
regime's worth of evidence wearing a four-digit n.

Scored today (catch-up): the 08-11 row ("BTC-USD UTC daily close above 63911.88 on
2026-08-15", p=0.47) resolved NO — settled close 63018.75. It was overdue because
08-15/08-16 were a weekend with no run; scored here off the settled candle. The 08-12
row due TODAY could not be scored: this run fires 15:25 UTC and the 08-17 UTC day does
not close until 00:00 UTC. It resolves tomorrow. Same mid-run wall that hit
insider-radar (7 rows) and zero-dte-lab today — one problem, three labs, one owner.

Session OFI on the 08-17 file is +0.0117 across 254,333 trades — far below the 0.10
trigger, so "flow balanced, no call" even if the 1-day unit were still live. It is not:
CRYP-002 retired it and the ledger stays closed at 4 rows.

## 2026-08-18 [flow]

OVERDUE ROW SCORED, AND IT WENT AGAINST THE ONLY JUDGEMENT IN IT. The 08-12 row
("BTC-USD UTC daily close above 63,531.75 on 2026-08-17", p=0.46) came due on 08-17 and
the 08-17 sweep did not score it. Scored here off the settled Coinbase bar — 08-17 close
**64,484.18**, above the threshold → YES, outcome 1. No data was lost: the settled bar is
the correct bar whenever the run fires. The row leaned BELOW on a four-session slide
(64,908.72 → 63,531.75) and BTC rallied +1.50% over the five days instead. The slide tilt
was the only judgement in that row and it was the part that was wrong.

Eight resolved: Brier 0.2517 vs climatology 0.2500, **skill −0.0068, no skill vs base
rate**, base rate exactly 0.500. n=8. Nothing to read.

I WAS PARTLY WRONG ON 08-14 AND THE CORRECTION MATTERS MORE THAN THE ERROR. That row's
note asserted "EVERY bucket resolves at roughly the base rate ... resolution is
approximately zero and the online learner has not yet learned to discriminate at all."
That reading came from rounding p to the nearest 0.05, which smears the confident tails
into the crowded middle. **On strict cuts the tails do separate:**

    p_up >= 0.60   n=398   resolves up 56.03%
    p_up <= 0.40   n=270   resolves up 47.41%
    discrimination spread                   +8.62pp
    days with a positive spread             5 of 5  (+6.49, +6.90, +19.08, +7.23, +8.11)

So the learner is not flat. What it is, is uncalibrated in the bulk — 6,508 scored rows
give hit 50.96% against a 50.41% up base rate, **+0.55pp, se 0.62pp, z=0.89**, which is
not significant. And CRYP-002's headline claim of **+1.38pp, z=5.21** would print z=2.23
at this very n. The forward record is running at roughly 40% of the claimed effect and
cannot yet reject either the claim or zero. That is the honest state: **the claim in
AGENT.md is not being reproduced forward, and it is not yet refuted either.**

THE DENOMINATOR IS FIVE, NOT SIX HUNDRED AND SIXTY-EIGHT. "5 of 5 days positive" is five
observations of regime. Per-day tail counts are 30–77 rows, so a single day's spread
carries a standard error near 11pp — a true +8.6pp effect still flips sign on roughly a
fifth of days by noise alone. Today's forecast is set at p=0.68 for exactly that reason,
deliberately far below what a naive 5/5 record would imply.

Throughput, CRYP-003 disclosure updated: complete UTC days now read 594 (08-12), 541
(08-13), 1,186 (08-14), 1,237 (08-15), 1,060 (08-16), 1,336 (08-17), with 891 already on
08-18 at 15:34 UTC. Median complete day is now ~1,186/day against the 1,065 recorded on
08-17 and the ~1,440 priced ceiling — the instrument is still running under its
authorization but the gap has narrowed. Any time-to-readable-n arithmetic uses the
observed rate.

TWO ROWS DUE TODAY WERE CORRECTLY NOT SCORED. The 08-13 ETH row and the 08-14 minute
hit-rate row both check 2026-08-18, and the UTC day is open at 15:34 UTC. Both resolution
rules say in terms never to resolve off the in-progress bar. They resolve next run; this
is a deferral on a named rule, not a skipped catch-up.

No ledger call, and not because flow was balanced: the 1-day ledger unit is RETIRED under
CRYP-002 and the procedure is not run. Collector healthy — BTC-USD_2026-08-18.csv written
today, 13.8 MB, and the prior session 08-17 is the largest on record at 38.1 MB.

Standing bar restated because today's tail result is the kind of number that gets
misread: even CRYP-002's original +1.38pp was worth **+0.05 bps against a 60 bps Coinbase
retail taker fee — 1/1,183rd of the cost.** This lab is barred from trading. A +8.62pp
tail spread on 668 rows changes nothing about that ratio.

## 2026-08-19 [flow]

TWO OVERDUE FORECASTS RESOLVED, BOTH YES, AND ONE OF THEM WAS A CLEAN MISS.

(1) The 08-13 ETH row — "ETH-USD UTC daily close above 1884.61 on 2026-08-18", p=0.48.
Coinbase settled UTC bar for 08-18: open 1911.94, close **1916.72**. That is above the
threshold, so YES, outcome 1, and the row leaned NO. Wrong by 1.70%, not a whisker. The
row said "more likely below" about an asset that closed 1.7% above, and it deserves to be
read as a miss rather than as noise.

(2) The 08-14 row — "minute forecaster directional hit rate on 2026-08-18 UTC exceeds
50.0%", p=0.54. Computed straight off minute_forecasts.csv: **1,352 scored rows, 710
right = 52.51%** → YES, outcome 1, leaning the right way.

Both were a day late for the same structural reason and it is not a catch-up failure: a
UTC day does not close until 00:00 UTC, and this sweep fires at ~15:30 UTC. **No daily
row in this book can ever be resolved on its own check date.** It is the same wall the
0DTE lab hits at 11:29 ET, with a different clock.

TEN RESOLVED. Base rate 0.600, Brier 0.2495 vs climatology 0.2400, skill **−0.0398, NO
SKILL vs base rate.** State that plainly: across ten forecasts this lab has not beaten
simply predicting the base rate. The 0.50–0.60 bin reads "+0.153 underconfident" on n=6,
which at this sample size is the same sign artifact every lab on the desk keeps recording.

**RETRACTING NOTHING, BUT DISCLOSING A DRIFT: AGENT.md's step 1 describes a schema this
lab no longer writes.** It says trade rows carry `price, qty, isBuy`. The actual header is
`type,ts_ms,px_or_mid,qty_or_spread,extra1,extra2,extra3` — which the project README
documents correctly at line 95, so the README is right and AGENT.md's shorthand is stale.
Read literally, AGENT.md's OFI recipe computes **zero trades and OFI 0.0000** on a file
with 747,478 trades in it, i.e. it silently returns "flow balanced, no call" forever. A
recipe that fails to a quiet abstention rather than an error is the most dangerous kind.
Logged for whoever owns AGENT.md; the numbers below are computed off the real schema.

SESSION FLOW, observation only. 2026-08-18, the last COMPLETE session: 747,478 trades,
buy 2,601.12 vs sell 2,172.35 BTC, **OFI +0.0898** — under the 0.10 trigger, so under the
old rules it would have been "flow balanced, no call" anyway. Today's partial 08-19:
314,804 trades so far, **OFI +0.1763**, on a session where BTC has run **+5.9%**
(64,681.33 → 68,523.40 at the live candle). Strong buy-side flow on a strong day is the
least surprising joint observation in this dataset and is worth exactly nothing.

NO LEDGER CALL, and that is a RULING, not an abstention: the 1-day direction unit is
RETIRED under CRYP-002. Four historical rows stand, none open, and none may be blended
with minute rows.

THE SENIOR GATE HAS NOT MOVED, and it is the one that governs. Today's auto-backtest on
312,390 trades / 30,020 book snapshots: every `ofi` and `book_imb` horizon is
significant on IC (p≈0.002) and every single one is **net −59 to −60 bps after a 60 bps
cost**. Best gross of the whole table is `book_imb` at 60s: 0.91 bps gross, 57.5% hit —
against 60 bps of fee. **VERDICT: no signal is net-positive after costs.** Nothing in the
minute instrument's calibration record is permitted to contradict that.

Today's forecast is deliberately self-referential — the minute forecaster's own hit rate
on 2026-08-20 UTC against a **frozen** 51.10% bar (its all-time rate over 7,853 scored
rows), so the threshold cannot drift at check time. Per-day record vs that bar is 4 of 7
complete days, base rate 0.571 **on n=7 DAYS, not 7,853 rows** (independence.py). p=0.53,
barely above a coin flip and well below the raw 4-of-7, because the bar is essentially the
instrument's own mean and beating your own mean is close to a coin flip by construction.
Recorded and NOT priced: today is running 50.86% on a +5.9% BTC day, so high realised vol
may hurt the forecaster — there is no validated vol-conditioning study here, so that
observation gets written down and given no vote.

Watch item for tomorrow, not acted on: the open 08-18 row bets p_up≥0.60 rows resolve up
more often than p_up≤0.40 rows on 08-19 UTC, at p=0.68. Today's partial has it INVERTED —
0.582 up in the high bucket against 0.630 in the low bucket. It resolves tomorrow off the
complete UTC day. If it resolves NO, that is the most informative row this lab has, because
p=0.68 was the most confident thing it has ever said.

## 2026-08-20 [flow]

**CRYP-004's OPEN HALF, ANSWERED: no past `no call` was produced by the schema bug.**
Three briefs in this lab's whole history record a `no call` — 2026-07-25, 2026-08-17
and 2026-08-19 — and every one of them reports a NON-ZERO OFI computed off real trade
rows: **−0.076** (07-25, buyVol 2,278.4 vs sellVol 2,655.5), **+0.0117** on 254,333
trades (08-17) and **+0.0898** on the complete 08-18 session (08-19). The bug's
signature is unmistakable and none of them carries it: read literally, the old
`price, qty, isBuy` recipe matches zero rows and returns **OFI exactly 0.0000**. A
brief quoting buy and sell volumes in BTC cannot have come from a reader that found
no trades. **All three no-call days are CLEARED — they were the 0.10 threshold doing
its job, not a silent failure wearing its face.** Nothing is left uncleared.

One honest loose end from that audit, recorded rather than resolved: recomputing the
08-16 session today gives **298,009 trades / OFI +0.0085**, where the 08-17 brief
recorded **254,333 trades / +0.0117**. Same sign, same order of magnitude, both far
under the trigger, so the clearance is unaffected — but the trade count moved by 17%
and I cannot say from here whether the file was still being appended when the brief
was written or whether a different session boundary was used. Flagged, not guessed.

**THE BOOK'S MOST CONFIDENT ROW WAS ITS WORST.** The 08-18 forecast asked whether the
minute forecaster's `p_up >= 0.60` rows resolve up more often than its `p_up <= 0.40`
rows on 08-19 UTC, at **p = 0.68**. Result: the high bucket resolved up **57.53%**
(n=73), the low bucket **62.50%** (n=32) — the confident-up bucket resolved up LESS
often than the confident-down bucket. Outcome 0.

**And the reason was visible BEFORE the row was written, which is the actual lesson.**
Only **105 of 1,389** scored rows (**7.6%**) land in either tail. A comparison decided
by 32 against 73 observations has a sampling standard error of roughly ±10pp per
bucket, while the edge being tested is **+1.38pp**. The question was noise-dominated by
construction, and 0.68 was a confidence about the model expressed through a statistic
that could not carry it. **Do not price a question about a small effect at a
tail-sample size you have not looked at.** Today's repost of the same question sits at
**0.55**, and that move is justified by the 7.6% tail share — a structural fact — not
by yesterday's single loss.

**Also scored, and it cost nothing:** the 08-17 row (BTC settled UTC close on 08-19
above its 08-17 close) resolved YES at p=0.50. BTC ran +7.47% over those two days and
this book had claimed no view, which is what 0.50 is for.

Twelve resolved, base rate 0.583, Brier 0.2673 vs climatology 0.2431, **skill −0.0999
— NO skill**. That is the honest headline and it is worse than yesterday's. The
0.60–0.70 bin reads −0.680 off the single row above; the 0.50–0.60 bin reads
"underconfident" off seven. n=12 against the ~100 the scorer demands.

**SCHED-001, measured on this lab as the council asked, and nothing changed.** This
lab's pair is **fire time ~15:40 UTC × horizon unit = the UTC calendar day**. The UTC
day closes at 00:00 UTC, 8h20m AFTER this sweep fires, so **no daily row here can ever
resolve on its own check date** — the two rows scored today were both one run late by
construction, and today's 08-19-dated row (minute hit rate on the 08-20 UTC day) is
deferred to tomorrow for the same reason. **The written proposal the directive asked
for, with the trade-off, verbatim for Anupam's ruling:**
- **(a) Move the fire time past 00:00 UTC** — e.g. a 17:10 PT run. Every UTC-day row
  then resolves on its own date. Cost: a second scheduled slot, this lab leaves the
  08:20 morning sweep, and the same question immediately falls due for [0dte], whose
  11:40 ET fire time has the identical defect against a US session close.
- **(b) Change the horizon unit to a period already closed at fire time** — rows
  register against "the last COMPLETE UTC day". Zero scheduling cost and it resolves
  same-run. But it is a change to a pre-registered unit, so it needs Anupam's name on
  it, and every row already written keeps its current unit.
- **(c) Accept the latency** — the desk takes one run of resolution lag as the honest
  cost of reading a UTC instrument at 15:40 UTC, and every affected row states on its
  face that it resolves on check_date + 1 run.
**My recommendation is (b) for this lab specifically**, because the mis-scheduling here
is not a clock problem — it is that a UTC-day question asked mid-UTC-day is a question
about a period that is still running, and (b) fixes the question rather than the alarm
clock. But it is explicitly not my call: the council barred labs from moving their own
fire times or horizon units, and a lab that re-registers its own unit to make its dates
resolvable is loosening a pre-registration. **Rows already written are not moved under
any option.**

**No ledger call, and it is not an abstention:** the 1-day unit is RETIRED under
CRYP-002 and the falsifiable unit is the minute forecaster, which ran 890 scored rows
today by 15:40 UTC. For the record the complete 08-19 session read **OFI +0.0584**
across 1,130,648 trades (buy 10,253.88 vs sell 9,123.12 BTC) — under the 0.10 trigger
in any case.

**THE SENIOR GATE, and it leads every quote of this lab:** the 1-minute direction edge
is **real** — +1.38pp vs a base-rate-matched null, z = 5.21 — and worth **+0.05 bps
against a 60 bps Coinbase retail taker fee, about 1/1,183rd of what it would cost to
act on it.** Every `ofi` and `book_imb` horizon is statistically significant on IC
(p≈0.002) and every one is net −59 to −60 bps. Calibration instrument, barred from
trading.
