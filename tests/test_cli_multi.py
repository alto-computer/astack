import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli  # noqa: E402

GOOD = Path(__file__).parent / "fixtures/good.html"


class MultiFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        os.environ["ASTACK_HOME"] = str(self.dir / "home")
        os.environ["ASTACK_ROOMS_HOME"] = str(self.dir / "no-rooms")
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = str(self.dir / "bin")  # rooms 없음
        self.folder = self.dir / "out"
        self.folder.mkdir()
        shutil.copy(GOOD, self.folder / "b.html")
        shutil.copy(GOOD, self.folder / "a.html")
        (self.folder / "note.txt").write_text("x", encoding="utf-8")
        self.single = self.dir / "s.html"
        shutil.copy(GOOD, self.single)

    def tearDown(self):
        os.environ["PATH"] = self.old_path
        os.environ.pop("ASTACK_HOME", None)
        os.environ.pop("ASTACK_ROOMS_HOME", None)
        self.tmp.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue().splitlines(), err.getvalue()

    def test_inline_folder_and_file_sorted(self):
        code, out, _ = self.run_cli("inline", str(self.single), str(self.folder))
        self.assertEqual(code, 0)
        self.assertEqual(out, [str(self.single), str(self.folder / "a.html"), str(self.folder / "b.html")])

    def test_done_folder_prints_line_per_file(self):
        code, out, _ = self.run_cli("done", str(self.folder), str(self.single), "--skill", "spec")
        self.assertEqual(code, 0)
        self.assertEqual(out, [str((self.folder / "a.html").resolve()), str((self.folder / "b.html").resolve()),
                               str(self.single.resolve())])

    def test_done_any_failure_exits_1_but_processes_all(self):
        (self.folder / "a.html").write_text("<p>no contract</p>", encoding="utf-8")
        code, out, err = self.run_cli("done", str(self.folder), "--skill", "spec")
        self.assertEqual(code, 1)
        self.assertEqual(out, [str((self.folder / "b.html").resolve())])
        self.assertIn("a.html", err)


    def test_done_empty_folder_is_error(self):
        empty = self.dir / "empty"
        empty.mkdir()
        code, out, err = self.run_cli("done", str(empty), "--skill", "spec")
        self.assertEqual(code, 1)
        self.assertEqual(out, [])
        self.assertIn(f"astack done: {empty}: html 없음", err)

    def test_done_missing_file_named_once(self):
        missing = self.dir / "nope.html"
        code, _, err = self.run_cli("done", str(missing), "--skill", "spec")
        self.assertEqual(code, 1)
        self.assertEqual(err.count("nope.html"), 1, err)

if __name__ == "__main__":
    unittest.main()
