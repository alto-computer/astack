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


if __name__ == "__main__":
    unittest.main()
