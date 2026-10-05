import contextlib
import io
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

    def test_html_entities_are_unescaped(self):
        vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n&gt;&gt; What&#39;s up?\n"
        self.assertEqual(media.parse_vtt(vtt), [(1.0, ">> What's up?")])


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
lang = a[a.index("--sub-langs") + 1].split(",")[0]
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
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["transcript", "https://youtu.be/x", "--lang", "ko"]), 2)


class Rc:
    def __init__(self, returncode=0, stderr=""):
        self.returncode, self.stderr = returncode, stderr


def yt_runner(files: dict, info: dict | None = None, calls: list | None = None):
    """가짜 yt-dlp: -o 경로 옆에 info.json과 주어진 vtt 파일들을 쓴다."""
    def run(cmd, **kw):
        if calls is not None:
            calls.append(cmd)
        out = Path(cmd[cmd.index("-o") + 1])
        Path(str(out) + ".info.json").write_text(json.dumps(info or {}))
        for suffix, text in files.items():
            Path(str(out) + suffix).write_text(text)
        return Rc()
    return run


class TrackChoiceTest(unittest.TestCase):
    def test_requests_orig_track_too(self):
        calls = []
        media.transcript("u", lang="en", runner=yt_runner({".en.vtt": ROLLING}, calls=calls))
        self.assertEqual(calls[0][calls[0].index("--sub-langs") + 1], "en,en-orig")

    def test_orig_track_wins_over_auto_translation(self):
        files = {".en.vtt": MANUAL, ".en-orig.vtt": ROLLING}
        t = media.transcript("u", lang="en", runner=yt_runner(files, info={"automatic_captions": {"en": []}}))
        self.assertEqual(t["lang"], "en-orig")
        self.assertEqual(t["lines"][0][1], "so today we talk about")

    def test_manual_track_wins_when_listed_in_subtitles(self):
        files = {".en.vtt": MANUAL, ".en-orig.vtt": ROLLING}
        t = media.transcript("u", lang="en", runner=yt_runner(files, info={"subtitles": {"en": []}}))
        self.assertEqual(t["lang"], "en")
        self.assertEqual(t["lines"][0][1], "First line of a cue")

    def test_plain_output_prints_lang(self):
        files = {".en-orig.vtt": ROLLING}
        real = media.transcript
        media.transcript = lambda url, **k: real(url, runner=yt_runner(files), **k)
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                cli.main(["transcript", "u"])
        finally:
            media.transcript = real
        self.assertIn("# lang en-orig", buf.getvalue())


LONG_429 = "\n".join(f"[youtube] x: step {i}" for i in range(40)) + \
    "\nERROR: [youtube] x: Unable to download video subtitles for 'en': HTTP Error 429: Too Many Requests\n"


