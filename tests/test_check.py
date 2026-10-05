import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import check  # noqa: E402

GOOD = (Path(__file__).parent / "fixtures/good.html").read_text(encoding="utf-8")


def codes(html, level="error"):
    return [i.code for i in check.check_html(html) if i.level == level]


class CheckTest(unittest.TestCase):
    def test_good_fixture_has_no_errors(self):
        self.assertEqual(codes(GOOD), [])

    def test_missing_meta_fails(self):
        html = GOOD.replace('<meta name="rooms:machine" content="MacBook-Pro">', "")
        self.assertIn("meta", codes(html))

    def test_created_must_be_rfc3339(self):
        html = GOOD.replace("2026-10-05T14:12:09+09:00", "yesterday")
        msgs = [i.message for i in check.check_html(html) if i.code == "meta"]
        self.assertTrue(any("RFC3339" in m for m in msgs), msgs)

    def test_meta_after_64kb_fails(self):
        big = "<style>" + ("a{}" * 30000) + "</style>"
        html = GOOD.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + big)
        msgs = [i.message for i in check.check_html(html) if i.code == "meta"]
        self.assertTrue(any("64KB" in m for m in msgs), msgs)

    def test_stray_title_in_body_fails(self):
        html = GOOD.replace("&lt;title&gt;이라는", "<title>이라는")
        self.assertIn("title", codes(html))

    def test_external_files_fail_but_links_pass(self):
        for bad in ['<script src="x.js"></script>', '<img src="images/a.png">',
                    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jost">',
                    '<div style="background:url(a.png)"></div>']:
            html = GOOD.replace("</body>", bad + "</body>")
            self.assertIn("external", codes(html), bad)
        ok = GOOD.replace("</body>", '<img src="data:image/png;base64,AAA="><svg><path marker-end="url(#ar)"/></svg></body>')
        self.assertEqual(codes(ok), [])

    def test_layers_and_source_required(self):
        self.assertIn("layer", codes(GOOD.replace('data-astack="3m"', "")))
        self.assertIn("source", codes(GOOD.replace('data-astack="source"', "")))

    def test_unreplaced_marker_fails(self):
        self.assertIn("marker", codes(GOOD.replace("</head>", "<!--astack:css--></head>")))

    def test_slop_and_long_sentence_are_warnings(self):
        html = GOOD.replace("<p>바뀐 곳은 두 군데다.</p>",
                            "<p>핵심은 이것이다. " + "아주 " * 30 + "긴 문장이다. 끝.</p>")
        self.assertEqual(codes(html), [])
        self.assertIn("slop", codes(html, "warn"))
        self.assertIn("long", codes(html, "warn"))

    def test_code_and_pre_are_not_prose(self):
        text = check.prose_text("<p>보인다.</p><pre>핵심은 숨김</pre><code>매우 숨김</code>")
        self.assertIn("보인다", text)
        self.assertNotIn("숨김", text)


if __name__ == "__main__":
    unittest.main()
