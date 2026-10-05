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
