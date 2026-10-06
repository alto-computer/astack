import io
import contextlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli, gate  # noqa: E402

SRC = "<p>Figure 1: a. Fig. 2 shows b. Table 3 and Table A1. Algorithm 1.</p>"


class GateTest(unittest.TestCase):
    def test_labels_normalize(self):
        self.assertEqual(gate.labels("see Fig. 2 and Figure 2, Table A1, Algorithm 3"),
                         {"Figure 2", "Table A1", "Algorithm 3"})

    def test_missing_table(self):
        out = "<p>Figure 1 Figure 2 Algorithm 1 Table 3</p><img src=a><img src=b>"
        miss = gate.paper(out, gate.strip_tags(SRC))
        self.assertEqual(miss, ["Table A1이 결과물에 없다"])

    def test_img_shortage(self):
        out = "<p>Figure 1 Figure 2 Table 3 Table A1 Algorithm 1</p><img src=a>"
        miss = gate.paper(out, gate.strip_tags(SRC))
        self.assertEqual(len(miss), 1)
        self.assertIn("img", miss[0])

    def test_numbers(self):
        out = "<p>Figure 1 Figure 2 Table 3 Table A1 Algorithm 1 92.4</p><img><img>"
        self.assertEqual(gate.paper(out, gate.strip_tags(SRC), ["92.4", "7.7%"]), ["수치 7.7%가 결과물에 없다"])

    def test_ok(self):
        out = "<p>Figure 1 Figure 2 Table 3 Table A1 Algorithm 1</p><img><img>"
        self.assertEqual(gate.paper(out, gate.strip_tags(SRC)), [])


class GateCliTest(unittest.TestCase):
    def run_cli(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli.main(list(argv))
        return code, buf.getvalue()

    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "src.html").write_text(SRC, encoding="utf-8")
            (d / "n.txt").write_text("92.4\n\n", encoding="utf-8")
            (d / "bad.html").write_text("<p>Figure 1</p>", encoding="utf-8")
            (d / "ok.html").write_text("<p>Figure 1 Figure 2 Table 3 Table A1 Algorithm 1 92.4</p><img><img>", encoding="utf-8")
            code, out = self.run_cli("gate", "paper", str(d / "bad.html"), "--source", str(d / "src.html"))
            self.assertEqual(code, 1)
            self.assertIn("빠짐: ", out)
            code, out = self.run_cli("gate", "paper", str(d / "ok.html"), "--source", str(d / "src.html"),
                                     "--numbers", str(d / "n.txt"))
            self.assertEqual((code, out.strip()), (0, "gate: 통과"))


if __name__ == "__main__":
    unittest.main()
