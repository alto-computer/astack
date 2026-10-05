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
        self.assertTrue({"spec", "change", "recall", "interview", "seminar", "paper", "repo", "quest", "map", "dream", "feed"} <= names, names)

    def test_feed_template_has_order_and_cards(self):
        html = (ROOT / "skills/feed/assets/template.html").read_text(encoding="utf-8")
        for s in ('id="deep"', 'id="cards"', 'class="card"', "읽는 순서"):
            self.assertIn(s, html)

    def test_atom_skills_respond_only_on_request(self):
        for name in ("interview", "seminar", "paper", "repo"):
            p = ROOT / f"skills/{name}/SKILL.md"
            if not p.exists():
                continue
            front = p.read_text(encoding="utf-8").split("---", 2)[1]
            self.assertIn("요청할 때", front, name)

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

    def test_every_template_signs_the_source_line(self):
        for t in TEMPLATES:
            with self.subTest(t=t.relative_to(ROOT)):
                self.assertIn("Claude Code가 썼습니다", t.read_text(encoding="utf-8"))

    def test_seminar_stage_reads_scene_img_src(self):
        html = (ROOT / "skills/seminar/assets/template.html").read_text(encoding="utf-8")
        self.assertIn("s.querySelector('.scene-fig img').src", html)
        self.assertNotIn("data-img", html)

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

    def test_paper_template_has_postit_and_figure_slots(self):
        html = (ROOT / "skills/paper/assets/template.html").read_text(encoding="utf-8")
        self.assertIn('<details class="postit">', html)
        self.assertIn('class="vis" data-v="1"', html)

    def test_body_placeholders_are_braces(self):
        for name in ("paper/assets/template.html", "repo/assets/template.html", "quest/assets/chapter-template.html",
                     "quest/assets/map-template.html", "map/assets/template.html"):
            html = (ROOT / f"skills/{name}").read_text(encoding="utf-8")
            with self.subTest(name=name):
                body = re.sub(r'<meta name="[^"]+" content="[^"]*">', "", html)
                self.assertEqual(re.findall(r"\[[^\[\]\n]{1,80}\]", body), [])
                self.assertIn("{{", body)

    def test_paper_postit_is_not_inside_p(self):
        html = (ROOT / "skills/paper/assets/template.html").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"<p>(?:(?!</p>).)*<details", html, re.S))

    def test_paper_figure_path_names_the_document(self):
        html = (ROOT / "skills/paper/assets/template.html").read_text(encoding="utf-8")
        self.assertIn("<!-- <날짜>-<slug>-figs/fig-1.png -->", html)

    def test_repo_code_slots_pick_language_from_path(self):
        html = (ROOT / "skills/repo/assets/template.html").read_text(encoding="utf-8")
        self.assertNotIn('data-lang="ts"', html)
        self.assertEqual(html.count('data-lang="auto"'), 3)

    def test_repo_template_has_evidence_tiers_and_weakness(self):
        html = (ROOT / "skills/repo/assets/template.html").read_text(encoding="utf-8")
        for s in ("ev ev-ok", "ev ev-mid", "ev ev-bad", 'id="r5"'):
            self.assertIn(s, html)

    def test_quest_chapter_has_quiz_and_nav(self):
        html = (ROOT / "skills/quest/assets/chapter-template.html").read_text(encoding="utf-8")
        self.assertIn('<details class="quiz" data-kind="mc">', html)
        self.assertIn('href="00-지도.html"', html)
        self.assertIn("그래서 나한테는?", html)

    def test_quest_chapter_scenes_have_mobile_figure_slot(self):
        html = (ROOT / "skills/quest/assets/chapter-template.html").read_text(encoding="utf-8")
        scenes = re.findall(r'<section class="scene.*?</section>', html, re.S)
        self.assertTrue(scenes)
        for sc in scenes:
            self.assertIn("inl vis-inl", sc)

    def test_quest_chapter_has_experiment_report_block(self):
        html = (ROOT / "skills/quest/assets/chapter-template.html").read_text(encoding="utf-8")
        block = re.search(r"<!-- 실험 보고서 장이면 tome 앞에:.*?-->", html, re.S)
        self.assertIsNotNone(block)
        self.assertLess(block.start(), html.index('<section class="tome">'))
        for s in ('<section class="report" id="report">', "방법", "차트", "원자료", "재현 명령", "한계",
                  '<img src="bench/{{차트}}.svg"', 'class="ustab"', '<pre data-lang="bash"><code>{{명령}}</code></pre>'):
            self.assertIn(s, block.group(0))
        css = (ROOT / "skills/design/assets/alto-ext.css").read_text(encoding="utf-8")
        self.assertIn(".report figure img{max-width:100%;height:auto}", css)

    def test_quest_map_has_terms_between_chapters_and_sources(self):
        html = (ROOT / "skills/quest/assets/map-template.html").read_text(encoding="utf-8")
        i = html.index('<section class="terms" id="terms">')
        self.assertLess(html.index('<section class="chapters">'), i)
        self.assertLess(i, html.index('<section class="sources">'))
        skill = (ROOT / "skills/quest/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`#terms`", skill)

    def test_quest_skill_subagent_fallback_and_topic_query(self):
        skill = (ROOT / "skills/quest/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("topic:<주제어>", skill)
        self.assertNotIn("`astack memory search topic:`", skill)
        self.assertIn("채팅이 없으면", skill)

    def test_map_template_has_converge_sections(self):
        html = (ROOT / "skills/map/assets/template.html").read_text(encoding="utf-8")
        for s in ('id="known"', 'id="agree"', 'id="conflict"', 'id="open"', 'id="decided"'):
            self.assertIn(s, html)

    def test_dream_template_sections(self):
        html = (ROOT / "skills/dream/assets/template.html").read_text(encoding="utf-8")
        for s in ('id="themes"', 'id="clash"', 'id="questions"', 'id="review"', 'id="mywords"', 'id="weekly"', 'class="quiz"'):
            self.assertIn(s, html)


if __name__ == "__main__":
    unittest.main()
