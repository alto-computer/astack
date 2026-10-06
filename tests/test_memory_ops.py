import datetime
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli, memory, paths  # noqa: E402

D = datetime.date(2026, 10, 5)


def rec(**kw):
    base = {"type": "correction", "key": "skill:interview", "insight": "x", "source": "told", "date": "2026-10-01", "host": "h"}
    base.update(kw)
    return json.dumps(base, ensure_ascii=False)


class MemoryOpsBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get("ASTACK_HOME")
        os.environ["ASTACK_HOME"] = self.tmp.name

    def tearDown(self):
        if self.old is None:
            os.environ.pop("ASTACK_HOME", None)
        else:
            os.environ["ASTACK_HOME"] = self.old
        self.tmp.cleanup()

    def write(self, *lines):
        paths.memory_file().write_text("".join(l + "\n" for l in lines), encoding="utf-8")


class PruneTest(MemoryOpsBase):
    def test_prune_by_key_prefix_and_archives(self):
        self.write(rec(key="channel:a"), rec(key="channel:b"), rec(key="skill:x"))
        self.assertEqual(memory.prune(key="channel:", today=D), 2)
        keys = [r["key"] for r in memory.parse(memory.read_lines())]
        self.assertEqual(keys, ["skill:x"])
        self.assertEqual(len((paths.archive_dir() / "2026-10-05.jsonl").read_text().splitlines()), 3)

    def test_prune_by_type_and_before(self):
        self.write(rec(type="taste", source="observed", date="2026-08-01"), rec(type="taste", source="observed", date="2026-10-04"))
        self.assertEqual(memory.prune(type_="taste", before="2026-09-01", today=D), 1)

    def test_prune_needs_a_filter(self):
        self.write(rec())
        with self.assertRaises(ValueError):
            memory.prune(today=D)

    def test_restore_brings_back_archive(self):
        self.write(rec(key="a"), rec(key="b"))
        memory.prune(key="a", today=D)
        memory.restore("2026-10-05", today=D)
        self.assertEqual(len(memory.read_lines()), 2)

    def test_restore_missing_date_is_error(self):
        with self.assertRaises(FileNotFoundError):
            memory.restore("2026-01-01", today=D)

    def test_archive_keeps_first_state_of_the_day(self):
        self.write(rec(key="a"))
        memory.archive(D)
        self.write(rec(key="a"), rec(key="b"))
        memory.archive(D)
        self.assertEqual(len((paths.archive_dir() / "2026-10-05.jsonl").read_text().splitlines()), 1)


