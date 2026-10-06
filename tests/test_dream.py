import datetime
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli, dream  # noqa: E402
from astack_cli.recall import Item  # noqa: E402

D = datetime.date(2026, 10, 4)  # 일요일


def item(day: str, skill="spec", hour="10"):
    return Item(Path(f"/x/{skill}-{day}-{hour}.html"), skill, f"{day}T{hour}:00:00+09:00", f"t {day}", f"d {day}", 0)


class DreamTest(unittest.TestCase):
    def test_today_and_spaced(self):
        items = [item("2026-10-04"), item("2026-10-04", "change", "15"), item("2026-10-03"), item("2026-09-27"), item("2026-09-04")]
        got = dream.collect(D, items=items)
        self.assertEqual(len(got["today"]), 2)
        self.assertEqual([s["days_ago"] for s in got["spaced"]], [1, 7, 30])

    def test_spaced_picks_latest_of_that_day(self):
        got = dream.collect(D, items=[item("2026-10-03", hour="09"), item("2026-10-03", "change", "18")])
        self.assertEqual(got["spaced"][0]["skill"], "change")

    def test_spaced_review_skips_missing_days(self):
        got = dream.collect(D, items=[item("2026-09-27")])
        self.assertEqual([s["days_ago"] for s in got["spaced"]], [7])

    def test_weekly_on_sunday_only(self):
        items = [item("2026-09-28"), item("2026-10-04"), item("2026-09-27")]
        self.assertEqual(len(dream.collect(D, items=items)["week"]), 2)
        self.assertFalse(dream.collect(datetime.date(2026, 10, 5), items=items)["weekly"])

    def test_own_outputs_are_excluded(self):
        got = dream.collect(D, items=[item("2026-10-04", "dream"), item("2026-10-04", "feed")])
        self.assertEqual(got["today"], [])

    def test_cli(self):
        self.assertEqual(cli.main(["dream", "collect", "--date", "2026-10-04"]), 0)
        self.assertEqual(cli.main(["dream", "collect", "--date", "어제"]), 2)


class JournalPathTest(unittest.TestCase):
    def setUp(self):
        import os, tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.old = {k: os.environ.get(k) for k in ("ASTACK_ROOMS_HOME", "ASTACK_HOME")}
        os.environ["ASTACK_HOME"] = self.tmp.name + "/a"

    def tearDown(self):
        import os
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def test_rooms_journal_when_home_exists(self):
        import os
        home = Path(self.tmp.name) / "rooms"
        (home / ".rooms").mkdir(parents=True)
        os.environ["ASTACK_ROOMS_HOME"] = str(home)
        self.assertEqual(dream.journal_path(D), home / "journal/2026-10-04/dream.html")
        self.assertEqual(dream.journal_path(D, "feed"), home / "journal/2026-10-04/feed.html")

    def test_astack_journal_without_rooms(self):
        import os
        os.environ["ASTACK_ROOMS_HOME"] = str(Path(self.tmp.name) / "none")
        self.assertEqual(dream.journal_path(D).name, "2026-10-04.html")
        self.assertEqual(dream.journal_path(D, "feed").name, "2026-10-04-feed.html")

    def test_cli_path_rejects_bad_name(self):
        self.assertEqual(cli.main(["dream", "path", "--date", "2026-10-04", "--name", "../x"]), 2)


if __name__ == "__main__":
    unittest.main()
