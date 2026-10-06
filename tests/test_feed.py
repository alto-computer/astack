import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli, feed, memory, paths  # noqa: E402

PLAYLIST = {"entries": [
    {"id": "AAAAAAAAAAA", "title": "new", "duration": 3600, "upload_date": "20261004"},
    {"id": "BBBBBBBBBBB", "title": "seen", "duration": 1200, "upload_date": "20261003"},
    {"id": "CCCCCCCCCCC", "title": "old", "duration": 600, "upload_date": "20260901"},
]}


class R:
    def __init__(self, out, code=0):
        self.stdout, self.returncode, self.stderr = out, code, ""


class FeedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get("ASTACK_HOME")
        os.environ["ASTACK_HOME"] = self.tmp.name

    def tearDown(self):
        if self.old is None:
            os.environ.pop("ASTACK_HOME", None)
        else:
            os.environ["ASTACK_HOME"] = self.old
        self.tmp.cleanup()

    def test_seed_is_idempotent_and_whitelist_reads_url(self):
        self.assertTrue(feed.seed("Example Pod", "https://www.youtube.com/@ExamplePod"))
        self.assertFalse(feed.seed("Example Pod", "https://www.youtube.com/@ExamplePod"))
        self.assertEqual(feed.whitelist(), [{"name": "Example Pod", "url": "https://www.youtube.com/@ExamplePod"}])

    def test_exclude_removes_channel(self):
        feed.seed("X", "https://www.youtube.com/@x")
        memory.add('{"type":"exclude","key":"channel:X","insight":"feed에서 제외","source":"told"}')
        self.assertEqual(feed.whitelist(), [])

    def test_seed_after_exclude_adds_channel_back(self):
        feed.seed("X", "https://www.youtube.com/@x")
        memory.add('{"type":"exclude","key":"channel:X","insight":"feed에서 제외","source":"told"}')
        self.assertTrue(feed.seed("X", "https://www.youtube.com/@x"))
        self.assertEqual(feed.whitelist(), [{"name": "X", "url": "https://www.youtube.com/@x"}])
        memory.add('{"type":"exclude","key":"channel:X","insight":"다시 제외","source":"told"}')
        self.assertEqual(feed.whitelist(), [])

    def test_newer_date_wins_over_line_order(self):
        lines = [
            {"type": "exclude", "key": "channel:Y", "insight": "제외", "source": "told", "date": "2026-10-03"},
            {"type": "whitelist", "key": "feed:youtube:Y", "insight": "https://www.youtube.com/@y", "source": "told", "date": "2026-10-01"},
            {"type": "whitelist", "key": "feed:youtube:Z", "insight": "https://www.youtube.com/@z", "source": "told", "date": "2026-10-04"},
            {"type": "exclude", "key": "channel:Z", "insight": "제외", "source": "told", "date": "2026-10-02"},
        ]
        paths.memory_file().write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lines), encoding="utf-8")
        self.assertEqual([w["name"] for w in feed.whitelist()], ["Z"])

    def test_cli_since_must_be_a_date(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(cli.main(["feed", "candidates", "--since", "어제"]), 2)
        self.assertIn("YYYY-MM-DD", err.getvalue())

    def test_skill_documents_readd_and_magazine_folder(self):
        skill = (Path(__file__).resolve().parents[1] / "skills/feed/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("다시 넣기", skill)
        self.assertIn("~/.astack/journal/feed/<날짜>/", skill)
        self.assertIn('skill == "feed"', skill)
        self.assertIn("--lang", skill)
        interview = (Path(__file__).resolve().parents[1] / "skills/interview/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("호출한 스킬이 폴더를 주면", interview)
        seminar = (Path(__file__).resolve().parents[1] / "skills/seminar/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("호출한 스킬이 폴더를 주면", seminar)

    def test_seen_ids_from_short_links(self):
        doc = Path(self.tmp.name) / "a.html"
        doc.write_text('<a href="https://youtu.be/BBBBBBBBBBB?t=3">원본</a>', encoding="utf-8")
        paths.outputs_log().write_text(f"2026-10-04T10:00:00+09:00\tinterview\t{doc}\n", encoding="utf-8")
        self.assertEqual(feed.seen_ids(), {"BBBBBBBBBBB"})

    def test_candidates_skip_seen_and_old(self):
        feed.seed("C", "https://www.youtube.com/@c")
        doc = Path(self.tmp.name) / "a.html"
        doc.write_text("https://www.youtube.com/watch?v=BBBBBBBBBBB", encoding="utf-8")
        paths.outputs_log().write_text(f"2026-10-04T10:00:00+09:00\tinterview\t{doc}\n", encoding="utf-8")
        calls = []

        def runner(cmd, **kw):
            calls.append(cmd)
            return R(json.dumps(PLAYLIST))

        got = feed.candidates(since="2026-10-01", runner=runner)
        self.assertEqual([c["id"] for c in got], ["AAAAAAAAAAA"])
        self.assertEqual(got[0]["channel"], "C")
        self.assertTrue(calls[0][-1].endswith("/@c/videos"))

    def _flat(self, entries):
        return json.dumps({"entries": [{"id": i, "title": i, "duration": 60, "upload_date": None, "timestamp": ts}
                                       for i, ts in entries]})

    def test_undated_entries_get_dates_from_one_fallback_call(self):
        feed.seed("C", "https://www.youtube.com/@c")
        doc = Path(self.tmp.name) / "a.html"
        doc.write_text("https://www.youtube.com/watch?v=SSSSSSSSSSS", encoding="utf-8")
        paths.outputs_log().write_text(f"2026-10-04T10:00:00+09:00\tinterview\t{doc}\n", encoding="utf-8")
        calls = []

        def runner(cmd, **kw):
            calls.append(cmd)
            if "--print" in cmd:
                return R("NEWNEWNEWNE 20261004\nOLDOLDOLDOL 20260901\n")
            return R(self._flat([("NEWNEWNEWNE", None), ("SSSSSSSSSSS", None), ("OLDOLDOLDOL", None)]))

        got = feed.candidates(since="2026-10-01", runner=runner)
        self.assertEqual([c["id"] for c in got], ["NEWNEWNEWNE"])
        fb = [c for c in calls if "--print" in c]
        self.assertEqual(len(fb), 1)
        self.assertEqual(fb[0][-2:], ["https://www.youtube.com/watch?v=NEWNEWNEWNE",
                                      "https://www.youtube.com/watch?v=OLDOLDOLDOL"])

    def test_timestamp_is_used_without_fallback(self):
        feed.seed("C", "https://www.youtube.com/@c")
        calls = []

        def runner(cmd, **kw):
            calls.append(cmd)
            return R(self._flat([("OLDOLDOLDOL", 1788000000), ("NEWNEWNEWNE", 1791000000)]))

        got = feed.candidates(since="2026-10-01", runner=runner)
        self.assertEqual([(c["id"], c["upload_date"]) for c in got], [("NEWNEWNEWNE", "20261003")])
        self.assertFalse(any("--print" in c for c in calls))

    def test_fallback_failure_keeps_undated_last_with_warnings(self):
        feed.seed("C", "https://www.youtube.com/@c")

        def runner(cmd, **kw):
            if "--print" in cmd:
                return R("", 1)
            return R(json.dumps({"entries": [
                {"id": "UNDATEDUNDA", "upload_date": None, "timestamp": None},
                {"id": "DATEDDATEDD", "upload_date": "20260920"}]}))

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            got = feed.candidates(since="2026-10-01", runner=runner)
        self.assertEqual([c["id"] for c in got], ["UNDATEDUNDA"])
        self.assertIn("날짜를 못 읽음 C:", stderr.getvalue())
        self.assertIn("날짜 없는 후보 1개 — since로 거르지 못함", stderr.getvalue())
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            got = feed.candidates(runner=runner)
        self.assertEqual([c["id"] for c in got], ["DATEDDATEDD", "UNDATEDUNDA"])

    def test_partial_print_output_is_used_despite_exit_1(self):
        feed.seed("C", "https://www.youtube.com/@c")

        def runner(cmd, **kw):
            if "--print" in cmd:
                self.assertIn("--ignore-errors", cmd)
                return R("NEWNEWNEWNE 20261004\nNA\nPRIVATEPRIV NA\nbad line extra 20261004\n", 1)
            return R(self._flat([("NEWNEWNEWNE", None), ("PRIVATEPRIV", None)]))

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            got = feed.candidates(since="2026-10-01", runner=runner)
        self.assertEqual([(c["id"], c["upload_date"]) for c in got], [("NEWNEWNEWNE", "20261004"), ("PRIVATEPRIV", "")])
        self.assertNotIn("못 읽음", stderr.getvalue())
        self.assertIn("날짜 없는 후보 1개", stderr.getvalue())

    def test_no_since_makes_no_fallback_call_and_no_warning(self):
        feed.seed("C", "https://www.youtube.com/@c")
        calls = []

        def runner(cmd, **kw):
            calls.append(cmd)
            return R(self._flat([("AAAAAAAAAAA", None)]))

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            got = feed.candidates(runner=runner)
        self.assertEqual([c["id"] for c in got], ["AAAAAAAAAAA"])
        self.assertFalse(any("--print" in c for c in calls))
        self.assertEqual(stderr.getvalue(), "")

    def test_nonpositive_timestamp_is_undated(self):
        self.assertEqual(feed._entry_date({"timestamp": 0}), "")
        self.assertEqual(feed._entry_date({"timestamp": -5}), "")

    def test_same_video_in_two_channels_appears_once(self):
        feed.seed("A", "https://www.youtube.com/@a")
        feed.seed("B", "https://www.youtube.com/@b")
        runner = lambda cmd, **kw: R(json.dumps({"entries": [{"id": "AAAAAAAAAAA", "upload_date": "20261004"}]}))
        got = feed.candidates(runner=runner)
        self.assertEqual([(c["id"], c["channel"]) for c in got], [("AAAAAAAAAAA", "A")])

    def test_dated_entries_sort_newest_first(self):
        feed.seed("C", "https://www.youtube.com/@c")
        runner = lambda cmd, **kw: R(json.dumps({"entries": [
            {"id": "OLDOLDOLDOL", "upload_date": "20261001"}, {"id": "NEWNEWNEWNE", "upload_date": "20261005"}]}))
        self.assertEqual([c["id"] for c in feed.candidates(runner=runner)], ["NEWNEWNEWNE", "OLDOLDOLDOL"])

    def test_channel_failure_skips_that_channel(self):
        feed.seed("Bad", "https://www.youtube.com/@bad")
        self.assertEqual(feed.candidates(runner=lambda cmd, **kw: R("", 1)), [])

    def test_cli(self):
        self.assertEqual(cli.main(["feed", "seed", "Y", "https://www.youtube.com/@y"]), 0)
        self.assertEqual(cli.main(["feed", "seed", "Z", "not-a-url"]), 2)

    def test_seed_rejects_video_url(self):
        with self.assertRaises(ValueError):
            feed.seed("Bad", "https://www.youtube.com/watch?v=AAAAAAAAAAA")

    def test_candidates_prints_skip_message_to_stderr(self):
        feed.seed("Bad", "https://www.youtube.com/@bad")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = feed.candidates(runner=lambda cmd, **kw: R("", 1))
        self.assertEqual(result, [])
        self.assertIn("건너뜀 Bad", stderr.getvalue())

    def test_latest_guards_json_loads(self):
        calls = []

        def runner(cmd, **kw):
            calls.append(cmd)
            return R("invalid json")

        with self.assertRaises(feed.MediaError) as ctx:
            feed.latest("https://www.youtube.com/@test", runner=runner)
        self.assertIn("채널 목록을 읽지 못했습니다", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
