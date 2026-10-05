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

    def test_ext_css_follows_kit_css(self):
        html = GOOD.replace("<style>body{margin:0}</style>", "<!--astack:css-->")
        out = inline.inline_html(html, self.dir)
        self.assertIn("p.why{", out)
        self.assertLess(out.index(".reader{"), out.index("p.why{"))

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

    @unittest.skipUnless(inline.HAS_PYGMENTS, "Pygments 없음")
    def test_auto_lang_uses_file_extension(self):
        html = GOOD.replace("</body>", '<pre data-lang="auto" data-start="1" data-path="src/main.rs"><code>fn main() {}</code></pre></body>')
        out = inline.inline_html(html, self.dir)
        self.assertIn('<span class="k">fn</span>', out)

    @unittest.skipUnless(inline.HAS_PYGMENTS, "Pygments 없음")
    def test_auto_lang_unknown_extension_is_plain(self):
        html = GOOD.replace("</body>", '<pre data-lang="auto" data-path="notes.zzz"><code>fn main() {}</code></pre></body>')
        out = inline.inline_html(html, self.dir)
        self.assertIn('class="cx"', out)
        self.assertNotIn('<span class="k">fn</span>', out)

    def test_non_image_file_not_inlined(self):
        (self.dir / "notes.txt").write_text("secret", encoding="utf-8")
        out = inline.inline_html(GOOD.replace("</body>", '<img src="notes.txt" alt=""></body>'), self.dir)
        self.assertIn('src="notes.txt"', out)
        self.assertNotIn("data:", out.split("<body", 1)[1])

    def test_parent_directory_image_not_inlined(self):
        # Create file outside base_dir
        (self.dir.parent / "secret.png").write_bytes(PNG)
        html = GOOD.replace("</body>", '<img src="../secret.png" alt=""></body>')
        out = inline.inline_html(html, self.dir)
        # Should NOT be converted to data URI
        self.assertNotIn('src="data:image/png;base64,', out)
        # Should still have the src attribute
        self.assertIn('src="../secret.png"', out)

    def test_absolute_path_image_not_inlined(self):
        # Create file with absolute path
        (self.dir / "a.png").write_bytes(PNG)
        abs_path = str((self.dir / "a.png").resolve())
        html = GOOD.replace("</body>", f'<img src="{abs_path}" alt=""></body>')
        out = inline.inline_html(html, self.dir)
        # Should NOT be converted to data URI
        self.assertNotIn('src="data:image/png;base64,', out)
        # Should still have the original src
        self.assertIn(f'src="{abs_path}"', out)

    def test_nested_relative_image_is_inlined(self):
        # Create nested directory with image
        (self.dir / "img").mkdir()
        (self.dir / "img" / "a.png").write_bytes(PNG)
        html = GOOD.replace("</body>", '<img src="img/a.png" alt=""></body>')
        out = inline.inline_html(html, self.dir)
        # Should be converted to data URI
        self.assertIn('src="data:image/png;base64,', out)

    def test_bad_data_start_falls_back_to_1(self):
        html = GOOD.replace("</body>", '<pre data-lang="rust" data-start="x" data-path="test.rs" data-who="Author"><code>code</code></pre></body>')
        out = inline.inline_html(html, self.dir)
        # Should show path with :1 instead of crashing
        self.assertIn("test.rs:1", out)
        self.assertIn('class="cx"', out)

    def test_data_img_becomes_data_uri(self):
        (self.dir / "s1.png").write_bytes(PNG)
        out = inline.inline_html(GOOD.replace("</body>", '<section class="scene" data-img="s1.png"></section></body>'), self.dir)
        self.assertIn('data-img="data:image/png;base64,', out)

    def test_js_marker_includes_quiz(self):
        out = inline.inline_html(GOOD.replace("</body>", "<!--astack:js--></body>"), self.dir)
        self.assertIn("details.quiz", out)

    def test_quiz_js_in_separate_script_element(self):
        out = inline.inline_html(GOOD.replace("</body>", "<!--astack:js--></body>"), self.dir)
        # quiz.js must be in its own <script> element, not concatenated with reader.js
        # Verify that </script><script> appears between reader code and quiz code
        self.assertIn("addEventListener('scroll'", out)  # reader.js code
        self.assertIn("details.quiz", out)  # quiz.js code
        reader_pos = out.index("addEventListener('scroll'")
        quiz_pos = out.index("details.quiz")
        between = out[reader_pos:quiz_pos]
        self.assertIn("</script><script>", between, "quiz.js must be in its own script element")


if __name__ == "__main__":
    unittest.main()
