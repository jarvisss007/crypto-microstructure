#!/opt/anaconda3/bin/python
"""Tests for range_question.py (CRYPTO-008). Stdlib unittest, nothing outside a temp dir is ever written:
    /opt/anaconda3/bin/python test_range_question.py -v          (next to range_question.py)
The real book and the real minute files are only READ (the byte-identity tests copy the real book into the temp dir first).
The tool's test hooks (--book --minutes-dir --now --today) are refused unless RQ_TEST=1, which this module sets for itself."""
import contextlib
import csv
import datetime as dt
import io
import os
import re
import shutil
import sys
import tempfile
import time
import unittest
from decimal import Decimal
from unittest import mock

os.environ["RQ_TEST"] = "1"                                      # the suite's own switch; production never sets it
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import range_question as rq  # noqa: E402

LAB = os.path.expanduser("~/crypto-microstructure")
REAL_BOOK = os.path.join(LAB, "agent", "forecasts.csv")
REAL_MINUTES = os.path.join(LAB, "research", "minutes")
AGENT_MD = next((p for p in (os.path.join(HERE, "AGENT.md"), os.path.join(LAB, "agent", "AGENT.md")) if os.path.exists(p)), None)
MHEAD = ["minute_epoch", "minute_utc", "close", "book_imb", "ofi", "day", "trades", "volume", "buy_share", "high", "low"]
LONG_AGO = time.time() - 2 * 86400


