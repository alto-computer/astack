import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from astack_cli import setup  # noqa: E402

BEGIN, END = "<!-- astack:begin -->", "<!-- astack:end -->"


class SetupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        (self.home / ".codex/skills").mkdir(parents=True)
        (self.home / ".aside/u/0/skills/user").mkdir(parents=True)
        self.env = setup.Env(home=self.home, repo=ROOT)

    def tearDown(self):
        self.tmp.cleanup()

    def skills(self):
        return sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))

    def test_detect_finds_hosts(self):
        self.assertEqual(setup.detect(self.env)[:2], ["cli", "claude"])
        self.assertIn("codex", setup.detect(self.env))
        self.assertIn("aside", setup.detect(self.env))

    def test_cli_links_binary_and_roots(self):
        setup.install(["cli"], self.env)
        link = self.home / ".local/bin/astack"
        self.assertEqual(link.resolve(), (ROOT / "bin/astack").resolve())
        self.assertEqual((self.home / ".astack/roots").read_text().strip(), str(self.home / "personal"))

    def test_claude_snippet_once_and_plugin_todo(self):
        md = self.home / ".claude/CLAUDE.md"
        md.parent.mkdir(parents=True)
        md.write_text("# mine\n")
        out = setup.install(["claude"], self.env)
        out2 = setup.install(["claude"], self.env)
        text = md.read_text()
        self.assertTrue(text.startswith("# mine\n"))
        self.assertEqual(text.count(BEGIN), 1)
        self.assertTrue(any("/plugin install astack@astack-dev" in l for l in out + out2))

    def test_codex_links_every_skill(self):
        setup.install(["codex"], self.env)
        for name in self.skills():
            p = self.home / f".codex/skills/astack-{name}"
            self.assertTrue(p.is_symlink(), name)
            self.assertEqual(p.resolve(), (ROOT / "skills" / name).resolve())
        self.assertEqual((self.home / ".codex/AGENTS.md").read_text().count(BEGIN), 1)

    def test_aside_copies_with_marker(self):
        setup.install(["aside"], self.env)
        d = self.home / ".aside/u/0/skills/user/astack-spec"
        self.assertTrue(d.is_dir() and not d.is_symlink())
        self.assertTrue((d / "SKILL.md").is_file())
        self.assertTrue((d / ".astack-managed").is_file())

    def test_install_is_idempotent(self):
        setup.install(["cli", "claude", "codex", "aside"], self.env)
        setup.install(["cli", "claude", "codex", "aside"], self.env)
        self.assertEqual((self.home / ".claude/CLAUDE.md").read_text().count(BEGIN), 1)
        self.assertEqual(len(list((self.home / ".codex/skills").glob("astack-*"))), len(self.skills()))

    def test_existing_user_dir_is_not_overwritten(self):
        mine = self.home / ".codex/skills/astack-spec"
        mine.mkdir()
        (mine / "SKILL.md").write_text("mine")
        out = setup.install(["codex"], self.env)
        self.assertEqual((mine / "SKILL.md").read_text(), "mine")
        self.assertTrue(any("건너뜀" in l and "astack-spec" in l for l in out))
        aside_mine = self.home / ".aside/u/0/skills/user/astack-spec"
        aside_mine.mkdir()
        (aside_mine / "SKILL.md").write_text("mine")
        setup.install(["aside"], self.env)
        self.assertEqual((aside_mine / "SKILL.md").read_text(), "mine")

    def test_uninstall_removes_only_ours(self):
        md = self.home / ".claude/CLAUDE.md"
        md.parent.mkdir(parents=True)
        md.write_text("# mine\n")
        (self.home / ".codex/skills/other").mkdir()
        setup.install(["cli", "claude", "codex", "aside"], self.env)
        setup.uninstall(["cli", "claude", "codex", "aside"], self.env)
        self.assertEqual(md.read_text(), "# mine\n")
        self.assertTrue((self.home / ".codex/skills/other").is_dir())
        self.assertEqual(list((self.home / ".codex/skills").glob("astack-*")), [])
        self.assertEqual(list((self.home / ".aside/u/0/skills/user").glob("astack-*")), [])
        self.assertFalse((self.home / ".local/bin/astack").exists())

    def test_dry_run_changes_nothing(self):
        out = setup.install(["cli", "claude", "codex", "aside"], self.env, dry_run=True)
        self.assertTrue(out)
        self.assertFalse((self.home / ".local/bin/astack").exists())
        self.assertEqual(list((self.home / ".codex/skills").glob("astack-*")), [])

    def test_setup_script_runs(self):
        import subprocess
        r = subprocess.run([str(ROOT / "setup"), "--host", "codex", "--dry-run"], capture_output=True, text=True,
                           env={**os.environ, "ASTACK_SETUP_HOME": str(self.home)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("astack-spec", r.stdout)


if __name__ == "__main__":
    unittest.main()
