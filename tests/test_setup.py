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

    def _broken(self, content):
        md = self.home / ".claude/CLAUDE.md"
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(content)
        out = setup.install(["claude"], self.env)
        self.assertEqual(md.read_text(), content)
        self.assertTrue(any("표식이 깨짐" in l for l in out), out)
        out = setup.uninstall(["claude"], self.env)
        self.assertEqual(md.read_text(), content)
        self.assertTrue(any("표식이 깨짐" in l for l in out), out)

    def test_broken_markers_untouched(self):
        self._broken(f"a\n{BEGIN}\nuser text\n")
    def test_broken_end_only(self):
        self._broken(f"a\nuser\n{END}\nb\n")
    def test_broken_end_before_begin(self):
        self._broken(f"a\n{END}\nuser\n{BEGIN}\nb\n")
    def test_broken_two_blocks(self):
        self._broken(f"{BEGIN}\nx\n{END}\nmid\n{BEGIN}\ny\n{END}\n")

    def test_no_trailing_newline_roundtrip(self):
        md = self.home / ".claude/CLAUDE.md"
        md.parent.mkdir(parents=True)
        md.write_text("# mine")
        setup.install(["claude"], self.env)
        setup.install(["claude"], self.env)
        self.assertEqual(md.read_text().count(BEGIN), 1)
        setup.uninstall(["claude"], self.env)
        self.assertEqual(md.read_text(), "# mine")

    def test_user_text_after_block_preserved(self):
        md = self.home / ".claude/CLAUDE.md"
        md.parent.mkdir(parents=True)
        md.write_text("top\n")
        setup.install(["claude"], self.env)
        md.write_text(md.read_text() + "\n\nafter  \n")
        setup.install(["claude"], self.env)
        self.assertTrue(md.read_text().endswith(END + "\n\n\nafter  \n"))
        setup.uninstall(["claude"], self.env)
        self.assertEqual(md.read_text(), "top\n\n\nafter  \n")

    def test_symlinked_file_followed(self):
        real = self.home / "dotfiles/CLAUDE.md"
        real.parent.mkdir()
        real.write_text("x\n")
        md = self.home / ".claude/CLAUDE.md"
        md.parent.mkdir()
        md.symlink_to(real)
        setup.install(["claude"], self.env)
        self.assertTrue(md.is_symlink())
        self.assertIn(BEGIN, real.read_text())

    def test_bogus_host_changes_nothing(self):
        with self.assertRaises(ValueError):
            setup.install(["codex", "bogus"], self.env)
        self.assertEqual(list((self.home / ".codex/skills").glob("astack-*")), [])
        with self.assertRaises(ValueError):
            setup.uninstall(["codex", "bogus"], self.env)
        import subprocess
        r = subprocess.run([str(ROOT / "setup"), "--host", "codex", "bogus"], capture_output=True, text=True,
                           env={**os.environ, "ASTACK_SETUP_HOME": str(self.home)})
        self.assertEqual(r.returncode, 2)
        self.assertEqual(list((self.home / ".codex/skills").glob("astack-*")), [])

    def test_auto_expands_in_list(self):
        out = setup.install(["auto", "cli"], self.env, dry_run=True)
        self.assertTrue(any("astack-spec" in l for l in out))
        self.assertEqual(sum(1 for l in out if ".local/bin/astack" in l), 1)

    def test_aside_recopy_failure_keeps_old(self):
        import shutil
        from unittest import mock
        setup.install(["aside"], self.env)
        d = self.home / ".aside/u/0/skills/user/astack-spec"
        with mock.patch.object(shutil, "copytree", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                setup.install(["aside"], self.env)
        self.assertTrue((d / ".astack-managed").is_file())
        self.assertTrue((d / "SKILL.md").is_file())
        self.assertFalse((d.parent / ".astack-spec.tmp-astack").exists())

    def test_setup_script_runs(self):
        import subprocess
        r = subprocess.run([str(ROOT / "setup"), "--host", "codex", "--dry-run"], capture_output=True, text=True,
                           env={**os.environ, "ASTACK_SETUP_HOME": str(self.home)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("astack-spec", r.stdout)


if __name__ == "__main__":
    unittest.main()
