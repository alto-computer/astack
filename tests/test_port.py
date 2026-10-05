import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from astack_cli import check, inline  # noqa: E402

spec = importlib.util.spec_from_file_location("port_template", ROOT / "tools/port_template.py")
port_template = importlib.util.module_from_spec(spec)
spec.loader.exec_module(port_template)

SRC = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>옛 제목</title>
<style>:root{--accent:#3a5a7c}</style>
</head><body>
<header class="cover"><img src="images/masthead.jpg" alt=""></header>
<section class="standfirst">리드</section>
<section class="scene" data-img="01_slide.jpg"><img src="{{SLIDE_DATAURI}}"></section>
<footer class="foot">화자</footer>
<script>var x=1</script>
</body></html>"""


class PortTest(unittest.TestCase):
    def setUp(self):
        self.out = port_template.port(SRC, "/* alto */ .x{}", "[제목] — 인터뷰",
                                      [('<header class="cover">', "30s"), ('<section class="standfirst">', "3m"), ('<footer class="foot">', "source")],
                                      source_footer="")

    def test_astack_metas_come_first_in_head(self):
        head = self.out.split("<head>", 1)[1]
        self.assertTrue(head.lstrip().startswith('<meta charset="utf-8">\n<meta name="description"'))
        self.assertIn('<meta name="rooms:machine" content="[머신 이름]">', head)

    def test_override_css_is_appended_inside_first_style(self):
        style = self.out.split("<style>", 1)[1].split("</style>", 1)[0]
        self.assertTrue(style.rstrip().endswith("/* alto */ .x{}"))
        self.assertIn("--accent:#3a5a7c", style)

    def test_markers_title_and_images(self):
        self.assertIn('<header class="cover" data-astack="30s">', self.out)
        self.assertIn('<footer class="foot" data-astack="source">', self.out)
        self.assertIn("<title>[제목] — 인터뷰</title>", self.out)
        self.assertNotIn('src="images/', self.out)
        self.assertIn("그림 자리: images/masthead.jpg", self.out)
        self.assertNotIn('src="{{', self.out)
        self.assertIn('data-img=""', self.out)

    def test_script_untouched(self):
        self.assertIn("<script>var x=1</script>", self.out)

    def test_missing_marker_is_error(self):
        with self.assertRaises(ValueError):
            port_template.port(SRC, "", "t", [('<nav class="nope">', "3m")], "")

    def test_footer_added_when_source_footer_given(self):
        out = port_template.port(SRC.replace('<footer class="foot">화자</footer>', ""), "", "t",
                                 [('<header class="cover">', "30s"), ('<section class="standfirst">', "3m")],
                                 source_footer='<footer class="astack-source" data-astack="source">원본</footer>')
        self.assertIn('data-astack="source">원본</footer>\n</body>', out)


class GeneratedTemplatesTest(unittest.TestCase):
    def test_generated_templates_keep_one_title_and_markers(self):
        for name in ("interview", "seminar"):
            t = ROOT / f"skills/{name}/assets/template.html"
            html = t.read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertEqual(html.count("<title>"), 1)
                for layer in ("30s", "3m", "source"):
                    self.assertIn(f'data-astack="{layer}"', html)
                self.assertIn("#e31c5f", html)  # Alto 실이 덮였다


if __name__ == "__main__":
    unittest.main()
