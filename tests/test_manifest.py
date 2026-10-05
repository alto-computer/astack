import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ManifestTest(unittest.TestCase):
    def test_plugin_json(self):
        p = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(p["name"], "astack")
        self.assertIn("version", p)

    def test_marketplace_points_to_repo_root(self):
        m = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(m["name"], "astack-dev")
        self.assertEqual(m["plugins"][0]["name"], "astack")
        self.assertEqual(m["plugins"][0]["source"], "./")

    def test_every_skill_has_use_when_description(self):
        for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
            text = skill.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), skill)
            front = text.split("---", 2)[1]
            desc = next(l for l in front.splitlines() if l.startswith("description:"))
            body = desc.split(":", 1)[1].strip().strip('"')
            self.assertTrue(body.startswith("Use when"), f"{skill}: {body[:40]}")
            self.assertLessEqual(len(body), 500, skill)


if __name__ == "__main__":
    unittest.main()
