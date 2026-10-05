import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import paths, recall  # noqa: E402


def page(title, desc, created="2026-10-05T10:00:00+09:00"):
    return (f'<!doctype html><html><head><meta name="description" content="{desc}">'
            f'<meta name="rooms:created" content="{created}"><meta name="rooms:machine" content="m">'
            f"<title>{title}</title></head><body></body></html>")


class RecallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        os.environ["ASTACK_HOME"] = str(self.root / "home")
        self.proj = self.root / "work/alto-rooms"
        (self.proj / ".git").mkdir(parents=True)
        d = self.proj / "docs/astack/change"
        d.mkdir(parents=True)
        self.a = d / "2026-10-05-task-4-meta.html"
        self.a.write_text(page("Task 4 메타 읽기", "Rooms가 메타를 앞 64KB에서만 읽는 이유"), encoding="utf-8")
        self.b = d / "2026-10-04-task-3-scan.html"
        self.b.write_text(page("Task 3 스캔", "심볼릭 링크와 무시 규칙", "2026-10-04T09:00:00+09:00"), encoding="utf-8")
        other = self.root / "work/other/docs/astack/spec"
        other.mkdir(parents=True)
        self.c = other / "2026-10-05-x.html"
        self.c.write_text(page("다른 프로젝트 메타", "메타 이야기"), encoding="utf-8")

    def tearDown(self):
        os.environ.pop("ASTACK_HOME", None)
        self.tmp.cleanup()

    def _log(self, *rows):
        paths.outputs_log().parent.mkdir(parents=True, exist_ok=True)
        paths.outputs_log().write_text("".join(f"{ts}\t{s}\t{p}\n" for ts, s, p in rows), encoding="utf-8")

    def test_query_ranks_by_title_and_description(self):
        self._log(("2026-10-04T09:00:00+09:00", "change", self.b), ("2026-10-05T10:00:00+09:00", "change", self.a),
                  ("2026-10-05T11:00:00+09:00", "spec", self.c))
        got = recall.recall(query="메타 64KB")
        self.assertEqual(got[0].path, self.a.resolve())
        self.assertNotIn(self.b.resolve(), [i.path for i in got])

    def test_project_filter_and_now_picks_one_from_same_project(self):
        self._log(("2026-10-05T10:00:00+09:00", "change", self.a), ("2026-10-05T11:00:00+09:00", "spec", self.c))
        got = recall.recall(project=recall.project_root(self.proj / "docs"), limit=1)
        self.assertEqual([i.path for i in got], [self.a.resolve()])

    def test_since_filter(self):
        self._log(("2026-10-04T09:00:00+09:00", "change", self.b), ("2026-10-05T10:00:00+09:00", "change", self.a))
        self.assertEqual([i.path for i in recall.recall(since="2026-10-05")], [self.a.resolve()])

    def test_recall_rebuilds_from_roots_when_log_missing(self):
        paths.roots_file().parent.mkdir(parents=True, exist_ok=True)
        paths.roots_file().write_text(str(self.root / "work") + "\n", encoding="utf-8")
        found = {i.path for i in recall.recall(limit=10)}
        self.assertEqual(found, {self.a.resolve(), self.b.resolve(), self.c.resolve()})

    def test_rescan_finds_docs_astack_inside_a_repo_named_astack(self):
        d = self.root / "work/astack/docs/astack/spec"
        d.mkdir(parents=True)
        f = d / "2026-10-05-astack-v1.html"
        f.write_text(page("astack 스펙", "이해물 스펙"), encoding="utf-8")
        paths.roots_file().parent.mkdir(parents=True, exist_ok=True)
        paths.roots_file().write_text(str(self.root / "work") + "\n", encoding="utf-8")
        got = {i.path: i.skill for i in recall.recall(limit=20)}
        self.assertEqual(got[f.resolve()], "spec")

    def test_recall_skips_broken_log_lines_and_missing_files(self):
        paths.outputs_log().parent.mkdir(parents=True, exist_ok=True)
        paths.outputs_log().write_text(f"garbage\n2026-10-05T10:00:00+09:00\tchange\t{self.a}\n"
                                       f"2026-10-05T10:00:00+09:00\tchange\t{self.root}/gone.html\n", encoding="utf-8")
        self.assertEqual([i.path for i in recall.recall()], [self.a.resolve()])


if __name__ == "__main__":
    unittest.main()
