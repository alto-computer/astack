import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1] / "skills/design/assets"


class KitTest(unittest.TestCase):
    def test_css_has_reference_components(self):
        css = (KIT / "alto.css").read_text(encoding="utf-8")
        for sel in [".reader", ".stage", ".toc", ".dg .e.on", ".hl .linenos", ".wrong", ".kc", "table.rv", "table.ustab", ".scene.lvl3"]:
            self.assertIn(sel, css, sel)
        self.assertIn("#e31c5f", css)

    def test_css_has_no_external_urls(self):
        css = (KIT / "alto.css").read_text(encoding="utf-8")
        self.assertNotIn("http://", css)
        self.assertNotIn("https://", css)

    def test_js_drives_scroll_sync_toc_and_review_filter(self):
        js = (KIT / "reader.js").read_text(encoding="utf-8")
        for s in ["addEventListener('scroll'", ".toc a", ".rfilter button", ".st span:last-child"]:
            self.assertIn(s, js, s)


if __name__ == "__main__":
    unittest.main()
