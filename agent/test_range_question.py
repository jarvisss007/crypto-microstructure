#!/opt/anaconda3/bin/python
"""Tests for range_question.py (CRYPTO-008). Stdlib unittest, nothing outside a temp dir is ever written:
    /opt/anaconda3/bin/python ~/crypto-microstructure/agent/test_range_question.py -v
The real book and the real minute files are only READ (a byte-identity test copies the real book into the temp dir first)."""
import contextlib
import csv
import datetime as dt
import io
import os
import re
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import range_question as rq  # noqa: E402

REAL_BOOK = os.path.join(HERE, "forecasts.csv")
REAL_MINUTES = os.path.join(os.path.dirname(HERE), "research", "minutes")
MHEAD = ["minute_epoch", "minute_utc", "close", "book_imb", "ofi", "day", "trades", "volume", "buy_share", "high", "low"]


def minute_file(mdir, day, n, low="83000", high="85490", skip_valid=0):
    """A minute file for UTC day `day` with n rows on that day: one row carries `high`, one carries `low`, the rest sit between.
    The first `skip_valid` rows have an unreadable high (they must not count as valid minutes)."""
    d0 = dt.datetime.fromisoformat(day + "T00:00").replace(tzinfo=dt.timezone.utc)
    mid = (Decimal(high) + Decimal(low)) / 2
    with open(os.path.join(mdir, f"BTC-USD_{day}.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(MHEAD)
        for i in range(n):
            t = d0 + dt.timedelta(minutes=i)
            hi, lo = (high if i == n // 2 else str(mid + 1)), (low if i == n // 3 else str(mid - 1))
            if i < skip_valid:
                hi = "nan"
            w.writerow([int(t.timestamp()) // 60, t.strftime("%Y-%m-%dT%H:%M"), mid, 0, 0, day, 1, 1, 0.5, hi, lo])


def q(day, x="3.0"):
    return rq.QUESTION.format(d=day, x=x)


def row(date, day, outcome="", x="3.0", question=None, check=None, notes="[flow] [tech] seed"):
    return {"date": date, "instrument": "BTC", "horizon_days": "1", "question": question or q(day, x), "p": "0.43",
            "check_date": check or day, "outcome": outcome, "notes": notes}


def write_book(path, rows):
    with open(path, "w", newline="") as fh:                      # csv default CRLF, exactly like the real book
        w = csv.DictWriter(fh, fieldnames=rq.COLS)
        w.writeheader()
        w.writerows(rows)


def run(book, mdir, *argv):
    """range_question.main with the scratch book/minutes; returns (exit code or SystemExit message, stdout)."""
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            code = rq.main(["--book", book, "--minutes-dir", mdir, *argv])
    except SystemExit as e:
        code = e.code if isinstance(e.code, str) else int(e.code or 0)
    return code, out.getvalue()


def read(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def rb(path):
    with open(path, "rb") as fh:
        return fh.read()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mdir = os.path.join(self.tmp.name, "minutes")
        os.makedirs(self.mdir)
        self.book = os.path.join(self.tmp.name, "forecasts.csv")

    def tearDown(self):
        self.tmp.cleanup()


class TestQuestion(unittest.TestCase):
    def test_canonical_form_only(self):
        self.assertTrue(rq.Q_RE.match(q("2026-10-06")))
        for bad in (q("2026-10-06").lower(), q("2026-10-06") + " ", "BTC-USD range on 2026-10-06 exceeds 3.0%",
                    q("2026-10-06").replace("high-low range", "range"), q("2026-10-06").replace("exceeds 3.0%", "exceeds 3.0 %"),
                    q("2026-10-06").replace("UTC-day ", ""), "minute forecaster directional hit rate on 2026-10-02 UTC scored rows exceeds 51.00%"):
            self.assertIsNone(rq.Q_RE.match(bad), bad)

    def test_declared_constants(self):
        self.assertEqual(rq.X_REGISTERED, (Decimal("3.0"),))
        self.assertEqual(rq.MIN_MINUTES, 1300)
        self.assertEqual(rq.CLEAN_FROM, "2026-08-22")

    def test_strictly_greater_in_exact_decimal(self):
        lo = Decimal("83000")
        self.assertFalse(rq.exceeds(Decimal("85490"), lo, Decimal("3.0")))            # exactly 3.0 -> NO
        self.assertTrue(rq.exceeds(Decimal("85490.01"), lo, Decimal("3.0")))
        self.assertFalse(rq.exceeds(Decimal("103.0"), Decimal("100.0"), Decimal("3.0")))  # a float trap: stays exactly 3.0
        self.assertEqual(rq.range_pct(Decimal("85490"), lo), Decimal("3"))


class TestResolve(Base):
    def test_yes_no_boundary_and_notes(self):
        minute_file(self.mdir, "2026-10-03", 1440, low="83000", high="85490")        # exactly 3.0% -> NO
        minute_file(self.mdir, "2026-10-04", 1440, low="83000", high="85490.01")     # above -> YES
        write_book(self.book, [row("2026-10-02", "2026-10-03"), row("2026-10-03", "2026-10-04")])
        code, out = run(self.book, self.mdir, "resolve", "--today", "2026-10-06")
        self.assertEqual(code, 0)
        r = read(self.book)
        self.assertEqual([x["outcome"] for x in r], ["0", "1"])
        self.assertIn("RESOLVED 2026-10-06 by range_question.py", r[0]["notes"])
        self.assertIn("-> NO", r[0]["notes"])
        self.assertIn("-> YES", r[1]["notes"])
        self.assertTrue(r[0]["notes"].startswith("[flow] [tech] seed"))              # the row's own notes are kept, appended to

    def test_void_threshold_is_1300_valid_minutes(self):
        minute_file(self.mdir, "2026-10-03", 1299)
        minute_file(self.mdir, "2026-10-04", 1300, high="86000")
        minute_file(self.mdir, "2026-10-05", 1400, skip_valid=101)                   # 1299 readable minutes out of 1400 rows
        write_book(self.book, [row("a", "2026-10-03"), row("b", "2026-10-04"), row("c", "2026-10-05")])
        run(self.book, self.mdir, "resolve", "--today", "2026-10-07")
        out = [x["outcome"] for x in read(self.book)]
        self.assertEqual(out, ["void", "1", "void"])

    def test_waiting_and_late_void(self):
        minute_file(self.mdir, "2026-10-09", 1440)                                   # a LATER day's file exists
        write_book(self.book, [row("a", "2026-10-04"), row("b", "2026-10-06"), row("c", "2026-10-07"), row("d", "2026-10-08")])
        code, out = run(self.book, self.mdir, "resolve", "--today", "2026-10-09")
        o = [x["outcome"] for x in read(self.book)]
        self.assertEqual(o, ["void", "void", "", ""])                                # 5 and 3 days late -> void; 2 and 1 -> waiting
        self.assertIn("waiting", out)

    def test_missing_file_without_a_later_file_waits_forever_not_void(self):
        write_book(self.book, [row("a", "2026-10-01")])
        run(self.book, self.mdir, "resolve", "--today", "2026-10-30")
        self.assertEqual(read(self.book)[0]["outcome"], "")                          # nothing proves nothing was recorded

    def test_target_day_that_has_not_ended_waits_even_with_a_file(self):
        minute_file(self.mdir, "2026-10-06", 1440, high="99999")
        write_book(self.book, [row("a", "2026-10-06")])
        run(self.book, self.mdir, "resolve", "--today", "2026-10-06")
        self.assertEqual(read(self.book)[0]["outcome"], "")

    def test_every_other_row_is_left_alone(self):
        minute_file(self.mdir, "2026-10-03", 1440, high="85490.01")
        legacy = row("2026-10-01", "x", question="minute forecaster directional hit rate on 2026-10-02 UTC scored rows exceeds 51.00%", check="2026-10-02")
        rows = [row("s", "2026-09-30", outcome="1", notes="scored earlier"), row("v", "2026-09-29", outcome="void", notes="void earlier"), legacy,
                row("u", "2026-10-03", question="BTC will be volatile on 2026-10-03"), row("x", "2026-10-03", x="2.0"),
                row("m", "2026-10-03", check="2026-10-04"), row("due", "2026-10-03")]
        write_book(self.book, rows)
        before = rb(self.book).split(b"\r\n")
        code, out = run(self.book, self.mdir, "resolve", "--today", "2026-10-06")
        after = rb(self.book).split(b"\r\n")
        self.assertEqual(len(before), len(after))
        changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        self.assertEqual(changed, [7])                                               # only the due row's line differs, byte for byte
        for word in ("LEGACY", "SKIP (unparsed)", "UNREGISTERED", "REFUSED"):
            self.assertIn(word, out)

    def test_noop_resolve_does_not_rewrite(self):
        write_book(self.book, [row("a", "2026-10-03", outcome="1")])
        before = os.stat(self.book).st_mtime_ns
        run(self.book, self.mdir, "resolve", "--today", "2026-10-06")
        self.assertEqual(os.stat(self.book).st_mtime_ns, before)

    def test_dry_writes_nothing(self):
        minute_file(self.mdir, "2026-10-03", 1440)
        write_book(self.book, [row("a", "2026-10-03")])
        before = rb(self.book)
        code, out = run(self.book, self.mdir, "resolve", "--dry", "--today", "2026-10-06")
        self.assertEqual(rb(self.book), before)
        self.assertIn("[DRY]", out)

    def test_resolver_is_idempotent(self):
        minute_file(self.mdir, "2026-10-03", 1440, high="85490.01")
        write_book(self.book, [row("a", "2026-10-03")])
        run(self.book, self.mdir, "resolve", "--today", "2026-10-06")
        once = rb(self.book)
        run(self.book, self.mdir, "resolve", "--today", "2026-10-07")
        self.assertEqual(rb(self.book), once)


class TestFile(Base):
    NOTE = "filed at the reference base; no conditional established at the S14 standard"

    def file(self, now, p="0.43", note=None, *extra):
        return run(self.book, self.mdir, "file", "--p", p, "--note", note or self.NOTE, "--now", now, *extra)

    def setUp(self):
        super().setUp()
        write_book(self.book, [row("2026-09-30", "2026-10-01", outcome="0")])

    def test_target_is_the_next_utc_day_and_the_row_is_canonical(self):
        code, out = self.file("2026-10-09T08:30:00-07:00")                           # Friday morning PT = 15:30Z Friday
        self.assertEqual(code, 0, out)
        r = read(self.book)[-1]
        self.assertEqual((r["date"], r["horizon_days"], r["check_date"], r["instrument"], r["outcome"]), ("2026-10-09", "1", "2026-10-10", "BTC", ""))
        self.assertEqual(r["question"], q("2026-10-10"))
        self.assertEqual(r["p"], "0.43")
        for token in ("[flow] [tech] [p_cal=", "Resolves check_date+1 (standing, SCHED-001)", "REFERENCE CLASS", "VOID RULE fixed in advance",
                      "BARRED FROM TRADING", "S8", "research/minutes/BTC-USD_2026-10-10.csv", self.NOTE):
            self.assertIn(token, r["notes"])

    def test_s8_uses_the_utc_date_at_filing_not_the_local_date(self):
        code, out = self.file("2026-10-09T20:30:00-07:00")                           # 03:30Z on 10-10: that UTC day has begun
        self.assertEqual(code, 0, out)
        r = read(self.book)[-1]
        self.assertEqual((r["date"], r["check_date"], r["horizon_days"]), ("2026-10-09", "2026-10-11", "2"))

    def test_one_row_per_resolving_day_and_one_per_run(self):
        self.file("2026-10-09T08:30:00-07:00")
        code, out = self.file("2026-10-09T10:30:00-07:00")
        self.assertIn("REFUSED", str(code) + out)                                    # a second row on the same date
        self.assertEqual(len(read(self.book)), 2)
        code, out = self.file("2026-10-10T08:30:00-07:00")                           # next day: 10-11 is the first free target day
        self.assertEqual(read(self.book)[-1]["check_date"], "2026-10-11")
        write_book(self.book, [row("2026-10-08", "2026-10-10"), row("2026-10-08", "2026-10-11")])
        self.file("2026-10-09T08:30:00-07:00")
        self.assertEqual(read(self.book)[-1]["check_date"], "2026-10-12")            # taken days are skipped

    def test_bad_probabilities_and_short_notes_are_refused(self):
        for p in ("0", "1", "1.2", "-0.1", "abc", "0.4321", ""):
            code, out = self.file("2026-10-09T08:30:00-07:00", p=p)
            self.assertIn("REFUSED", str(code) + out, p)
        code, out = self.file("2026-10-09T08:30:00-07:00", note="short")
        self.assertIn("REFUSED", str(code) + out)
        self.assertEqual(len(read(self.book)), 1)                                    # nothing was written

    def test_dry_writes_nothing(self):
        before = rb(self.book)
        code, out = self.file("2026-10-09T08:30:00-07:00", "0.43", None, "--dry")
        self.assertEqual(rb(self.book), before)
        self.assertIn("[DRY]", out)

    def test_refuses_without_atomicio_and_never_falls_back(self):
        orig = rq._load

        def boom(name, path):
            if name == "_atomicio_cr008":
                raise ImportError("simulated: atomicio missing")
            return orig(name, path)
        rq._load = boom
        saved_atom, rq._ATOM = rq._ATOM, None                                         # force a fresh load attempt, which fails
        try:
            before = rb(self.book)
            code, out = self.file("2026-10-09T08:30:00-07:00")
            self.assertIn("REFUSED", str(code) + out)
            code2, out2 = run(self.book, self.mdir, "resolve", "--today", "2026-10-30")
            self.assertEqual(rb(self.book), before)                   # no open(path, "w") fallback anywhere
        finally:
            rq._load = orig
            rq._ATOM = saved_atom


@unittest.skipUnless(os.path.exists(REAL_BOOK) and os.path.isdir(REAL_MINUTES), "needs the lab's real book and minute files (read only)")
class TestAgainstTheRealLab(Base):
    def test_old_rows_stay_byte_identical_when_a_row_is_filed(self):
        shutil.copy(REAL_BOOK, self.book)
        old = rb(self.book)
        self.assertIn(b"\r\n", old)
        code, out = run(self.book, REAL_MINUTES, "file", "--p", "0.43", "--note", "rehearsal on a COPY of the real book, never the real one",
                        "--now", "2026-10-09T08:30:00-07:00")
        self.assertEqual(code, 0, out)
        new = rb(self.book)
        self.assertTrue(new.startswith(old), "every existing byte of the real book must survive the atomic rewrite")
        self.assertEqual(new[len(old):].count(b"\r\n"), 1)
        self.assertEqual(len(read(self.book)), len(read(REAL_BOOK)) + 1)

    def test_legacy_rows_are_listed_and_untouched_by_resolve(self):
        shutil.copy(REAL_BOOK, self.book)
        old = rb(self.book)
        code, out = run(self.book, REAL_MINUTES, "resolve", "--today", "2026-12-31")
        self.assertEqual(rb(self.book), old)
        if any(not (r["outcome"] or "").strip() and r["question"].startswith(rq.LEGACY_PREFIX) for r in read(self.book)):
            self.assertIn("LEGACY", out)

    def test_reference_matches_an_independent_count_and_the_mandate_text(self):
        ref = rq.reference(dt.date(2026, 10, 2))
        indep_n = indep_k = 0
        for f in sorted(os.listdir(REAL_MINUTES)):
            m = re.match(r"BTC-USD_(\d{4}-\d{2}-\d{2})\.csv$", f)
            if not m or not ("2026-08-22" <= m.group(1) < "2026-10-02"):
                continue
            hi = lo = None
            n = 0
            with open(os.path.join(REAL_MINUTES, f), newline="") as fh:
                for r in csv.DictReader(fh):
                    if not r["minute_utc"].startswith(m.group(1)):
                        continue
                    try:
                        h, l = Decimal(r["high"]), Decimal(r["low"])
                    except Exception:
                        continue
                    if not (h.is_finite() and l.is_finite()) or l <= 0 or h < l:
                        continue
                    n += 1
                    hi = h if hi is None or h > hi else hi
                    lo = l if lo is None or l < lo else lo
            if n >= 1300:
                indep_n += 1
                indep_k += 1 if 100 * (hi - lo) > Decimal("3.0") * lo else 0
        self.assertEqual((ref["n"], ref["k"]), (indep_n, indep_k))
        text = rb(os.path.join(HERE, "AGENT.md")).decode("utf-8")
        if "THE STANDING QUESTION (CRYPTO-008" in text:                              # the mandate declares what the tool enforces
            self.assertIn(f"over the {indep_n} eligible complete UTC days to\n  2026-10-01", text)
            self.assertIn(f"exceeded 3.0% on {indep_k}", text)
            self.assertIn(f"{Decimal(indep_k) / Decimal(indep_n):.3f}", text)
            self.assertIn(rq.QUESTION.format(d="<D>", x="3.0"), text)
            self.assertIn("1,300", text)


if __name__ == "__main__":
    unittest.main()
