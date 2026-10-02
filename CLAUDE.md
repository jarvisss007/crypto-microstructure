# crypto-microstructure — a lab of Leo's Trading Firm

**Paper only, always.** Sim-only until the Rule 7 gate; nothing here places, sizes or
advises a real trade. Rule 4 bars live short-dated options regardless.

**Before acting, read `~/command-center/THE_FIRM_BRAIN.md`** — the cross-lab canon of
paid-for mechanisms — and ask whether an entry names a defect this lab has not checked
itself for.

**The law of this repo:**
- Pre-registration is sacred: a rule is frozen when registered; improving it is a NEW
  registered variant (log it in `~/command-center/council/evolution_ledger.json` — an
  unlogged tweak is a mining violation), never an edit to a live rule.
- BENCH-002: a scored number is never rewritten. Disposals go through /void-row —
  match the book's existing void convention exactly, and prove the row left every
  hit-rate (allowlists, never denylists).
- n is counted in independent days/events, never rows, and every published n carries
  `clustered_by`. A mid is not a fill; a mark is not a result.
- Freshness is judged by the DATA'S own stamp (last_trade_time, book timestamp, file
  vintage) — never the wall clock, never a CDN rebuild time.
- Every zero states its reason. A monitor aimed at a missing file reports BROKEN, not
  a clean age. Empty books exist with headers.
- Benchmark: climatology / base-rate-matched null per horizon
- **CRYPTO-006 — the 1/5/15-minute direction forecasters are RETIRED (2026-10-02).** Ruled by Anupam ('go ahead', 2026-10-02 10:24 PT), adopting the recommended option, option (a) STOP.
  The question is ANSWERED, no skill: 147,819 scored forecasts, Brier skill -0.0135 / -0.0374 / -0.0908 at +1 / +5 / +15 min, all below the
  base rate (numbers and the restore commands: README top). `com.anupam.crypto-minute` and `com.anupam.crypto-horizons` are
  unloaded; their plists sit in `~/Library/LaunchAgents/retired/`. **Do not restart them, and do not run `agent/minute_forecaster.py`
  or `agent/horizon_forecaster.py` by hand** (a manual tick appends to a frozen book). `agent/minute_forecasts.csv`,
  `agent/forecasts_5m.csv`, `agent/forecasts_15m.csv` and their state files are history, byte-pinned (sha256 in the README; the
  `_crypto006_` checks are proposed in `PROPOSED_resolver_changes_CRYPTO-006.py`; the freeze is ADVISORY until they are integrated
  into resolver.py): never edit, re-score or void a row (BENCH-002).
  A quiet scoreboard is the intended state, not a dead
  writer. The collector, the nightly rotation and the paper crypto desk (`~/crypto-desk`) keep running. A restart is Anupam's ruling.
  Open consequence, NOT decided here: the flow agent's standing daily forecast (`agent/AGENT.md`, "minute forecaster directional hit
  rate on <day> UTC ...") has no new rows to resolve against after 2026-10-02 - retiring or re-aiming it is Anupam's ruling.
- The 1-minute book inflates 791×: n is HOURS, never rows. Learning/data tool, not a strategy.
**Standing rulings live in `~/command-center/council/issues.json` — grep it before
rewriting any recorded row.** Commit this repo at session end (push if it has a remote).
