import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli, media  # noqa: E402

ROLLING = """WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:02.000
so today we talk about

00:00:02.000 --> 00:00:04.000
so today we talk about
<00:00:02.500><c>browsers</c><00:00:03.000><c> and agents</c>

00:00:04.000 --> 00:00:06.000
browsers and agents
and why they matter
"""

MANUAL = """WEBVTT

1
00:01:00.000 --> 00:01:03.000
First line of a cue
second line of the same cue
"""


class VttTest(unittest.TestCase):
    def test_rolling_auto_captions_are_deduped(self):
        lines = [t for _, t in media.parse_vtt(ROLLING)]
        self.assertEqual(lines, ["so today we talk about", "browsers and agents", "and why they matter"])

    def test_manual_multiline_cue_keeps_both_lines(self):
        got = media.parse_vtt(MANUAL)
        self.assertEqual(got, [(60.0, "First line of a cue"), (60.0, "second line of the same cue")])

    def test_fmt_ts(self):
        self.assertEqual(media.fmt_ts(3723.4), "01:02:03")


class FakeYtDlp(unittest.TestCase):
    """PATH 앞에 가짜 yt-dlp를 둔다. -o 경로에 info.json과 vtt를 쓴다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = Path(self.tmp.name) / "bin"
        self.bin.mkdir()
        self.old = os.environ["PATH"]
        os.environ["PATH"] = f"{self.bin}{os.pathsep}{self.old}"

    def tearDown(self):
        os.environ["PATH"] = self.old
        self.tmp.cleanup()

    def fake(self, write_vtt: bool):
        info = {"title": "T", "channel": "C", "upload_date": "20260901", "duration": 90,
                "thumbnail": "https://i.ytimg.com/vi/x/maxresdefault.jpg", "webpage_url": "https://youtu.be/x"}
        vtt = ROLLING if write_vtt else ""
        script = f"""#!/usr/bin/env python3
import sys, json, pathlib
a = sys.argv
out = pathlib.Path(a[a.index("-o") + 1])
lang = a[a.index("--sub-langs") + 1]
pathlib.Path(str(out) + ".info.json").write_text({json.dumps(json.dumps(info))})
if {write_vtt!r}:
    pathlib.Path(str(out) + "." + lang + ".vtt").write_text({vtt!r})
"""
        f = self.bin / "yt-dlp"
        f.write_text(script)
        f.chmod(f.stat().st_mode | stat.S_IEXEC)

    def test_transcript_returns_meta_and_lines(self):
        self.fake(True)
        t = media.transcript("https://youtu.be/x", lang="en")
        self.assertEqual((t["title"], t["channel"], t["duration"]), ("T", "C", 90))
        self.assertEqual(t["lines"][0], (0.0, "so today we talk about"))

    def test_missing_language_is_clear_error(self):
        self.fake(False)
        with self.assertRaises(media.MediaError) as e:
            media.transcript("https://youtu.be/x", lang="ko")
        self.assertIn("--lang", str(e.exception))
        self.assertEqual(cli.main(["transcript", "https://youtu.be/x", "--lang", "ko"]), 2)


SHOWINFO = """[Parsed_showinfo_1 @ 0x1] n:   0 pts:      0 pts_time:0       duration:1
[Parsed_showinfo_1 @ 0x1] n:   1 pts:  12345 pts_time:12.345  duration:1
[Parsed_showinfo_1 @ 0x1] n:   2 pts:  99000 pts_time:99      duration:1
"""


class SlidesTest(unittest.TestCase):
    def test_scene_times_reads_pts_time(self):
        self.assertEqual(media.scene_times(SHOWINFO), [0.0, 12.345, 99.0])

    def test_slides_writes_frames_and_tsv(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "slides"
            video = Path(d) / "talk.mp4"
            video.write_bytes(b"x")

            class R:
                returncode = 0
                stderr = SHOWINFO

            def runner(cmd, **kw):
                pattern = cmd[-1]
                for i in range(3):
                    Path(pattern % (i + 1)).write_bytes(b"jpg")
                return R()

            got = media.slides(str(video), out, runner=runner)
            self.assertEqual(got, [("slide-001.jpg", 0.0), ("slide-002.jpg", 12.345), ("slide-003.jpg", 99.0)])
            self.assertEqual((out / "slides.tsv").read_text().splitlines()[1], "slide-002.jpg\t12.345")

    def test_missing_video_file_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(media.MediaError):
                media.slides(str(Path(d) / "nope.mp4"), Path(d) / "o")


if __name__ == "__main__":
    unittest.main()