class SafetyTest(MemoryOpsBase):
    def test_unicode_line_separator_survives_prune(self):
        sep = "a\u2028b\u0085c\x1cd"
        self.write(rec(key="gone"), rec(key="keep", insight=sep))
        self.assertEqual(memory.prune(key="gone", today=D), 1)
        recs = memory.parse(memory.read_lines())
        self.assertEqual([r["key"] for r in recs], ["keep"])
        self.assertEqual(recs[0]["insight"], sep)

    def test_restore_leaves_pre_restore_copy(self):
        self.write(rec(key="a"), rec(key="b"))
        memory.prune(key="a", today=D)
        with open(paths.memory_file(), "a", encoding="utf-8") as f:
            f.write(rec(key="added") + "\n")
        memory.restore("2026-10-05", today=D)
        pre = list(paths.archive_dir().glob("2026-10-05.pre-restore-*.jsonl"))
        self.assertEqual(len(pre), 1)
        self.assertIn('"added"', pre[0].read_text())

    def test_restore_keeps_appended_tail(self):
        self.write(rec(key="a"))
        memory.archive(D)
        orig = memory._tail
        calls = []

        def spy(size):
            if not calls:  # 스냅샷과 교체 사이에 add가 끼어든 상황
                with open(paths.memory_file(), "a", encoding="utf-8") as f:
                    f.write(rec(key="late") + "\n")
                calls.append(1)
            return orig(size)

        memory._tail = spy
        try:
            memory.restore("2026-10-05", today=D)
        finally:
            memory._tail = orig
        keys = [r["key"] for r in memory.parse(memory.read_lines())]
        self.assertEqual(keys, ["a", "late"])

    def test_archive_is_atomic_no_tmp_left(self):
        self.write(rec())
        a = memory.archive(D)
        self.assertFalse(a.with_name(a.name + ".tmp").exists())

    def test_files_are_0600(self):
        self.write(rec(key="a"), rec(key="b"))
        memory.prune(key="a", today=D)
        self.assertEqual(stat.S_IMODE(paths.memory_file().stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((paths.archive_dir() / "2026-10-05.jsonl").stat().st_mode), 0o600)
        memory.restore("2026-10-05", today=D)
        self.assertEqual(stat.S_IMODE(paths.memory_file().stat().st_mode), 0o600)

    def test_restore_rejects_bad_date(self):
        for bad in ("../memory", "x", "2026-13-01"):
            with self.assertRaises(ValueError):
                memory.restore(bad, today=D)


class LockTest(MemoryOpsBase):
    def test_lock_is_exclusive(self):
        with memory.lock():
            with self.assertRaises(memory.MemoryLocked):
                with memory.lock():
                    pass
        self.assertFalse(paths.lock_file().exists())

    def test_stale_lock_is_cleared(self):
        paths.lock_file().write_text("1")
        old = paths.lock_file().stat().st_mtime - 3600
        os.utime(paths.lock_file(), (old, old))
        with memory.lock():
            pass

    def test_replace_lines_keeps_appended_tail(self):
        self.write(rec(key="a"))
        size = paths.memory_file().stat().st_size
        with open(paths.memory_file(), "a", encoding="utf-8") as f:
            f.write(rec(key="late") + "\n")
        memory.replace_lines([rec(key="a2")], since_size=size)
        keys = [r["key"] for r in memory.parse(memory.read_lines())]
        self.assertEqual(keys, ["a2", "late"])


class CliTest(MemoryOpsBase):
    def test_cli_prune_and_restore(self):
        self.write(rec(key="channel:a"), rec(key="skill:x"))
        self.assertEqual(cli.main(["memory", "prune", "--key", "channel:"]), 0)
        self.assertEqual(cli.main(["memory", "prune"]), 2)
        today = datetime.date.today().isoformat()
        self.assertEqual(cli.main(["memory", "restore", today]), 0)
        self.assertEqual(cli.main(["memory", "restore", "1999-01-01"]), 2)

    def test_cli_add_still_works(self):
        self.assertEqual(cli.main(["memory", "add", '{"type":"preference","key":"k","insight":"i","source":"told"}']), 0)


class SearchCliTest(MemoryOpsBase):
    def test_zero_results_say_so_on_stderr(self):
        import contextlib
        import io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(cli.main(["memory", "search", "skill:없음"]), 0)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("결과 없음", err.getvalue())


class ConsolidateTest(MemoryOpsBase):
    def keys(self):
        return [(r["type"], r["key"]) for r in memory.parse(memory.read_lines())]

    def test_duplicates_merge_to_latest(self):
        self.write(rec(date="2026-10-01"), rec(date="2026-10-03"))
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["merged"], 1)
        self.assertEqual([r["date"] for r in memory.parse(memory.read_lines())], ["2026-10-03"])

    def test_newer_told_supersedes_observed(self):
        self.write(rec(type="taste", key="topic:a", source="observed", date="2026-10-01", confidence=0.9),
                   rec(type="preference", key="topic:a", source="told", date="2026-10-02"))
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["superseded"], ["topic:a"])
        self.assertEqual(self.keys(), [("preference", "topic:a")])

    def test_decay_is_not_compounded(self):
        self.write(rec(type="taste", key="topic:b", source="observed", date="2026-09-05", confidence=0.8))
        memory.consolidate(today=D)
        memory.consolidate(today=D)
        r = memory.parse(memory.read_lines())[0]
        self.assertEqual((r["confidence0"], r["confidence"]), (0.8, 0.4))

    def test_old_observed_is_dropped(self):
        self.write(rec(type="taste", key="topic:c", source="observed", date="2026-06-01", confidence=0.5))
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["dropped"], ["topic:c"])
        self.assertEqual(self.keys(), [])

    def test_told_is_kept_regardless_of_age(self):
        self.write(rec(type="exclude", key="channel:z", source="told", date="2025-01-01"))
        memory.consolidate(today=D)
        self.assertEqual(self.keys(), [("exclude", "channel:z")])

    def test_repeated_corrections_promote_once(self):
        self.write(rec(insight="a", date="2026-10-01"), rec(insight="b", date="2026-10-02"), rec(insight="c", date="2026-10-03"))
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["promoted"], ["skill:interview"])
        self.assertEqual(rep["patch_suggestions"][0]["count"], 3)
        rep2 = memory.consolidate(today=D)
        self.assertEqual(rep2["promoted"], [])
        self.assertEqual(sum(1 for t, _ in self.keys() if t == "preference"), 1)

    def test_broken_lines_survive_in_archive(self):
        self.write(rec(key="ok"), "{not json")
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["broken"], 1)
        self.assertIn("{not json", (paths.archive_dir() / "2026-10-05.jsonl").read_text())
        self.assertIn("{not json", memory.read_lines())

    def test_broken_and_non_dict_lines_stay_in_live_file(self):
        hand = '{"type":"taste","key":"k","insight":"x","source":"told",}'
        self.write(rec(key="ok"), hand, "[1,2]", '"str"')
        rep = memory.consolidate(today=D)
        self.assertEqual((rep["broken"], rep["after"]), (3, 4))
        lines = memory.read_lines()
        for raw in (hand, "[1,2]", '"str"'):
            self.assertIn(raw, lines)

    def test_invalid_utf8_bytes_survive_rewrite(self):
        good = rec(type="taste", key="topic:z", source="observed", date="2026-09-05", confidence=0.8).encode()
        bad_rec = good.replace(b'"x"', b'"x\xff"')
        self.assertNotEqual(bad_rec, good)
        paths.memory_file().write_bytes(bad_rec + b"\n" + b"{broken \xfe\n")
        memory.consolidate(today=D)
        data = paths.memory_file().read_bytes()
        self.assertIn(b"x\xff", data)
        self.assertIn(b"{broken \xfe", data)
        self.assertNotIn("\ufffd".encode(), data)

    def test_identical_corrections_promote(self):
        self.write(*(rec(insight="짧게", date=f"2026-10-0{i}") for i in (1, 2, 3)))
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["promoted"], ["skill:interview"])
        self.assertEqual(rep["patch_suggestions"][0]["count"], 3)
        pref = [r for r in memory.parse(memory.read_lines()) if r["type"] == "preference"]
        self.assertEqual(pref[0]["promoted_from"], 3)
        self.assertEqual(pref[0]["insight"], "규칙: 짧게")

    def test_identical_corrections_promote_across_daily_runs(self):
        for i in (1, 2, 3):
            with open(paths.memory_file(), "a", encoding="utf-8") as f:
                f.write(rec(insight="짧게", date=f"2026-10-0{i}") + "\n")
            rep = memory.consolidate(today=datetime.date(2026, 10, i))
        self.assertEqual(rep["promoted"], ["skill:interview"])
        corr = [r for r in memory.parse(memory.read_lines()) if r["type"] == "correction"]
        self.assertEqual(len(corr), 1)

    def test_observed_corrections_are_not_promoted(self):
        self.write(*(rec(insight=n, source="observed", date="2026-10-0" + str(i), confidence=0.6)
                     for i, n in ((1, "a"), (2, "b"), (3, "c"))))
        rep = memory.consolidate(today=D)
        self.assertEqual((rep["promoted"], rep["patch_suggestions"]), ([], []))
        out = memory.parse(memory.read_lines())
        self.assertFalse([r for r in out if r["type"] == "preference"])
        self.assertTrue(all(r["confidence"] < 0.6 for r in out))

    def test_observed_corrections_do_not_count_toward_told(self):
        self.write(rec(insight="a", date="2026-10-01"), rec(insight="b", date="2026-10-02"),
                   rec(insight="c", source="observed", date="2026-10-03", confidence=0.9))
        self.assertEqual(memory.consolidate(today=D)["promoted"], [])

    def test_dry_run_changes_nothing(self):
        self.write(rec(date="2026-10-01"), rec(date="2026-10-03"))
        before = paths.memory_file().read_text()
        memory.consolidate(today=D, dry_run=True)
        self.assertEqual(paths.memory_file().read_text(), before)

    def test_append_during_consolidate_is_kept(self):
        self.write(rec(key="a"))
        real = memory.replace_lines

        def racing(lines, since_size):
            with open(paths.memory_file(), "a", encoding="utf-8") as f:
                f.write(rec(key="late") + "\n")
            real(lines, since_size)

        memory.replace_lines = racing
        try:
            memory.consolidate(today=D)
        finally:
            memory.replace_lines = real
        self.assertIn(("correction", "late"), self.keys())

    def test_second_consolidate_same_day_archives_snapshot(self):
        self.write(rec(key="a"))
        memory.consolidate(today=D)
        with open(paths.memory_file(), "a", encoding="utf-8") as f:
            f.write("{broken\n")
        memory.consolidate(today=D)
        texts = [p.read_text() for p in paths.archive_dir().glob("2026-10-05*.jsonl")]
        self.assertTrue(any("{broken" in t for t in texts))

    def test_unreadable_records_pass_through(self):
        a = rec(insight=["x"])
        b = json.dumps({"type": "taste", "insight": "no key", "source": "observed", "date": "2020-01-01"})
        c = rec(type="taste", key="k", source="observed", date="2026-10-01", confidence="0.5")
        self.write(a, b, c)
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["kept_unreadable"], 2)
        out = memory.parse(memory.read_lines())
        self.assertEqual(len(out), 3)
        self.assertIn({"type": "taste", "key": "k", "insight": "x", "source": "observed", "date": "2026-10-01",
                       "host": "h", "confidence": "0.5"}, out)

    def test_records_missing_insight_are_not_deduped(self):
        a = json.dumps({"type": "taste", "key": "k", "source": "told", "date": "2026-10-01", "n": 1})
        b = json.dumps({"type": "taste", "key": "k", "source": "told", "date": "2026-10-01", "n": 2})
        self.write(a, b)
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["merged"], 0)
        self.assertEqual(len(memory.parse(memory.read_lines())), 2)

    def test_blank_lines_not_counted(self):
        self.write(rec(), "", "   ")
        rep = memory.consolidate(today=D, dry_run=True)
        self.assertEqual((rep["before"], rep["broken"]), (1, 0))

    def test_cli_consolidate_prints_report(self):
        self.write(rec())
        self.assertEqual(cli.main(["memory", "consolidate", "--dry-run"]), 0)