class YtErrorTest(unittest.TestCase):
    def test_429_keeps_error_line_and_hints_cookies(self):
        def run(cmd, **kw):
            return Rc(1, LONG_429)
        with self.assertRaises(media.MediaError) as e:
            media.transcript("u", runner=run)
        msg = str(e.exception)
        self.assertIn("ERROR: [youtube] x: Unable", msg)
        self.assertIn("--cookies-from-browser", msg)
        self.assertNotIn("step 3", msg)

    def test_403_hints_upgrade(self):
        self.assertIn("brew upgrade yt-dlp", media._yt_error("ERROR: HTTP Error 403: Forbidden"))
        self.assertIn("brew upgrade yt-dlp", media._yt_error("ERROR: Requested format is not available"))

    def test_no_error_line_takes_last_three_lines(self):
        got = media._yt_error("a\nb\nc\nd\n")
        self.assertEqual(got, "b / c / d")

    def test_long_message_is_cut_at_a_line_boundary(self):
        err = "\n".join("ERROR: " + "x" * 150 + str(i) for i in range(5))
        got = media._yt_error(err)
        self.assertLessEqual(len(got), 400)
        self.assertTrue(got.startswith("ERROR: "))
        self.assertTrue(got.endswith("x1"))

    def test_cookies_flag_reaches_both_commands(self):
        calls = []
        media.transcript("u", cookies="chrome", runner=yt_runner({".en.vtt": ROLLING}, calls=calls))
        self.assertEqual(calls[0][1:3], ["--cookies-from-browser", "chrome"])
        with tempfile.TemporaryDirectory() as d:
            def run(cmd, **kw):
                calls.append(cmd)
                return Rc(1, "ERROR: boom")
            with self.assertRaises(media.MediaError):
                media.slides("https://youtu.be/x", Path(d) / "s", cookies="chrome", runner=run)
            self.assertEqual(calls[-1][1:3], ["--cookies-from-browser", "chrome"])

    def test_cli_accepts_cookies_flag(self):
        a = cli.build_parser().parse_args(["transcript", "u", "--cookies-from-browser", "chrome"])
        self.assertEqual(a.cookies_from_browser, "chrome")
        a = cli.build_parser().parse_args(["slides", "u", "o", "--cookies-from-browser", "chrome"])
        self.assertEqual(a.cookies_from_browser, "chrome")

    def test_missing_ytdlp_on_download_is_clear(self):
        def run(cmd, **kw):
            raise FileNotFoundError(cmd[0])
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(media.MediaError) as e:
                media.slides("https://youtu.be/x", Path(d) / "s", runner=run)
            self.assertIn("brew install yt-dlp", str(e.exception))
            self.assertFalse((Path(d) / "s").exists())


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

            got, _ = media.slides(str(video), out, runner=runner)
            self.assertEqual(got, [("slide-001.jpg", 0.0), ("slide-002.jpg", 12.345), ("slide-003.jpg", 99.0)])
            self.assertEqual((out / "slides.tsv").read_text().splitlines()[1], "slide-002.jpg\t12.345")

    def test_rerun_clears_old_frames_and_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "slides"
            out.mkdir()
            (out / "slide-009.jpg").write_bytes(b"old")
            (out / "slides.tsv").write_text("slide-009.jpg\t9\n")
            video = Path(d) / "talk.mp4"
            video.write_bytes(b"x")
            cmds = []

            def runner(cmd, **kw):
                cmds.append(cmd)
                for i in range(2):
                    Path(cmd[-1] % (i + 1)).write_bytes(b"jpg")
                return Rc(0, "pts_time:0 \npts_time:5 \n")

            got, _ = media.slides(str(video), out, runner=runner)
            self.assertEqual(got, [("slide-001.jpg", 0.0), ("slide-002.jpg", 5.0)])
            self.assertFalse((out / "slide-009.jpg").exists())
            self.assertIn("-y", cmds[0])

    def test_frame_and_time_count_mismatch_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            video = Path(d) / "talk.mp4"
            video.write_bytes(b"x")

            def runner(cmd, **kw):
                for i in range(3):
                    Path(cmd[-1] % (i + 1)).write_bytes(b"jpg")
                return Rc(0, "pts_time:0 \npts_time:5 \n")

            with self.assertRaises(media.MediaError) as e:
                media.slides(str(video), Path(d) / "o", runner=runner)
            self.assertIn("맞지 않습니다", str(e.exception))

    def test_download_ignores_partial_files(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            (out / "video.mp4.part").write_bytes(b"p")
            (out / "video.mp4").write_bytes(b"v")
            self.assertEqual(media._download("u", out, lambda cmd, **kw: Rc()).name, "video.mp4")

    def test_gaps_finds_long_stretches(self):
        self.assertEqual(media.gaps([0, 60, 147, 388, 400], 520), [(147, 388), (400, 520)])
        self.assertEqual(media.gaps([0, 60], 100), [])
        self.assertEqual(media.gaps([0, 60], 0), [])

    def test_slides_reports_gaps_from_duration(self):
        with tempfile.TemporaryDirectory() as d:
            video = Path(d) / "talk.mp4"
            video.write_bytes(b"x")

            def runner(cmd, **kw):
                for i in range(3):
                    Path(cmd[-1] % (i + 1)).write_bytes(b"jpg")
                return Rc(0, "  Duration: 00:06:40.50, start: 0.000000\npts_time:0 \npts_time:60 \npts_time:147 \n")

            _, gs = media.slides(str(video), Path(d) / "o", runner=runner)
            self.assertEqual(gs, [(147.0, 400.5)])

    def test_cli_prints_gap_warning(self):
        old = media.slides
        media.slides = lambda *a, **k: ([("slide-001.jpg", 0.0)], [(147.0, 388.0)])
        try:
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                self.assertEqual(cli.main(["slides", "v.mp4", "o"]), 0)
        finally:
            media.slides = old
        self.assertIn("슬라이드 없는 구간 02:27–06:28 (4분)", err.getvalue())
        self.assertIn("--threshold", err.getvalue())

    def test_crop_goes_before_select(self):
        with tempfile.TemporaryDirectory() as d:
            video = Path(d) / "talk.mp4"
            video.write_bytes(b"x")
            cmds = []

            def runner(cmd, **kw):
                cmds.append(cmd)
                Path(cmd[-1] % 1).write_bytes(b"jpg")
                return Rc(0, "pts_time:0 \n")

            media.slides(str(video), Path(d) / "o", crop="1280:720:320:0", runner=runner)
            vf = cmds[0][cmds[0].index("-vf") + 1]
            self.assertTrue(vf.startswith("crop=1280:720:320:0,select="), vf)
            with self.assertRaises(media.MediaError):
                media.slides(str(video), Path(d) / "o", crop="1280x720", runner=runner)

    def test_missing_video_file_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(media.MediaError):
                media.slides(str(Path(d) / "nope.mp4"), Path(d) / "o")


if __name__ == "__main__":
    unittest.main()
