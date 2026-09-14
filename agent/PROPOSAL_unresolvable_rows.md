# PROPOSAL — how a rate-threshold forecast treats rows that can never resolve

**Status: PROPOSAL for Anupam. NOT APPLIED.** Frozen 2026-09-14 by labs-morning-sweep [flow], answering the
council's 2026-09-11 OPEN. It governs no row filed before the day Anupam approves it, and no row already written
(BENCH-002) — in particular the 09-09 row scored YES at 51.0026% stands exactly as scored.

## The gap
The pre-registered void rule covers a *thin day* (< 200 scored rows). It says nothing about a day whose *deciding*
minutes are missing from the recording. On 2026-09-10, 3 rows targeting that day never got a `px_at_target`; all
three wrong would have flipped the row from YES to NO. The question's filed wording ("scored rows") decided it,
which was mechanical but accidental — no rule chose that.

## Proposed rule (one rule, mechanical, decided before any outcome it governs)
For any hand-filed question that thresholds a rate over a day's rows:
1. **Ties** stay excluded exactly as today (CRYP-001). **Unresolvable** rows (no `px_at_target` once a later UTC
   day has been scored) are counted separately and printed on the row. They are never silently dropped.
2. Compute the outcome twice: all unresolvable rows as **wrong**, then all as **right**.
3. If both give the same answer, score it as filed.
4. If they disagree, the row **VOIDS** with `void_reason = "undecided by the recording: N unresolvable rows span
   the threshold"`. It is kept, never deleted, and excluded from every scored statistic, like any void row.
5. The void rule for < 200 scored rows is unchanged and is checked first.

## What it would have done historically (disclosed so nobody has to guess)
- 09-09 row (1m, 09-10 day): 585/1,147 scored, 3 unresolvable. Wrong-bound 50.87% versus right-bound 51.13%, so it
  would have VOIDED rather than scored YES.
- 09-10 row (15m, 09-11 day): 52 unresolvable, bounds 39.70% / 44.92%, so NO either way.
- 09-11 row (1m, 09-12 day): 7 unresolvable, bounds 48.17% / 49.39%, so NO either way.

## Why this and not the alternatives
- *Score on scored rows only* (the status quo by wording): lets a gap in the recording decide a close call.
- *Treat unresolvable as wrong*: builds a bias against YES into a recording failure.
- *Void any day with an unresolvable row*: most days have a few; that voids the book for noise that never
  mattered to the outcome.

Bounding votes only when the missing rows could actually change the answer.
