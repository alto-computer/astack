import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from astack_cli import check, inline  # noqa: E402

TEMPLATES = sorted(ROOT.glob("skills/*/assets/*template*.html"))


class TemplateTest(unittest.TestCase):
    def test_templates_exist(self):
        names = {p.parent.parent.name for p in TEMPLATES}
        self.assertTrue({"spec"} <= names, names)

    def test_inlined_template_passes_contract(self):
        for t in TEMPLATES:
            with self.subTest(t=t.relative_to(ROOT)):
                html = inline.inline_html(t.read_text(encoding="utf-8"), t.parent)
                errors = [f"{i.code}: {i.message}" for i in check.check_html(html) if i.level == "error"]
                self.assertEqual(errors, [])

    def test_flow_scenes_have_design_reason(self):
        t = ROOT / "skills/spec/assets/template.html"
        html = t.read_text(encoding="utf-8")
        for sec in ("a2", "a3"):
            for scene in re.findall(rf'<section class="scene[^"]*"[^>]*data-sec="{sec}".*?</section>', html, re.S):
                self.assertIn('class="why"', scene, scene[:80])

    def test_every_scene_has_a_visual_slot(self):
        for t in TEMPLATES:
            html = t.read_text(encoding="utf-8")
            scenes = set(re.findall(r'class="scene[^"]*"[^>]*data-i="(\d+)"', html))
            slots = set(re.findall(r'class="vis" data-v="(\d+)"', html))
            self.assertEqual(scenes, slots, t.name)


if __name__ == "__main__":
    unittest.main()