class RestoreNameTest(MemoryOpsBase):
    def test_restore_by_archive_name_reaches_second_snapshot(self):
        self.write(rec(key="a"), rec(key="b"), rec(key="c"))
        memory.prune(key="a", today=D)
        memory.prune(key="c", today=D)
        snaps = [p for p in paths.archive_dir().glob("2026-10-05.*.jsonl")]
        self.assertEqual(len(snaps), 1)
        name = snaps[0].name[:-len(".jsonl")]
        memory.restore(name, today=D)
        self.assertEqual([r["key"] for r in memory.parse(memory.read_lines())], ["b", "c"])
        memory.restore(snaps[0].name, today=D)  # .jsonl을 붙여도 된다
        self.assertEqual([r["key"] for r in memory.parse(memory.read_lines())], ["b", "c"])

    def test_restore_reaches_pre_restore_copy(self):
        self.write(rec(key="a"), rec(key="b"))
        memory.prune(key="a", today=D)
        memory.restore("2026-10-05", today=D)
        pre = next(paths.archive_dir().glob("2026-10-05.pre-restore-*.jsonl"))
        memory.restore(pre.name[:-len(".jsonl")], today=D)
        self.assertEqual([r["key"] for r in memory.parse(memory.read_lines())], ["b"])

    def test_restore_rejects_names_outside_archive(self):
        for bad in ("2026-10-05.abc", "2026-10-05/../../memory", "2026-10-05.pre-restore-", "../2026-10-05"):
            with self.assertRaises(ValueError, msg=bad):
                memory.restore(bad, today=D)

    def test_archives_newest_first(self):
        d = paths.archive_dir()
        d.mkdir(parents=True)
        for i, n in enumerate(["2026-10-04", "2026-10-05", "2026-10-05.120000000000", "2026-10-05.pre-restore-130000000000"]):
            (d / f"{n}.jsonl").write_text(rec() + "\n")
            os.utime(d / f"{n}.jsonl", (1000 + i, 1000 + i))
        (d / "notes.txt").write_text("x")
        self.assertEqual(memory.archives(), ["2026-10-05.pre-restore-130000000000", "2026-10-05.120000000000",
                                             "2026-10-05", "2026-10-04"])
        self.assertEqual(memory.archives("2026-10-05")[-1], "2026-10-05")

    def test_cli_list_and_bare_date_warning(self):
        import contextlib
        import io
        self.write(rec(key="a"), rec(key="b"), rec(key="c"))
        today = datetime.date.today()
        memory.prune(key="a", today=today)
        memory.prune(key="b", today=today)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["memory", "restore", "--list"]), 0)
        self.assertEqual(len(out.getvalue().splitlines()), 2)
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.assertEqual(cli.main(["memory", "restore", today.isoformat()]), 0)
        self.assertIn("--list", err.getvalue())

    def test_two_restores_in_same_second_keep_both_copies(self):
        self.write(rec(key="s0"))
        memory.archive(D)
        self.write(rec(key="s1"))
        stamps = iter(["120000000000", "120000000000", "120000000001"])
        orig = memory._stamp
        memory._stamp = lambda: next(stamps)
        try:
            memory.restore("2026-10-05", today=D)
            memory.restore("2026-10-05", today=D)
        finally:
            memory._stamp = orig
        pre = sorted(paths.archive_dir().glob("2026-10-05.pre-restore-*.jsonl"))
        self.assertEqual(len(pre), 2)
        self.assertTrue(any('"s1"' in p.read_text() for p in pre))


    def test_design_skill_documents_restore_names(self):
        skill = (Path(__file__).resolve().parents[1] / "skills/design/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("astack memory restore --list", skill)
        self.assertIn("astack memory restore <이름>", skill)
        self.assertIn("접두사 일치", skill)


class PruneGuardTest(MemoryOpsBase):
    def test_before_must_be_iso_date(self):
        self.write(rec(date="2026-10-01"))
        before = paths.memory_file().read_bytes()
        for bad in ("yesterday", "어제", "2026-9-1", "2026-10-01T00:00", "2026-13-01"):
            with self.assertRaises(ValueError, msg=bad):
                memory.prune(before=bad, today=D)
        self.assertEqual(paths.memory_file().read_bytes(), before)
        self.assertFalse(paths.archive_dir().exists())

    def test_before_skips_records_without_valid_date(self):
        no_date = json.dumps({"type": "taste", "key": "k", "insight": "i", "source": "observed"})
        self.write(rec(key="old", date="2026-08-01"), rec(key="blank", date=""), rec(key="odd", date="last week"), no_date)
        self.assertEqual(memory.prune(before="2026-09-01", today=D), 1)
        self.assertEqual([r["key"] for r in memory.parse(memory.read_lines())], ["blank", "odd", "k"])

    def test_unknown_type_is_error(self):
        self.write(rec())
        with self.assertRaises(ValueError):
            memory.prune(type_="corection", today=D)

    def test_cli_bad_before_exits_2(self):
        self.write(rec())
        self.assertEqual(cli.main(["memory", "prune", "--before", "yesterday"]), 2)
        self.assertEqual(len(memory.read_lines()), 1)

    def test_prune_with_no_hit_writes_no_archive(self):
        self.write(rec(key="a"))
        self.assertEqual(memory.prune(key="zzz", today=D), 0)
        self.assertFalse(paths.archive_dir().exists())


class SymlinkTest(MemoryOpsBase):
    def setUp(self):
        super().setUp()
        self.real = Path(self.tmp.name) / "sync" / "memory.jsonl"
        self.real.parent.mkdir()
        self.real.write_text(rec(key="a") + "\n" + rec(key="b") + "\n", encoding="utf-8")
        os.chmod(self.real, 0o600)
        paths.memory_file().symlink_to(self.real)

    def test_prune_consolidate_restore_keep_the_link(self):
        memory.prune(key="a", today=D)
        self.assertTrue(paths.memory_file().is_symlink())
        self.assertNotIn('"a"', self.real.read_text())
        memory.consolidate(today=D)
        self.assertTrue(paths.memory_file().is_symlink())
        memory.restore("2026-10-05", today=D)
        self.assertTrue(paths.memory_file().is_symlink())
        self.assertIn('"a"', self.real.read_text())
        self.assertEqual(stat.S_IMODE(self.real.stat().st_mode), 0o600)
        self.assertEqual(list(self.real.parent.glob("*.tmp")), [])


class DurableWriteTest(MemoryOpsBase):
    def test_atomic_write_fsyncs_and_writes_everything(self):
        calls = []
        orig = os.fsync
        os.fsync = lambda fd: calls.append(fd)
        try:
            data = b"x" * (1 << 20)
            memory._write_atomic(Path(self.tmp.name) / "big", data)
        finally:
            os.fsync = orig
        self.assertEqual((Path(self.tmp.name) / "big").read_bytes(), data)
        self.assertGreaterEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()


class ReportTest(MemoryOpsBase):
    def _rep(self, **kw):
        base = {"before": 5, "after": 3, "merged": 1, "superseded": ["a:x"], "decayed": [["b:y", 0.8, 0.5]],
                "dropped": ["c:z"], "promoted": ["skill:p"],
                "patch_suggestions": [{"key": "skill:p", "count": 3, "insights": ["i1", "i2"]}],
                "broken": 0, "kept_unreadable": 0}
        base.update(kw)
        return base

    def test_report_passes_check(self):
        from astack_cli import check, inline
        html = memory.render_report(self._rep(), D)
        html = inline.inline_html(html, Path(self.tmp.name))
        errs = [i for i in check.check_html(html) if i.level == "error"]
        self.assertEqual(errs, [])
        self.assertIn("기록 5→3, 합침 1, 대체 1, 감쇠 1, 지움 1, 승격 1", html)
        self.assertIn("제안", html)
        self.assertIn("자동 적용", html)

    def test_report_unchanged(self):
        rep = self._rep(before=2, after=2, merged=0, superseded=[], decayed=[], dropped=[], promoted=[], patch_suggestions=[])
        self.assertIn("바뀐 것 없음", memory.render_report(rep, D))

    def test_report_escapes(self):
        html = memory.render_report(self._rep(dropped=["<b>x</b>"]), D)
        self.assertNotIn("<b>x</b>", html)

    def test_cli_html_writes_file(self):
        self.write(rec(), rec(insight="y"))
        out = Path(self.tmp.name) / "r.html"
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli.main(["memory", "consolidate", "--html", str(out)])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), str(out))
        self.assertIn("<style>", out.read_text(encoding="utf-8"))

    def test_cli_quiet_if_unchanged(self):
        self.write(rec())
        out = Path(self.tmp.name) / "r.html"
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli.main(["memory", "consolidate", "--html", str(out), "--quiet-if-unchanged"])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue(), "")
        self.assertFalse(out.exists())
