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
