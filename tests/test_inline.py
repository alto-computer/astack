import base64
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import check, inline  # noqa: E402

GOOD = (Path(__file__).parent / "fixtures/good.html").read_text(encoding="utf-8")
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


class InlineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_markers_become_inline_kit(self):
        html = GOOD.replace("<style>body{margin:0}</style>", "<!--astack:css-->").replace("</body>", "<!--astack:js--></body>")
        out = inline.inline_html(html, self.dir)
        self.assertNotIn("<!--astack:", out)
        self.assertIn(".reader", out)
        self.assertIn("addEventListener('scroll'", out)

    def test_relative_image_becomes_data_uri(self):
        (self.dir / "a.png").write_bytes(PNG)
        out = inline.inline_html(GOOD.replace("</body>", '<img src="a.png" alt=""></body>'), self.dir)
        self.assertIn('src="data:image/png;base64,', out)
        self.assertNotIn("external", [i.code for i in check.check_html(out)])

    def test_inline_keeps_meta_first(self):
        html = GOOD.replace("<style>body{margin:0}</style>", "<!--astack:css-->").replace("</body>", "<!--astack:js--></body>")
        out = inline.inline_html(html, self.dir)
        self.assertEqual([i.code for i in check.check_html(out) if i.level == "error"], [])

    def test_code_block_gets_header_and_line_numbers(self):
        html = GOOD.replace("</body>", '<pre data-lang="rust" data-start="270" data-path="crates/c.rs" data-who="RoomsCore"><code>fn a() {}\nlet b = 1;</code></pre></body>')
        out = inline.inline_html(html, self.dir)
        self.assertIn('class="cx"', out)
        self.assertIn("crates/c.rs:270", out)
        self.assertIn("RoomsCore", out)
        if inline.HAS_PYGMENTS:
            self.assertIn('class="linenos"', out)
            self.assertIn(">271<", out)


if __name__ == "__main__":
    unittest.main()
