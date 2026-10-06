import unittest
import os


class TestRecipes(unittest.TestCase):
    """Test recipe files for Task 2: Host recipes (Codex, Hermes, Aside)"""

    def setUp(self):
        """Set up test paths"""
        self.recipe_dir = os.path.join(
            os.path.dirname(__file__), "..", "recipes"
        )

    def test_codex_agents_snippet_exists(self):
        """Test that recipes/codex/AGENTS.md.snippet exists"""
        path = os.path.join(self.recipe_dir, "codex", "AGENTS.md.snippet")
        self.assertTrue(os.path.exists(path), f"File not found: {path}")

    def test_hermes_readme_exists(self):
        """Test that recipes/hermes/README.md exists"""
        path = os.path.join(self.recipe_dir, "hermes", "README.md")
        self.assertTrue(os.path.exists(path), f"File not found: {path}")

    def test_hermes_cron_yaml_exists(self):
        """Test that recipes/hermes/cron.yaml exists"""
        path = os.path.join(self.recipe_dir, "hermes", "cron.yaml")
        self.assertTrue(os.path.exists(path), f"File not found: {path}")

    def test_hermes_telegram_topics_yaml_exists(self):
        """Test that recipes/hermes/telegram-topics.yaml exists"""
        path = os.path.join(self.recipe_dir, "hermes", "telegram-topics.yaml")
        self.assertTrue(os.path.exists(path), f"File not found: {path}")

    def test_aside_permissions_exists(self):
        """Test that recipes/aside/permissions.md exists"""
        path = os.path.join(self.recipe_dir, "aside", "permissions.md")
        self.assertTrue(os.path.exists(path), f"File not found: {path}")

    def test_agents_snippet_contains_astack_spec(self):
        """Test that AGENTS.md.snippet contains astack-spec"""
        path = os.path.join(self.recipe_dir, "codex", "AGENTS.md.snippet")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(
            "astack-spec",
            content,
            "AGENTS.md.snippet should contain 'astack-spec'",
        )

    def test_agents_snippet_names_skills_by_frontmatter_name(self):
        """Codex는 폴더 이름(astack-spec)이 아니라 SKILL.md의 name(spec)으로 스킬을 부른다."""
        import re
        with open(os.path.join(self.recipe_dir, "codex", "AGENTS.md.snippet"), encoding="utf-8") as f:
            content = f.read()
        skills = os.path.join(self.recipe_dir, "..", "skills")
        for folder in re.findall(r"~/\.codex/skills/astack-([a-z]+)", content):
            with open(os.path.join(skills, folder, "SKILL.md"), encoding="utf-8") as f:
                name = re.search(r"^name:\s*(\S+)", f.read(), re.M).group(1)
            self.assertIn(f"`{name}` 스킬(~/.codex/skills/astack-{folder})", content)
        self.assertNotIn("astack-spec 스킬", content)
        self.assertNotIn("스킬 이름은 `astack-", content)

    def test_agents_snippet_contains_astack_recall_now(self):
        """Test that AGENTS.md.snippet contains astack recall --now"""
        path = os.path.join(self.recipe_dir, "codex", "AGENTS.md.snippet")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(
            "astack recall --now",
            content,
            "AGENTS.md.snippet should contain 'astack recall --now'",
        )

    def test_cron_yaml_has_astack_feed_job(self):
        """Test that cron.yaml has astack-feed job with schedule 0 5"""
        path = os.path.join(self.recipe_dir, "hermes", "cron.yaml")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("astack-feed", content, "Missing astack-feed job")
        self.assertIn(
            '0 5 * * *',
            content,
            "Missing schedule '0 5 * * *' for astack-feed",
        )

    def test_cron_yaml_has_astack_morning_job(self):
        """Test that cron.yaml has astack-morning job with schedule 0 7"""
        path = os.path.join(self.recipe_dir, "hermes", "cron.yaml")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("astack-morning", content, "Missing astack-morning job")
        self.assertIn(
            '0 7 * * *',
            content,
            "Missing schedule '0 7 * * *' for astack-morning",
        )

    def test_cron_yaml_has_astack_dream_job(self):
        """Test that cron.yaml has astack-dream job with schedule 0 20"""
        path = os.path.join(self.recipe_dir, "hermes", "cron.yaml")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("astack-dream", content, "Missing astack-dream job")
        self.assertIn(
            '0 20 * * *',
            content,
            "Missing schedule '0 20 * * *' for astack-dream",
        )

    def test_cron_yaml_has_astack_consolidate_job(self):
        """Test that cron.yaml has astack-consolidate job with schedule 30 20"""
        path = os.path.join(self.recipe_dir, "hermes", "cron.yaml")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(
            "astack-consolidate", content, "Missing astack-consolidate job"
        )
        self.assertIn(
            '30 20 * * *',
            content,
            "Missing schedule '30 20 * * *' for astack-consolidate",
        )

    def test_cron_yaml_has_astack_ask_tonight_job(self):
        """Test that cron.yaml has astack-ask-tonight job with schedule 0 21"""
        path = os.path.join(self.recipe_dir, "hermes", "cron.yaml")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(
            "astack-ask-tonight", content, "Missing astack-ask-tonight job"
        )
        self.assertIn(
            '0 21 * * *',
            content,
            "Missing schedule '0 21 * * *' for astack-ask-tonight",
        )

    def test_cron_yaml_has_astack_night_job(self):
        """Test that cron.yaml has astack-night job with schedule 0 1"""
        path = os.path.join(self.recipe_dir, "hermes", "cron.yaml")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("astack-night", content, "Missing astack-night job")
        self.assertIn(
            '0 1 * * *',
            content,
            "Missing schedule '0 1 * * *' for astack-night",
        )

    def test_cron_night_has_deadline_and_morning_reports_unreported(self):
        with open(os.path.join(self.recipe_dir, "hermes", "cron.yaml"), encoding="utf-8") as f:
            content = f.read()
        self.assertIn("astack goal run --max 3 --host claude --until 06:30", content)
        self.assertIn("astack goal report --new --text", content)
        self.assertNotIn("--date today", content)

    def test_hermes_undo_uses_real_setup_flags(self):
        with open(os.path.join(self.recipe_dir, "hermes", "README.md"), encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("--reset", content)
        self.assertIn("./setup --uninstall --host cli claude", content)

    def test_spec_reference_reachable_from_copies(self):
        """Aside 복사본에서는 ../../ 상대 경로가 깨진다. 설치된 astack 링크로 레포를 찾는 길을 함께 적는다."""
        root = os.path.join(self.recipe_dir, "..")
        with open(os.path.join(root, "skills", "spec", "SKILL.md"), encoding="utf-8") as f:
            content = f.read()
        ref = "docs/superpowers/specs/references/spec-reference-rooms-v1.html"
        self.assertIn(f'"$(dirname "$(readlink ~/.local/bin/astack)")/../{ref}"', content)
        self.assertTrue(os.path.isfile(os.path.join(root, "bin", "..", ref)))

    def test_hermes_files_start_with_validation_note(self):
        """Test that Hermes files start with 검증 전 comment"""
        hermes_files = [
            os.path.join(self.recipe_dir, "hermes", "cron.yaml"),
            os.path.join(self.recipe_dir, "hermes", "telegram-topics.yaml"),
            os.path.join(self.recipe_dir, "hermes", "README.md"),
        ]

        for path in hermes_files:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(
                "검증 전",
                content,
                f"File {path} should contain '검증 전'",
            )


if __name__ == "__main__":
    unittest.main()
