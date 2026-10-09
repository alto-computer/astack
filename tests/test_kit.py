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

    def test_quiz_js_grades_and_has_no_storage(self):
        js = (KIT / "quiz.js").read_text(encoding="utf-8")
        for s in ["details.quiz", "data-ok", "data-why", ".verdict"]:
            self.assertIn(s, js, s)
        for banned in ["localStorage", "sessionStorage", "indexedDB", "fetch("]:
            self.assertNotIn(banned, js, banned)

    def test_ext_css_sizes_stage_figures(self):
        css = (KIT / "alto-ext.css").read_text(encoding="utf-8")
        self.assertIn(".vis img,.vis svg{display:block;max-width:100%;height:auto;margin:0 auto}", css)
        self.assertIn(".stage .vis img{max-height:calc(100vh - 190px);object-fit:contain}", css)

    def test_open_postit_sets_text_color(self):
        css = (KIT / "alto-ext.css").read_text(encoding="utf-8")
        rule = css.split("details.postit[open]{", 1)[1].split("}", 1)[0]
        self.assertIn("color:var(--ink)", rule)

    def test_ext_css_styles_quiz(self):
        css = (KIT / "alto-ext.css").read_text(encoding="utf-8")
        self.assertIn("details.quiz", css)

    def test_readability_values(self):
        css = (KIT / "alto-ext.css").read_text(encoding="utf-8")
        for s in ("--measure:680px", "body{font-size:16px;",
                  ".cover h1{font-size:clamp(28px,3.2vw,40px);font-weight:600",
                  '--jost:"Pretendard","Apple SD Gothic Neo",system-ui',
                  ".overview p,.overview li{color:var(--ink)}", ".overview.one{display:block",
                  "pre code{font-size:inherit}", "pre,.wrong pre,.apx pre{font-size:13px}",
                  "table.ustab,table.cmp,table.rv,.apx table{font-size:15px}",
                  ".reader{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr)!important}",
                  ".stage,.codepane{justify-content:flex-start}",
                  ".src{display:block;font-size:13px", ".prose", ".point h3"):
            self.assertIn(s, css, s)
        rule = css.split(".wrap>section:not(.overview)", 1)[1].split("}", 1)[0]
        for s in (".wrap>footer", ".prose", "max-width:var(--measure)"):
            self.assertIn(s, rule)

    def test_ev_pills_are_grey_text_except_bad(self):
        css = (KIT / "alto-ext.css").read_text(encoding="utf-8")
        rule = css.split(".ev:not(.ev-bad){", 1)[1].split("}", 1)[0]
        self.assertIn("background:none", rule)
        self.assertIn("color:var(--ink-2)", rule)
        self.assertNotIn(".ev-bad{", css)

    def test_reader_ratio_precedes_narrow_override(self):
        css = (KIT / "alto-ext.css").read_text(encoding="utf-8")
        self.assertLess(css.index("minmax(0,1.15fr) minmax(0,1fr)"), css.index("@media (max-width:900px)"))

    def test_alto_css_is_untouched_reference_extract(self):
        css = (KIT / "alto.css").read_text(encoding="utf-8")
        self.assertTrue(css.startswith("/* extracted from spec-reference-rooms-v1.html"))
        self.assertIn(".cover h1{margin:0;font-size:clamp(34px,4.6vw,54px)", css)


if __name__ == "__main__":
    unittest.main()
