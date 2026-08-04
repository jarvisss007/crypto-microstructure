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
