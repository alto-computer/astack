import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli  # noqa: E402


class CliCheckTest(unittest.TestCase):
    def test_missing_file_exits_2_without_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cli.main(["check", str(Path(d) / "nope.html")]), 2)

    def test_non_utf8_file_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "bad.html"
            f.write_bytes(b"\xff\xfe\x00bad")
            self.assertEqual(cli.main(["check", str(f)]), 2)


if __name__ == "__main__":
    unittest.main()
