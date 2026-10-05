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
        self.assertTrue(feed.seed("Latent Space", "https://www.youtube.com/@LatentSpacePod"))
        self.assertFalse(feed.seed("Latent Space", "https://www.youtube.com/@LatentSpacePod"))
        self.assertEqual(feed.whitelist(), [{"name": "Latent Space", "url": "https://www.youtube.com/@LatentSpacePod"}])

    def test_exclude_removes_channel(self):
        feed.seed("X", "https://www.youtube.com/@x")
        memory.add('{"type":"exclude","key":"channel:X","insight":"feed에서 제외","source":"told"}')
        self.assertEqual(feed.whitelist(), [])

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

    def test_channel_failure_skips_that_channel(self):
        feed.seed("Bad", "https://www.youtube.com/@bad")
        self.assertEqual(feed.candidates(runner=lambda cmd, **kw: R("", 1)), [])

    def test_cli(self):
        self.assertEqual(cli.main(["feed", "seed", "Y", "https://www.youtube.com/@y"]), 0)
        self.assertEqual(cli.main(["feed", "seed", "Z", "not-a-url"]), 2)


if __name__ == "__main__":
    unittest.main()
