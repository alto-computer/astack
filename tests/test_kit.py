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
        for name in ("alto.css", "alto-ext.css"):
            css = (KIT / name).read_text(encoding="utf-8")
            self.assertNotIn("http://", css, name)
            self.assertNotIn("https://", css, name)

    def test_ext_css_keeps_one_column_inside_narrow_viewports(self):
        css = (KIT / "alto-ext.css").read_text(encoding="utf-8")
        self.assertIn("grid-template-columns:minmax(0,1fr)", css)
        self.assertIn("p.why{", css)

    def test_js_drives_scroll_sync_toc_and_review_filter(self):
        js = (KIT / "reader.js").read_text(encoding="utf-8")
        for s in ["addEventListener('scroll'", ".toc a", ".rfilter button", ".st span:last-child"]:
            self.assertIn(s, js, s)

    def test_ext_css_has_postit(self):
        css = (KIT / "alto-ext.css").read_text(encoding="utf-8")
        self.assertIn("details.postit", css)


if __name__ == "__main__":
    unittest.main()