def minute_file(mdir, day, n, low="83000", high="85490", skip_valid=0, fresh=False):
    """A minute file for UTC day `day` with n rows on that day: one row carries `high`, one carries `low`, the rest sit between. The first
    `skip_valid` rows are forward-filled minutes (high and low blank, as in the real files): they must not count as valid minutes.
    The file is back-dated two days unless fresh=True (a file modified moments ago may still be being written)."""
    d0 = dt.datetime.fromisoformat(day + "T00:00").replace(tzinfo=dt.timezone.utc)
    mid = (Decimal(high) + Decimal(low)) / 2
    path = os.path.join(mdir, f"BTC-USD_{day}.csv")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(MHEAD)
        for i in range(n):
            t = d0 + dt.timedelta(minutes=i)
            hi, lo = (high if i == n // 2 else str(mid + 1)), (low if i == n // 3 else str(mid - 1))
            if i < skip_valid:
                hi = lo = ""
            w.writerow([int(t.timestamp()) // 60, t.strftime("%Y-%m-%dT%H:%M"), mid, 0, 0, day, 1 if hi else "", 1 if hi else "", 0.5 if hi else "", hi, lo])
    if not fresh:
        os.utime(path, (LONG_AGO, LONG_AGO))


def q(day, x="3.0"):
    return rq.QUESTION.format(d=day, x=x)


def row(date, day, outcome="", x="3.0", question=None, check=None, notes="[flow] [tech] seed", p="0.43"):
    return {"date": date, "instrument": "BTC", "horizon_days": "1", "question": question if question is not None else q(day, x), "p": p,
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
        self.mdir = os.path.join(self.tmp.name, "research", "minutes")
        self.rawdir = os.path.join(self.tmp.name, "research", "data")
        os.makedirs(self.mdir)
        os.makedirs(self.rawdir)
        self.book = os.path.join(self.tmp.name, "forecasts.csv")

    def tearDown(self):
        self.tmp.cleanup()

    def raw(self, day, ext=".csv.gz"):
        open(os.path.join(self.rawdir, f"BTC-USD_{day}{ext}"), "w").close()


class TestQuestion(unittest.TestCase):
    def test_form_is_loose_but_canonical_is_exact(self):
        self.assertTrue(rq.Q_RE.match(q("2026-10-06")))
        for bad in (q("2026-10-06").lower(), "BTC-USD range on 2026-10-06 exceeds 3.0%", q("2026-10-06").replace("high-low range", "range"),
                    q("2026-10-06").replace("exceeds 3.0%", "exceeds 3.0 %"), q("2026-10-06").replace("UTC-day ", ""),
                    "minute forecaster directional hit rate on 2026-10-02 UTC scored rows exceeds 51.00%"):
            self.assertIsNone(rq.Q_RE.match(bad), bad)
        self.assertTrue(rq.canonical({"question": q("2026-10-06")}))
        for spelled in ("3%", "3.00%", "03.0%", "3.0 %"):
            r = {"question": q("2026-10-06", x=spelled.rstrip("%"))}
            if rq.form(r):                                         # a spelling the loose form still recognises must NOT be canonical
                self.assertIsNone(rq.canonical(r), spelled)
        for sloppy in (q("2026-10-06") + " ", " " + q("2026-10-06")):
            self.assertTrue(rq.form({"question": sloppy}), sloppy)  # recognised as an attempt at the question ...
            self.assertIsNone(rq.canonical({"question": sloppy}), repr(sloppy))   # ... but never canonical

    def test_declared_constants(self):
        self.assertEqual(rq.X_REGISTERED, (Decimal("3.0"),))
        self.assertEqual(rq.X_TEXT, "3.0")
        self.assertEqual(rq.MIN_MINUTES, 1300)
        self.assertEqual(rq.CLEAN_FROM, "2026-08-22")
        self.assertEqual(rq.MIN_FILE_AGE_S, 600)
        self.assertEqual(rq.LATE_VOID_DAYS, 3)

    def test_strictly_greater_in_exact_decimal(self):
        lo = Decimal("83000")
        self.assertFalse(rq.exceeds(Decimal("85490"), lo, Decimal("3.0")))            # exactly 3.0 -> NO
        self.assertTrue(rq.exceeds(Decimal("85490.01"), lo, Decimal("3.0")))
        self.assertFalse(rq.exceeds(Decimal("103.0"), Decimal("100.0"), Decimal("3.0")))  # a float trap: stays exactly 3.0
        self.assertEqual(rq.range_pct(Decimal("85490"), lo), Decimal("3"))

    def test_p_is_the_base_to_two_decimals_half_up(self):
        self.assertEqual(rq.base_p({"base": Decimal(10) / Decimal(23)}), Decimal("0.43"))
        self.assertEqual(rq.base_p({"base": Decimal("0.435")}), Decimal("0.44"))     # half up, not banker's rounding
        self.assertEqual(rq.base_p({"base": Decimal("0.4")}), Decimal("0.40"))
        self.assertIsNone(rq.base_p({"base": None}))


class TestHooks(Base):
    def test_test_hooks_are_refused_in_production(self):
        env = {k: v for k, v in os.environ.items() if k != "RQ_TEST"}
        paths_before = (rq.BOOK, rq.MINUTES)                                       # other tests repoint these in-process; compare to THIS moment
        with mock.patch.dict(os.environ, env, clear=True):
            for argv in (["--book", self.book, "reference"], ["--minutes-dir", self.mdir, "reference"],
                         ["file", "--note", "x" * 30, "--now", "2026-10-09T08:30:00-07:00"], ["file", "--dry", "--note", "x" * 30, "--now", "2026-10-09T08:30:00-07:00"],
                         ["resolve", "--today", "2026-10-30"], ["resolve", "--dry", "--today", "2026-10-30"]):
                with self.assertRaises(SystemExit) as cm:
                    rq.main(argv)
                self.assertIn("REFUSED", str(cm.exception.code), argv)
                self.assertIn("test hook", str(cm.exception.code), argv)
            self.assertEqual((rq.BOOK, rq.MINUTES), paths_before)                   # a refused hook never repointed the tool

    def test_read_only_flags_stay_available_in_production(self):
        env = {k: v for k, v in os.environ.items() if k != "RQ_TEST"}
        with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(rq, "cmd_file", return_value=0), \
                mock.patch.object(rq, "cmd_resolve", return_value=0), mock.patch.object(rq, "cmd_reference", return_value=0):
            self.assertEqual(rq.main(["file", "--dry", "--note", "x" * 30]), 0)
            self.assertEqual(rq.main(["resolve", "--dry"]), 0)
            self.assertEqual(rq.main(["reference", "--as-of", "2026-10-02"]), 0)


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

    def test_void_threshold_is_1300_trade_bearing_minutes(self):
        minute_file(self.mdir, "2026-10-03", 1299)
        minute_file(self.mdir, "2026-10-04", 1300, high="86000")
        minute_file(self.mdir, "2026-10-05", 1440, skip_valid=141)                   # 1299 trade minutes out of 1440 rows (forward-filled rest)
        minute_file(self.mdir, "2026-10-06", 1440, skip_valid=140, high="86000")     # exactly 1300
        write_book(self.book, [row("a", "2026-10-03"), row("b", "2026-10-04"), row("c", "2026-10-05"), row("d", "2026-10-06")])
        run(self.book, self.mdir, "resolve", "--today", "2026-10-08")
        self.assertEqual([x["outcome"] for x in read(self.book)], ["void", "1", "void", "1"])

    def test_young_minute_file_waits_then_scores(self):
        minute_file(self.mdir, "2026-10-03", 1440, high="85490.01", fresh=True)      # modified just now: the rotation may still be writing it
        write_book(self.book, [row("a", "2026-10-03")])
        before = rb(self.book)
        code, out = run(self.book, self.mdir, "resolve", "--today", "2026-10-06")
        self.assertEqual(rb(self.book), before)                                      # neither scored nor void nor rewritten
        self.assertIn("may still be being written", out)
        os.utime(os.path.join(self.mdir, "BTC-USD_2026-10-03.csv"), (LONG_AGO, LONG_AGO))
        run(self.book, self.mdir, "resolve", "--today", "2026-10-06")
        self.assertEqual(read(self.book)[0]["outcome"], "1")

    def test_a_thin_young_file_is_not_voided_either(self):
        minute_file(self.mdir, "2026-10-03", 100, fresh=True)
        write_book(self.book, [row("a", "2026-10-03")])
        run(self.book, self.mdir, "resolve", "--today", "2026-10-06")
        self.assertEqual(read(self.book)[0]["outcome"], "")                          # a void is permanent (BENCH-002): never on a half-written file

    def test_waiting_and_late_void_when_nothing_was_recorded(self):
        minute_file(self.mdir, "2026-10-09", 1440)                                   # a LATER day's file exists; no raw tape for any target
        write_book(self.book, [row("a", "2026-10-04"), row("b", "2026-10-06"), row("c", "2026-10-07"), row("d", "2026-10-08")])
        code, out = run(self.book, self.mdir, "resolve", "--today", "2026-10-09")
        self.assertEqual([x["outcome"] for x in read(self.book)], ["void", "void", "", ""])     # 5 and 3 days late -> void; 2 and 1 -> waiting
        self.assertIn("waiting", out)
        self.assertIn("no raw tape and no minute file", read(self.book)[0]["notes"])

    def test_a_raw_tape_without_a_minute_file_is_broken_never_void(self):
        minute_file(self.mdir, "2026-10-09", 1440)
        self.raw("2026-10-04", ".csv.gz")                                            # recorded and compressed, but never derived
        self.raw("2026-10-05", ".csv")                                               # recorded, still uncompressed
        write_book(self.book, [row("a", "2026-10-04"), row("b", "2026-10-05"), row("c", "2026-10-06")])
        code, out = run(self.book, self.mdir, "resolve", "--today", "2026-10-09")
        self.assertEqual([x["outcome"] for x in read(self.book)], ["", "", "void"])  # only the day with NO raw tape voids
        self.assertEqual(out.count("BROKEN"), 2)
        run(self.book, self.mdir, "resolve", "--today", "2027-01-01")
        self.assertEqual([x["outcome"] for x in read(self.book)], ["", "", "void"])  # months later: still not void while a raw tape exists

    def test_missing_file_without_a_later_file_waits_forever_not_void(self):
        write_book(self.book, [row("a", "2026-10-01")])
        run(self.book, self.mdir, "resolve", "--today", "2026-10-30")
        self.assertEqual(read(self.book)[0]["outcome"], "")                          # nothing proves the directory was readable

    def test_target_day_that_has_not_ended_waits_even_with_a_file(self):
        minute_file(self.mdir, "2026-10-06", 1440, high="99999")
        write_book(self.book, [row("a", "2026-10-06")])
        run(self.book, self.mdir, "resolve", "--today", "2026-10-06")
        self.assertEqual(read(self.book)[0]["outcome"], "")

    def test_non_canonical_spellings_are_never_scored(self):
        minute_file(self.mdir, "2026-10-03", 1440, high="85490.01")
        spelled = [q("2026-10-03", x="3"), q("2026-10-03", x="3.00"), q("2026-10-03", x="03.0"), q("2026-10-03") + " ", " " + q("2026-10-03")]
        write_book(self.book, [row(f"d{i}", "2026-10-03", question=s) for i, s in enumerate(spelled)] + [row("ok", "2026-10-03")])
        before = rb(self.book).split(b"\r\n")
        code, out = run(self.book, self.mdir, "resolve", "--today", "2026-10-06")
        self.assertEqual([x["outcome"] for x in read(self.book)], ["", "", "", "", "", "1"])   # only the exact text scores
        self.assertEqual(out.count("NONCANONICAL"), 5)
        after = rb(self.book).split(b"\r\n")
        self.assertEqual([i for i, (a, b) in enumerate(zip(before, after)) if a != b], [6])     # and only that row's line changed

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
    NOTE = "filed at the reference base; no conditional established, a conditional is a new registered variant"

    def file(self, now, p=None, note=None, *extra):
        argv = ["file", "--note", note or self.NOTE, "--now", now, *extra]
        if p is not None:
            argv += ["--p", p]
        return run(self.book, self.mdir, *argv)

    def setUp(self):
        super().setUp()
        write_book(self.book, [row("2026-09-30", "2026-10-01", outcome="0")])
        for i in range(10):                                                          # a reference class of 10 eligible days, 4 above the bar: base 0.40
            minute_file(self.mdir, f"2026-09-{i + 1:02d}", 1440, high="85490.01" if i < 4 else "85490")

    def test_target_is_the_next_utc_day_and_the_row_is_canonical(self):
        code, out = self.file("2026-10-09T08:30:00-07:00")                           # Friday morning PT = 15:30Z Friday
        self.assertEqual(code, 0, out)
        r = read(self.book)[-1]
        self.assertEqual((r["date"], r["horizon_days"], r["check_date"], r["instrument"], r["outcome"]), ("2026-10-09", "1", "2026-10-10", "BTC", ""))
        self.assertEqual(r["question"], q("2026-10-10"))
        self.assertTrue(rq.canonical(r))
        self.assertEqual(r["p"], "0.40")
        for token in ("[flow] [tech] [p_cal=", "Resolves check_date+1 (standing, SCHED-001)", "REFERENCE CLASS", "VOID RULE fixed in advance",
                      "trade-bearing minutes", "BARRED FROM TRADING", "S8", "research/minutes/BTC-USD_2026-10-10.csv", self.NOTE,
                      "p = the reference base to two decimals"):
            self.assertIn(token, r["notes"])

    def test_p_is_the_reference_base_and_nothing_else(self):
        code, out = self.file("2026-10-09T08:30:00-07:00", p="0.4")                  # equal in value to 0.40: accepted
        self.assertEqual(code, 0, out)
        self.assertEqual(read(self.book)[-1]["p"], "0.40")
        write_book(self.book, [row("2026-09-30", "2026-10-01", outcome="0")])
        for bad in ("0.43", "0.5", "0.41", "0.399", "abc", ""):
            code, out = self.file("2026-10-09T08:30:00-07:00", p=bad)
            self.assertIn("REFUSED", str(code) + out, bad)
        self.assertEqual(len(read(self.book)), 1)                                    # nothing was written

    def test_no_reference_class_means_no_row(self):
        for f in os.listdir(self.mdir):
            os.remove(os.path.join(self.mdir, f))
        code, out = self.file("2026-10-09T08:30:00-07:00")
        self.assertIn("REFUSED", str(code) + out)
        self.assertIn("no reference base", str(code) + out)
        self.assertEqual(len(read(self.book)), 1)

    def test_s8_uses_the_utc_date_at_filing_not_the_local_date(self):
        code, out = self.file("2026-10-09T20:30:00-07:00")                           # 03:30Z on 10-10: that UTC day has begun
        self.assertEqual(code, 0, out)
        r = read(self.book)[-1]
        self.assertEqual((r["date"], r["check_date"], r["horizon_days"]), ("2026-10-09", "2026-10-11", "2"))

    def test_already_filed_is_a_noop_not_a_refusal(self):
        self.file("2026-10-09T08:30:00-07:00")
        before = rb(self.book)
        code, out = self.file("2026-10-09T10:30:00-07:00")                           # a retry on the same date
        self.assertEqual(code, 0)
        self.assertIn("NOOP", out)
        self.assertNotIn("REFUSED", str(code) + out)
        self.assertEqual(rb(self.book), before)                                      # byte for byte: nothing written
        self.assertEqual(len(read(self.book)), 2)

    def test_one_row_per_resolving_day(self):
        self.file("2026-10-09T08:30:00-07:00")
        code, out = self.file("2026-10-10T08:30:00-07:00")                           # next day: 10-11 is the first free target day
        self.assertEqual(read(self.book)[-1]["check_date"], "2026-10-11")
        write_book(self.book, [row("2026-10-08", "2026-10-10"), row("2026-10-08", "2026-10-11")])
        self.file("2026-10-09T08:30:00-07:00")
        self.assertEqual(read(self.book)[-1]["check_date"], "2026-10-12")            # taken days are skipped
        write_book(self.book, [row("2026-10-08", "2026-10-10", question=q("2026-10-10", x="3"))])
        self.file("2026-10-09T08:30:00-07:00")
        self.assertEqual(read(self.book)[-1]["check_date"], "2026-10-11")            # a non-canonical row still occupies its day

    def test_short_notes_are_refused(self):
        code, out = self.file("2026-10-09T08:30:00-07:00", note="short")
        self.assertIn("REFUSED", str(code) + out)
        self.assertEqual(len(read(self.book)), 1)

    def test_dry_writes_nothing(self):
        before = rb(self.book)
        code, out = self.file("2026-10-09T08:30:00-07:00", None, None, "--dry")
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
    def test_old_rows_stay_byte_identical_after_file_and_after_resolve(self):
        shutil.copy(REAL_BOOK, self.book)
        old = rb(self.book)
        self.assertIn(b"\r\n", old)
        code, out = run(self.book, REAL_MINUTES, "file", "--note", "rehearsal on a COPY of the real book, never the real one",
                        "--now", "2099-06-09T08:30:00-07:00")
        self.assertEqual(code, 0, out)
        new = rb(self.book)
        self.assertTrue(new.startswith(old), "every existing byte of the real book must survive the atomic rewrite")
        self.assertEqual(new[len(old):].count(b"\r\n"), 1)
        self.assertEqual(len(read(self.book)), len(read(REAL_BOOK)) + 1)
        code, out = run(self.book, REAL_MINUTES, "resolve", "--today", "2099-06-30")           # the real tape has no 2099 file: waiting, nothing changes
        self.assertEqual(code, 0, out)
        self.assertEqual(rb(self.book), new)
        self.assertEqual(rb(REAL_BOOK), old if REAL_BOOK == self.book else rb(REAL_BOOK))      # the real book itself was never opened for writing

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
        self.assertEqual((indep_n, indep_k), (23, 10))                              # the numbers the mandate pre-declares
        text = " ".join(open(AGENT_MD, encoding="utf-8").read().split()) if AGENT_MD else ""
        if "THE STANDING QUESTION (CRYPTO-008" in text:                             # once applied, the mandate declares what the tool enforces
            self.assertIn(f"over the {indep_n} eligible complete UTC days to 2026-10-01", text)
            self.assertIn(f"exceeded 3.0% on {indep_k}", text)
            self.assertIn(f"{Decimal(indep_k) / Decimal(indep_n):.3f}", text)
            self.assertIn(rq.QUESTION.format(d="<D>", x="3.0"), text)
            self.assertIn("1,300", text)


if __name__ == "__main__":
    unittest.main()
