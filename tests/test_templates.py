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
        self.assertTrue({"spec", "change", "recall"} <= names, names)

    def test_raw_template_fails_with_meta_placeholders(self):
        for t in TEMPLATES:
            with self.subTest(t=t.relative_to(ROOT)):
                html = inline.inline_html(t.read_text(encoding="utf-8"), t.parent)
                self.assertIn("meta", [i.code for i in check.check_html(html) if i.level == "error"])

    def test_inlined_template_passes_contract(self):
        real = {"description": "채운 설명", "rooms:created": "2026-10-05T10:00:00+09:00", "rooms:machine": "test-host"}
        for t in TEMPLATES:
            with self.subTest(t=t.relative_to(ROOT)):
                html = inline.inline_html(t.read_text(encoding="utf-8"), t.parent)
                for name, val in real.items():
                    html, n = re.subn(rf'(<meta name="{name}" content=")[^"]*', rf"\g<1>{val}", html)
                    self.assertEqual(n, 1, name)
                errors = [f"{i.code}: {i.message}" for i in check.check_html(html) if i.level == "error" and i.code != "placeholder"]
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
