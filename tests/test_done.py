import datetime
import os
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import done, paths  # noqa: E402

GOOD = Path(__file__).parent / "fixtures/good.html"
NOW = datetime.datetime(2026, 10, 5, 14, 12, 9, tzinfo=datetime.timezone(datetime.timedelta(hours=9)))


class DoneTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        os.environ["ASTACK_HOME"] = str(self.dir / "home")
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = str(self.dir / "bin")  # rooms 없음
        self.file = self.dir / "x.html"
        shutil.copy(GOOD, self.file)

    def tearDown(self):
        os.environ["PATH"] = self.old_path
        os.environ.pop("ASTACK_HOME", None)
        self.tmp.cleanup()

    def _fake_rooms(self, exit_code: int) -> Path:
        b = self.dir / "bin"
        b.mkdir(exist_ok=True)
        log = self.dir / "rooms-calls"
        f = b / "rooms"
        f.write_text(f'#!/bin/sh\necho "$@" >> "{log}"\nexit {exit_code}\n')
        f.chmod(f.stat().st_mode | stat.S_IEXEC)
        return log

    def test_done_without_rooms(self):
        code, notes = done.done(self.file, "change", now=NOW)
        self.assertEqual(code, 0)
        self.assertEqual(notes, [])
        line = paths.outputs_log().read_text(encoding="utf-8").strip()
        self.assertEqual(line, f"2026-10-05T14:12:09+09:00\tchange\t{self.file.resolve()}")

    def test_done_calls_rooms_link_with_room(self):
        calls = self._fake_rooms(0)
        code, _ = done.done(self.file, "spec", room="alto-rooms", now=NOW)
        self.assertEqual(code, 0)
        self.assertEqual(calls.read_text().strip(), f"link {self.file.resolve()} --room alto-rooms")

    def test_done_when_rooms_fails_is_warning(self):
        self._fake_rooms(3)
        code, notes = done.done(self.file, "spec", now=NOW)
        self.assertEqual(code, 0)
        self.assertTrue(notes and "rooms link" in notes[0])
        self.assertTrue(paths.outputs_log().exists())

    def test_contract_error_blocks_unless_forced(self):
        self.file.write_text(GOOD.read_text(encoding="utf-8").replace('data-astack="source"', ""), encoding="utf-8")
        code, notes = done.done(self.file, "spec", now=NOW)
        self.assertEqual(code, 1)
        self.assertFalse(paths.outputs_log().exists())
        code, _ = done.done(self.file, "spec", force=True, now=NOW)
        self.assertEqual(code, 0)

    def test_skill_with_tab_rejected(self):
        code, notes = done.done(self.file, "a\tb", now=NOW)
        self.assertEqual(code, 1)
        self.assertFalse(paths.outputs_log().exists())
        self.assertTrue(notes and "tab or newline" in notes[0])

    def test_missing_file_rejected(self):
        code, notes = done.done(self.dir / "nonexistent.html", "spec", now=NOW)
        self.assertEqual(code, 1)
        self.assertFalse(paths.outputs_log().exists())
        self.assertTrue(notes and "not a file" in notes[0])


if __name__ == "__main__":
    unittest.main()
