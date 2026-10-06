import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli, route  # noqa: E402


class RouteTest(unittest.TestCase):
    def s(self, text, cwd=None):
        return route.route(text, cwd).skill

    def test_url_variants(self):
        for u in ["https://www.youtube.com/watch?v=abc", "https://youtu.be/abc", "https://m.youtube.com/watch?v=abc"]:
            r = route.route(u)
            self.assertEqual((r.skill, r.needs_judgment), ("interview", True), u)
        for u in ["https://arxiv.org/abs/2210.03629", "https://arxiv.org/pdf/2210.03629v2", "https://example.com/paper.pdf"]:
            self.assertEqual(self.s(u), "paper", u)
        for u in ["https://github.com/openai/codex", "https://github.com/openai/codex/tree/main/codex-rs"]:
            self.assertEqual(self.s(u), "repo", u)

    def test_spec_markdown_path(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "docs/superpowers/specs/2026-10-05-x.md"
            p.parent.mkdir(parents=True)
            p.write_text("# x")
            self.assertEqual(self.s(str(p)), "spec")
            self.assertEqual(self.s("docs/superpowers/specs/2026-10-05-x.md", Path(d)), "spec")

    def test_local_pdf_is_paper(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "논문.pdf"
            p.write_bytes(b"%PDF-1.4")
            self.assertEqual(self.s(str(p)), "paper")

    def test_dream_phrases(self):
        for t in ["오늘 정리", "오늘 정리해줘", "하루 정리"]:
            self.assertEqual(self.s(t), "dream", t)

    def test_recall_phrases(self):
        for t in ["지난주 거 보여줘", "에이전트 관련 뭐 쌓였지", "최근에 본 것들", "recall codex"]:
            r = route.route(t)
            self.assertEqual((r.skill, r.needs_judgment), ("recall", False), t)

    def test_recall_skill_and_snippet_pregenerate(self):
        root = Path(__file__).resolve().parents[1]
        self.assertIn("작업당 1개", (root / "skills/recall/SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("없으면 하나 만들어 둬", (root / "recipes/claude/CLAUDE.md.snippet").read_text(encoding="utf-8"))

    def test_recall_does_not_swallow_questions(self):
        self.assertEqual(route.route("최근 나온 모델 중 뭐가 제일 빠른지 알아봐").skill, "quest")
        self.assertEqual(route.route("최근에 나온 것 중 제일 빠른 걸 찾아봐").skill, "quest")
        self.assertEqual(route.route("최근에 나온 것 보여줘").skill, "recall")

    def test_today_learned_is_quest_not_dream(self):
        r = route.route("오늘 배운 거 정리")
        self.assertEqual((r.skill, r.needs_judgment), ("quest", False))

    def test_local_html_is_study_with_judgment(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "01-a.html"
            p.write_text("<p>x</p>")
            r = route.route(str(p))
            self.assertEqual((r.skill, r.needs_judgment), ("study", True))

    def test_other_local_file_is_quest_with_judgment(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("notes.txt", "README.md"):
                p = Path(d) / name
                p.write_text("x")
                r = route.route(str(p))
                self.assertEqual((r.skill, r.needs_judgment), ("quest", True), name)

    def test_question_is_quest(self):
        r = route.route("Codex CLI 공부하고 싶어")
        self.assertEqual((r.skill, r.needs_judgment), ("quest", False))

    def test_other_url_is_quest_with_judgment(self):
        r = route.route("https://blog.example.com/post")
        self.assertEqual((r.skill, r.needs_judgment), ("quest", True))

    def test_cli_prints_json(self):
        self.assertEqual(cli.main(["route", "https://youtu.be/abc"]), 0)

    def test_long_question_is_quest(self):
        self.assertEqual(route.route("왜 " * 200).skill, "quest")
        self.assertEqual(route.route("a" * 300).skill, "quest")


if __name__ == "__main__":
    unittest.main()
