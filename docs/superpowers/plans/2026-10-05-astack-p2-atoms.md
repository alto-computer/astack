# astack P2 원자 (interview · seminar · paper · repo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 소스 하나를 이해물 하나로 바꾸는 원자 스킬 네 개(interview, seminar, paper, repo)와, 그 스킬들이 쓰는 CLI 능력(자막, 슬라이드, PDF 페이지·크롭)을 만든다.

**Architecture:** 능력은 `bin/astack`의 하위 명령으로만 추가한다(C5 얇은 하네스). interview·seminar 템플릿은 사용자가 고른 Aside 템플릿에 `alto-override.css`만 덮어 `tools/port_template.py`로 옮긴다(C6, C7). paper·repo는 승인된 템플릿이 없으므로 spec과 같은 Alto 키트(본문 | 시각화)로 만들고 "첫 실제 결과물로 사용자 확인"을 남긴다.

**Tech Stack:** Python 3 표준 라이브러리 + unittest, 외부 명령 `yt-dlp`, `ffmpeg`, `swift`(PDFKit), `sips`. Pygments는 기존대로 선택.

**Spec:** `docs/superpowers/specs/2026-10-05-astack-v1-handoff.md` (§6.4 원자, §10 원칙, §11.1 능력, §14 마이그레이션, §15 P2, §20 명료화 — 20장이 우선)

## Global Constraints

- 스크립트는 Python 3 표준 라이브러리, 테스트는 unittest. 문법 강조만 Pygments 허용 (C2).
- 스크립트는 `bin/astack` 하나. 새 능력은 하위 명령으로 (C5).
- 템플릿은 사용자가 고른 결과물의 배치·JS를 그대로 두고 디자인 디테일만 Alto로 (C6). interview = podcast-magazine, seminar = seminar-report (C7).
- 캐릭터·그림은 의미 없이 넣지 않는다. 그림이 없으면 비운다 (C8).
- 메타 줄은 회색 한 줄, 세 항목까지 (C9).
- `description`, `rooms:created`(RFC3339), `rooms:machine`은 `<head>` 맨 앞, 앞 64KB 안 (C10).
- 완료는 `astack done <file> --skill <s>` (C11).
- 원자는 요약이 아니라 무손실 변환. "요약해줘"라고 해도 변환하고, 30초/3분 층이 요약 역할 (§6.4).
- 무거운 원자는 요청할 때만 반응: description을 "요청할 때"로 좁힌다. 링크만 붙여넣었을 땐 반응하지 않는다 (§6.1).
- description은 `Use when`으로 시작, 500자 이내, 워크플로 요약 금지 (§6.1).
- 글쓰기는 §20.2: 두괄식, 개조식이되 설명적으로, 주요 흐름에 "왜", 짧은 문장, AI 말투 금지, 출처 줄에 "Claude Code가 썼습니다"와 요청 원문.
- 원문 인용은 원문 그대로 두고 해설은 옆에 따로 (§20.2).
- 클론 캐시는 `~/.cache/astack/repos/` (§6.3).
- 레포는 공개다. 제3자 발언·사진·슬라이드·논문 figure가 든 결과물은 커밋하지 않는다(`.gitignore`). 템플릿에는 자리표시만.

## Review Focus

1. 자동 자막만 있는 영상 — 유튜브 자동 자막은 앞 줄을 반복하는 "굴러가는" 형식이다. 같은 문장이 두세 번 찍히면 안 된다. (Task 1 `test_rolling_auto_captions_are_deduped`)
2. 요청한 언어의 자막이 없음 — 빈 파일이 아니라 "lang을 바꿔 보라"는 오류와 종료 코드 2. (Task 1 `test_missing_language_is_clear_error`)
3. seminar 결과물의 `data-img`가 상대 경로로 남음 — 화면 오른쪽 슬라이드가 비어 보인다. inline이 `data-img`도 내장하고, 남으면 check가 잡는다. (Task 4 `test_data_img_becomes_data_uri`, `test_data_img_file_is_external`)
4. 채우지 않은 `{{자리표시}}`가 본문에 남은 채 done — check가 오류로 잡는다. (Task 4 `test_unfilled_braces_fail`)
5. 공백·한글이 든 PDF 경로, 여러 쪽 PDF — 쪽마다 `page-001.png`가 생기고 순서가 맞다. (Task 3 `test_pages_renders_each_page_in_order`)

---

## 파일 구조

```
lib/astack_cli/
  media.py            자막(yt-dlp + VTT 정리), 슬라이드(ffmpeg 장면 전환)    Task 1, 2
  pdf.py              PDF 쪽 렌더(swift PDFKit), 크롭(sips)                  Task 3
  pdf_pages.swift     PDFKit 렌더 스크립트                                   Task 3
  inline.py           data-img 내장 추가                                     Task 4
  check.py            {{…}} 자리표시, data-img 외부 파일 검사                 Task 4
  cli.py              transcript · slides · pdf 하위 명령                     Task 1~3
skills/design/assets/alto-ext.css   포스트잇(details.postit) 스타일          Task 4
skills/design/references/capabilities.md  능력 지도(§11.1)                   Task 10
tools/port_template.py             Aside 템플릿 → astack 템플릿               Task 5
skills/interview/{SKILL.md,assets/template.html}                           Task 5, 6
skills/seminar/{SKILL.md,assets/template.html}                             Task 5, 7
skills/paper/{SKILL.md,assets/template.html}                               Task 8
skills/repo/{SKILL.md,assets/template.html}                                Task 9
tests/test_media.py, test_pdf.py, test_port.py (+ 기존 test_inline/test_check/test_templates)
docs/superpowers/plans/2026-10-05-astack-p2-dogfood.md                     Task 10
```

---

### Task 1: `astack transcript` — 자막과 메타데이터

**Files:**
- Create: `lib/astack_cli/media.py`
- Modify: `lib/astack_cli/cli.py` (하위 명령 추가)
- Test: `tests/test_media.py`

**Interfaces:**
- Produces: `media.MediaError(Exception)`, `media.parse_vtt(text: str) -> list[tuple[float, str]]`, `media.fmt_ts(sec: float) -> str` (`"01:02:03"`), `media.transcript(url: str, lang: str = "en", runner=subprocess.run) -> dict` (키: `title, channel, upload_date, duration, thumbnail, url, lines`), CLI `astack transcript <url> [--lang en] [--json]`.

- [ ] **Step 1: Write the failing tests**

`tests/test_media.py`:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_media -v`
Expected: FAIL — `ImportError: cannot import name 'media'`

- [ ] **Step 3: Write `lib/astack_cli/media.py`**

```python
"""영상 소스 능력: 자막(yt-dlp)과 슬라이드(ffmpeg)."""
import json
import re
import subprocess
import tempfile
from pathlib import Path

TS = re.compile(r"(?:(\d+):)?(\d{2}):(\d{2})\.(\d{3})\s+-->")


class MediaError(Exception):
    pass


def fmt_ts(sec: float) -> str:
    s = int(sec)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def parse_vtt(text: str) -> list[tuple[float, str]]:
    """VTT를 (시작 초, 줄) 목록으로. 자동 자막의 굴러가는 반복 줄은 한 번만 남긴다."""
    out: list[tuple[float, str]] = []
    recent: list[str] = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        lines = block.strip().splitlines()
        idx = next((i for i, l in enumerate(lines) if TS.search(l)), None)
        if idx is None:
            continue
        h, m, s, ms = TS.search(lines[idx]).groups()
        start = int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        for raw in lines[idx + 1:]:
            line = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw)).strip()
            if not line or line in recent:
                continue
            out.append((start, line))
            recent = (recent + [line])[-3:]
    return out


def transcript(url: str, lang: str = "en", runner=subprocess.run) -> dict:
    with tempfile.TemporaryDirectory() as d:
        base = Path(d) / "src"
        cmd = ["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", lang,
               "--sub-format", "vtt", "--write-info-json", "-o", str(base), url]
        try:
            r = runner(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        except FileNotFoundError:
            raise MediaError("yt-dlp가 없습니다. `brew install yt-dlp`")
        if r.returncode != 0:
            raise MediaError(f"yt-dlp 실패: {(r.stderr or '').strip()[-300:]}")
        info_f = Path(str(base) + ".info.json")
        info = json.loads(info_f.read_text(encoding="utf-8")) if info_f.exists() else {}
        vtts = sorted(Path(d).glob("src*.vtt"))
        if not vtts:
            raise MediaError(f"'{lang}' 자막이 없습니다. --lang을 바꿔 보세요 (예: --lang ko, --lang en-orig)")
        lines = parse_vtt(vtts[0].read_text(encoding="utf-8"))
    return {"title": info.get("title", ""), "channel": info.get("channel") or info.get("uploader", ""),
            "upload_date": info.get("upload_date", ""), "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""), "url": info.get("webpage_url", url), "lines": lines}
```

- [ ] **Step 4: Add the CLI subcommand in `lib/astack_cli/cli.py`**

Add `from . import media as _media` with the other imports, then this handler above `build_parser`:

```python
def _cmd_transcript(args) -> int:
    try:
        t = _media.transcript(args.url, lang=args.lang)
    except _media.MediaError as e:
        print(f"astack transcript: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({**t, "lines": [[s, l] for s, l in t["lines"]]}, ensure_ascii=False))
        return 0
    print(f"# {t['title']}\n# {t['channel']} · {t['upload_date']} · {t['duration']}s\n# {t['url']}\n# thumbnail {t['thumbnail']}")
    for s, line in t["lines"]:
        print(f"[{_media.fmt_ts(s)}] {line}")
    return 0
```

and inside `build_parser`, before `return p`:

```python
    t = sub.add_parser("transcript", help="영상 자막과 메타데이터 (yt-dlp)")
    t.add_argument("url")
    t.add_argument("--lang", default="en")
    t.add_argument("--json", action="store_true")
    t.set_defaults(fn=_cmd_transcript)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_media -v && python3 -m unittest discover -s tests`
Expected: PASS, 전체 OK

- [ ] **Step 6: Commit**

```bash
git add lib/astack_cli/media.py lib/astack_cli/cli.py tests/test_media.py
git commit -m "feat(cli): astack transcript fetches captions and dedupes rolling auto-subs"
```

---

### Task 2: `astack slides` — 발표 영상에서 슬라이드 프레임

**Files:**
- Modify: `lib/astack_cli/media.py`, `lib/astack_cli/cli.py`
- Test: `tests/test_media.py` (클래스 추가)

**Interfaces:**
- Consumes: `media.MediaError`, `media.fmt_ts` (Task 1)
- Produces: `media.scene_times(stderr: str) -> list[float]`, `media.slides(src: str, outdir: Path, threshold: float = 0.08, runner=subprocess.run) -> list[tuple[str, float]]` (파일 이름, 초), 결과 폴더에 `slide-001.jpg…`와 `slides.tsv`(`file\tseconds`). CLI `astack slides <url|video> <outdir> [--threshold 0.08]`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_media.py`, before `if __name__`)

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest tests.test_media.SlidesTest -v`
Expected: FAIL — `AttributeError: module 'astack_cli.media' has no attribute 'scene_times'`

- [ ] **Step 3: Implement in `media.py`** (append)

```python
def scene_times(stderr: str) -> list[float]:
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", stderr)]


def _download(url: str, outdir: Path, runner) -> Path:
    cmd = ["yt-dlp", "-f", "bv*[height<=720]/b[height<=720]/b", "-o", str(outdir / "video.%(ext)s"), url]
    r = runner(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise MediaError(f"yt-dlp 실패: {(r.stderr or '').strip()[-300:]}")
    vids = sorted(outdir.glob("video.*"))
    if not vids:
        raise MediaError("영상을 받지 못했습니다")
    return vids[0]


def slides(src: str, outdir: Path, threshold: float = 0.08, runner=subprocess.run) -> list[tuple[str, float]]:
    """장면이 바뀌는 프레임을 slide-NNN.jpg로 뽑는다. 첫 프레임은 항상 포함."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if re.match(r"^https?://", src):
        video = _download(src, outdir, runner)
    else:
        video = Path(src)
        if not video.is_file():
            raise MediaError(f"영상 파일이 없습니다: {src}")
    vf = f"select='eq(n\\,0)+gt(scene\\,{threshold})',showinfo"
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-i", str(video), "-vf", vf, "-vsync", "vfr", "-q:v", "3",
           str(outdir / "slide-%03d.jpg")]
    try:
        r = runner(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        raise MediaError("ffmpeg가 없습니다. `brew install ffmpeg`")
    if r.returncode != 0:
        raise MediaError(f"ffmpeg 실패: {(r.stderr or '').strip()[-300:]}")
    times = scene_times(r.stderr or "")
    files = sorted(p.name for p in outdir.glob("slide-*.jpg"))
    pairs = list(zip(files, times))
    (outdir / "slides.tsv").write_text("".join(f"{f}\t{t:g}\n" for f, t in pairs), encoding="utf-8")
    return pairs
```

- [ ] **Step 4: CLI** — in `cli.py` add handler and parser entry:

```python
def _cmd_slides(args) -> int:
    try:
        pairs = _media.slides(args.src, Path(args.outdir), threshold=args.threshold)
    except _media.MediaError as e:
        print(f"astack slides: {e}", file=sys.stderr)
        return 2
    for f, t in pairs:
        print(f"{f}\t{_media.fmt_ts(t)}")
    return 0
```

```python
    s = sub.add_parser("slides", help="발표 영상에서 슬라이드가 바뀌는 프레임 뽑기 (ffmpeg)")
    s.add_argument("src")
    s.add_argument("outdir")
    s.add_argument("--threshold", type=float, default=0.08)
    s.set_defaults(fn=_cmd_slides)
```

- [ ] **Step 5: Run tests**

Run: `python3 -m unittest discover -s tests`
Expected: OK

- [ ] **Step 6: Commit**

```bash
git add lib/astack_cli/media.py lib/astack_cli/cli.py tests/test_media.py
git commit -m "feat(cli): astack slides extracts scene-change frames with timestamps"
```

---

### Task 3: `astack pdf pages|crop` — 논문 쪽 렌더와 figure 크롭

**Files:**
- Create: `lib/astack_cli/pdf.py`, `lib/astack_cli/pdf_pages.swift`
- Modify: `lib/astack_cli/cli.py`
- Test: `tests/test_pdf.py`

**Interfaces:**
- Produces: `pdf.PdfError(Exception)`, `pdf.pages(pdf_path: Path, outdir: Path, max_dim: int = 2200, runner=subprocess.run) -> list[Path]`, `pdf.crop(png: Path, x: int, y: int, w: int, h: int, out: Path, runner=subprocess.run) -> Path`. CLI `astack pdf pages <pdf> <outdir> [--max 2200]`, `astack pdf crop <png> <x> <y> <w> <h> <out>`.

- [ ] **Step 1: Write the failing tests** — `tests/test_pdf.py`

```python
import shutil
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import pdf  # noqa: E402


def tiny_pdf(n_pages: int) -> bytes:
    kids = " ".join(f"{3 + i} 0 R" for i in range(n_pages))
    objs = [b"<</Type/Catalog/Pages 2 0 R>>", f"<</Type/Pages/Kids[{kids}]/Count {n_pages}>>".encode()]
    objs += [b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 300]>>"] * n_pages
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj".encode() + o + b"endobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)
    out += f"trailer<</Size {len(objs) + 1}/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def tiny_png(w: int, h: int) -> bytes:
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def png_size(p: Path) -> tuple[int, int]:
    return struct.unpack(">II", p.read_bytes()[16:24])


@unittest.skipUnless(shutil.which("swift"), "swift 없음")
class PagesTest(unittest.TestCase):
    def test_pages_renders_each_page_in_order(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "논문 초안.pdf"
            src.write_bytes(tiny_pdf(3))
            got = pdf.pages(src, Path(d) / "out", max_dim=300)
            self.assertEqual([p.name for p in got], ["page-001.png", "page-002.png", "page-003.png"])
            self.assertTrue(all(p.stat().st_size > 0 for p in got))


class PagesErrorTest(unittest.TestCase):
    def test_missing_pdf_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(pdf.PdfError):
                pdf.pages(Path(d) / "none.pdf", Path(d) / "o")


@unittest.skipUnless(shutil.which("sips"), "sips 없음")
class CropTest(unittest.TestCase):
    def test_crop_cuts_requested_box(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "p.png"
            src.write_bytes(tiny_png(40, 30))
            out = pdf.crop(src, 5, 4, 20, 10, Path(d) / "fig.png")
            self.assertEqual(png_size(out), (20, 10))

    def test_crop_outside_image_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "p.png"
            src.write_bytes(tiny_png(40, 30))
            with self.assertRaises(pdf.PdfError):
                pdf.crop(src, 30, 0, 20, 10, Path(d) / "fig.png")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest tests.test_pdf -v`
Expected: FAIL — `ImportError: cannot import name 'pdf'`

- [ ] **Step 3: Write `lib/astack_cli/pdf_pages.swift`**

```swift
// usage: swift pdf_pages.swift <pdf> <outdir> <maxdim>
// 쪽마다 page-NNN.png를 쓰고 파일 이름을 한 줄씩 출력한다.
import AppKit
import PDFKit

let a = CommandLine.arguments
guard a.count == 4, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
    FileHandle.standardError.write("PDF를 열 수 없습니다\n".data(using: .utf8)!)
    exit(2)
}
let out = URL(fileURLWithPath: a[2])
let maxDim = CGFloat(Double(a[3]) ?? 2200)
for i in 0..<doc.pageCount {
    guard let page = doc.page(at: i) else { continue }
    let box = page.bounds(for: .mediaBox)
    let scale = maxDim / max(box.width, box.height)
    let w = Int(box.width * scale), h = Int(box.height * scale)
    guard let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8,
                                     samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                                     colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0),
          let ctx = NSGraphicsContext(bitmapImageRep: rep) else { exit(1) }
    let cg = ctx.cgContext
    cg.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    cg.fill(CGRect(x: 0, y: 0, width: w, height: h))
    cg.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: cg)
    guard let png = rep.representation(using: .png, properties: [:]) else { exit(1) }
    let name = String(format: "page-%03d.png", i + 1)
    try! png.write(to: out.appendingPathComponent(name))
    print(name)
}
```

- [ ] **Step 4: Write `lib/astack_cli/pdf.py`**

```python
"""논문 능력: PDF 쪽 렌더(swift PDFKit)와 figure 크롭(sips). macOS 전용."""
import struct
import subprocess
from pathlib import Path

SWIFT = Path(__file__).with_name("pdf_pages.swift")


class PdfError(Exception):
    pass


def _run(cmd, runner):
    try:
        return runner(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        raise PdfError(f"{cmd[0]}가 없습니다 (macOS 기본 도구)")


def pages(pdf_path: Path, outdir: Path, max_dim: int = 2200, runner=subprocess.run) -> list[Path]:
    pdf_path, outdir = Path(pdf_path), Path(outdir)
    if not pdf_path.is_file():
        raise PdfError(f"PDF가 없습니다: {pdf_path}")
    outdir.mkdir(parents=True, exist_ok=True)
    r = _run(["swift", str(SWIFT), str(pdf_path), str(outdir), str(max_dim)], runner)
    if r.returncode != 0:
        raise PdfError(f"렌더 실패: {(r.stderr or '').strip()[-300:]}")
    return [outdir / n for n in r.stdout.split()]


def _png_size(p: Path) -> tuple[int, int]:
    head = p.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise PdfError(f"PNG가 아닙니다: {p}")
    return struct.unpack(">II", head[16:24])


def crop(png: Path, x: int, y: int, w: int, h: int, out: Path, runner=subprocess.run) -> Path:
    png, out = Path(png), Path(out)
    W, H = _png_size(png)
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > W or y + h > H:
        raise PdfError(f"크롭 상자({x},{y},{w},{h})가 이미지({W}x{H}) 밖입니다")
    r = _run(["sips", "-c", str(h), str(w), "--cropOffset", str(y), str(x), str(png), "--out", str(out)], runner)
    if r.returncode != 0 or not out.is_file():
        raise PdfError(f"sips 실패: {(r.stderr or '').strip()[-300:]}")
    return out
```

- [ ] **Step 5: CLI** — in `cli.py` add `from . import pdf as _pdf`, handler and parser:

```python
def _cmd_pdf(args) -> int:
    try:
        if args.action == "pages":
            for p in _pdf.pages(Path(args.a), Path(args.b), max_dim=args.max):
                print(p)
        else:
            x, y, w, h = (int(v) for v in args.box)
            print(_pdf.crop(Path(args.a), x, y, w, h, Path(args.b)))
    except (_pdf.PdfError, ValueError) as e:
        print(f"astack pdf: {e}", file=sys.stderr)
        return 2
    return 0
```

```python
    pd = sub.add_parser("pdf", help="PDF 쪽을 PNG로 렌더(pages), 그림 영역 자르기(crop)")
    pd.add_argument("action", choices=["pages", "crop"])
    pd.add_argument("a", help="pages: PDF 경로 / crop: PNG 경로")
    pd.add_argument("box", nargs="*", help="crop: x y w h (픽셀)")
    pd.add_argument("b", help="pages: 출력 폴더 / crop: 출력 PNG")
    pd.add_argument("--max", type=int, default=2200)
    pd.set_defaults(fn=_cmd_pdf)
```

Add a CLI test to `tests/test_pdf.py` (`CropTest`):

```python
    def test_cli_crop(self):
        from astack_cli import cli
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "p.png"
            src.write_bytes(tiny_png(40, 30))
            self.assertEqual(cli.main(["pdf", "crop", str(src), "0", "0", "10", "10", str(Path(d) / "o.png")]), 0)
            self.assertEqual(cli.main(["pdf", "crop", str(src), "0", "0", "99", "10", str(Path(d) / "o.png")]), 2)
```

- [ ] **Step 6: Run tests**

Run: `python3 -m unittest tests.test_pdf -v && python3 -m unittest discover -s tests`
Expected: PASS (swift 테스트는 첫 실행에 10초쯤 걸린다)

- [ ] **Step 7: Commit**

```bash
git add lib/astack_cli/pdf.py lib/astack_cli/pdf_pages.swift lib/astack_cli/cli.py tests/test_pdf.py
git commit -m "feat(cli): astack pdf renders pages with PDFKit and crops figures with sips"
```

---

### Task 4: inline·check·키트 — `data-img`, `{{자리표시}}`, 포스트잇

**Files:**
- Modify: `lib/astack_cli/inline.py:73-83` (`inline_html`), `lib/astack_cli/check.py` (`check_html`), `skills/design/assets/alto-ext.css`
- Modify: `tests/test_templates.py` (`test_inlined_template_passes_contract`가 `placeholder`를 무시)
- Test: `tests/test_inline.py`, `tests/test_check.py`, `tests/test_kit.py`

**Interfaces:**
- Produces: inline이 `data-img="상대경로"`도 data URI로 바꾼다. check 오류 코드 `placeholder`(본문에 `{{…}}`), `external`(data-img가 파일을 가리킴). `alto-ext.css`에 `details.postit`.

- [ ] **Step 1: Failing tests**

`tests/test_inline.py` (InlineTest 안):

```python
    def test_data_img_becomes_data_uri(self):
        (self.dir / "s1.png").write_bytes(PNG)
        out = inline.inline_html(GOOD.replace("</body>", '<section class="scene" data-img="s1.png"></section></body>'), self.dir)
        self.assertIn('data-img="data:image/png;base64,', out)
```

`tests/test_check.py` (CheckTest 안):

```python
    def test_unfilled_braces_fail(self):
        html = GOOD.replace("</body>", "<p>{{SPEAKER}}의 발표</p></body>")
        self.assertIn("placeholder", codes(html))

    def test_braces_inside_code_are_fine(self):
        html = GOOD.replace("</body>", "<pre><code>{{ value }}</code></pre></body>")
        self.assertNotIn("placeholder", codes(html))

    def test_data_img_file_is_external(self):
        html = GOOD.replace("</body>", '<section data-img="slides/s1.jpg"></section></body>')
        self.assertIn("external", codes(html))
```

`tests/test_kit.py` (KitTest 안):

```python
    def test_ext_css_has_postit(self):
        css = (KIT / "alto-ext.css").read_text(encoding="utf-8")
        self.assertIn("details.postit", css)
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest tests.test_inline tests.test_check tests.test_kit`
Expected: 4 failures (`data-img`, `placeholder` ×1, `external`, `postit`)

- [ ] **Step 3: Implement**

`inline.py` — in `inline_html`, after the `<img` substitution line add:

```python
    html = re.sub(r"""(<[a-zA-Z][^>]*\bdata-img=)["']([^"']+)["']""", lambda m: _image(m, base_dir), html)
```

`check.py` — in `check_html`, after the `<link` loop add:

```python
    for m in re.finditer(r"""\bdata-img=["']([^"']+)["']""", html, re.I):
        if not m.group(1).startswith(("data:", "#")):
            issues.append(Issue("error", "external", f'data-img="{m.group(1)[:80]}"가 파일을 불러옵니다. astack inline으로 내장하세요'))
```

and right after `text = prose_text(html)`:

```python
    for m in re.finditer(r"\{\{[^{}\n]{1,80}\}\}", text):
        issues.append(Issue("error", "placeholder", f"채우지 않은 자리표시: {m.group(0)}"))
```

`alto-ext.css` — append:

```css
/* 포스트잇: 에이전트가 덧댄 조사. 기본 접힘, 본문과 구분되는 바탕 */
details.postit{display:inline-block;vertical-align:baseline;margin:0 2px}
details.postit>summary{list-style:none;cursor:pointer;font-size:12px;color:var(--ink-2);border:1px solid var(--hairline);border-radius:999px;padding:0 8px}
details.postit>summary::-webkit-details-marker{display:none}
details.postit[open]{display:block;margin:10px 0;padding:12px 14px;background:#fff8c5;border-radius:10px}
details.postit[open]>summary{margin-bottom:6px}
```

`tests/test_templates.py` — in `test_inlined_template_passes_contract`, change the errors line to:

```python
                errors = [f"{i.code}: {i.message}" for i in check.check_html(html) if i.level == "error" and i.code != "placeholder"]
```

- [ ] **Step 4: Run tests**

Run: `python3 -m unittest discover -s tests`
Expected: OK

- [ ] **Step 5: Commit**

```bash
git add lib/astack_cli/inline.py lib/astack_cli/check.py skills/design/assets/alto-ext.css tests/
git commit -m "feat: inline data-img, flag unfilled {{placeholders}}, add postit style"
```

---

### Task 5: `tools/port_template.py` — interview·seminar 템플릿 옮기기

**Files:**
- Create: `tools/port_template.py`, `skills/interview/assets/template.html`, `skills/seminar/assets/template.html`
- Test: `tests/test_port.py`

**Interfaces:**
- Consumes: `docs/superpowers/specs/references/alto-override.css`, Aside 원본 템플릿 경로(인자)
- Produces: `port_template.port(src: str, override: str, title: str, markers: list[tuple[str, str]], source_footer: str) -> str`. 생성된 두 템플릿(Task 6, 7이 SKILL.md에서 가리킨다).

원본 경로 (이 머신):
- interview: `~/.aside/u/0/skills/user/podcast-magazine/assets/template.html`
- seminar: `~/.aside/u/0/skills/user/seminar-report/assets/report-template.html`

- [ ] **Step 1: Failing tests** — `tests/test_port.py`

```python
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from astack_cli import check, inline  # noqa: E402

spec = importlib.util.spec_from_file_location("port_template", ROOT / "tools/port_template.py")
port_template = importlib.util.module_from_spec(spec)
spec.loader.exec_module(port_template)

SRC = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>옛 제목</title>
<style>:root{--accent:#3a5a7c}</style>
</head><body>
<header class="cover"><img src="images/masthead.jpg" alt=""></header>
<section class="standfirst">리드</section>
<section class="scene" data-img="01_slide.jpg"><img src="{{SLIDE_DATAURI}}"></section>
<footer class="foot">화자</footer>
<script>var x=1</script>
</body></html>"""


class PortTest(unittest.TestCase):
    def setUp(self):
        self.out = port_template.port(SRC, "/* alto */ .x{}", "[제목] — 인터뷰",
                                      [('<header class="cover">', "30s"), ('<section class="standfirst">', "3m"), ('<footer class="foot">', "source")],
                                      source_footer="")

    def test_astack_metas_come_first_in_head(self):
        head = self.out.split("<head>", 1)[1]
        self.assertTrue(head.lstrip().startswith('<meta charset="utf-8">\n<meta name="description"'))
        self.assertIn('<meta name="rooms:machine" content="[머신 이름]">', head)

    def test_override_css_is_appended_inside_first_style(self):
        style = self.out.split("<style>", 1)[1].split("</style>", 1)[0]
        self.assertTrue(style.rstrip().endswith("/* alto */ .x{}"))
        self.assertIn("--accent:#3a5a7c", style)

    def test_markers_title_and_images(self):
        self.assertIn('<header class="cover" data-astack="30s">', self.out)
        self.assertIn('<footer class="foot" data-astack="source">', self.out)
        self.assertIn("<title>[제목] — 인터뷰</title>", self.out)
        self.assertNotIn('src="images/', self.out)
        self.assertIn("그림 자리: images/masthead.jpg", self.out)
        self.assertNotIn('src="{{', self.out)
        self.assertIn('data-img=""', self.out)

    def test_script_untouched(self):
        self.assertIn("<script>var x=1</script>", self.out)

    def test_missing_marker_is_error(self):
        with self.assertRaises(ValueError):
            port_template.port(SRC, "", "t", [('<nav class="nope">', "3m")], "")

    def test_footer_added_when_source_footer_given(self):
        out = port_template.port(SRC.replace('<footer class="foot">화자</footer>', ""), "", "t",
                                 [('<header class="cover">', "30s"), ('<section class="standfirst">', "3m")],
                                 source_footer='<footer class="astack-source" data-astack="source">원본</footer>')
        self.assertIn('data-astack="source">원본</footer>\n</body>', out)


class GeneratedTemplatesTest(unittest.TestCase):
    def test_generated_templates_keep_one_title_and_markers(self):
        for name in ("interview", "seminar"):
            t = ROOT / f"skills/{name}/assets/template.html"
            html = t.read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertEqual(html.count("<title>"), 1)
                for layer in ("30s", "3m", "source"):
                    self.assertIn(f'data-astack="{layer}"', html)
                self.assertIn("#e31c5f", html)  # Alto 실이 덮였다


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest tests.test_port -v`
Expected: FAIL — `FileNotFoundError: .../tools/port_template.py`

- [ ] **Step 3: Write `tools/port_template.py`**

```python
"""사용자가 고른 Aside 템플릿을 astack 템플릿으로 옮긴다 (C6, C7).

배치·JS는 그대로 두고, Alto 디테일(alto-override.css)만 첫 <style> 끝에 덧붙인다.
원본이 바뀌면 다시 실행한다:
  python3 tools/port_template.py interview
  python3 tools/port_template.py seminar
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDE = ROOT / "docs/superpowers/specs/references/alto-override.css"
ASIDE = Path.home() / ".aside/u/0/skills/user"

HEAD = ('<meta charset="utf-8">\n'
        '<meta name="description" content="[이 이해물이 무엇인지 한 줄]">\n'
        '<meta name="rooms:created" content="[RFC3339 지금 시각]">\n'
        '<meta name="rooms:machine" content="[머신 이름]">\n')

JOBS = {
    "interview": {
        "src": ASIDE / "podcast-magazine/assets/template.html",
        "title": "[메인 제목] — 인터뷰",
        "markers": [('<header class="cover">', "30s"), ('<section class="standfirst">', "3m"), ('<footer class="foot">', "source")],
        "footer": "",
    },
    "seminar": {
        "src": ASIDE / "seminar-report/assets/report-template.html",
        "title": "{{TITLE}} — 세미나",
        "markers": [('<header class="cover">', "30s"), ('<section class="mapwrap">', "3m")],
        "footer": '<footer class="astack-source" data-astack="source">원본 영상 {{SOURCE_URL}} · 요청 "{{요청 원문}}" · Claude Code가 썼습니다</footer>',
    },
}


def port(src: str, override: str, title: str, markers: list[tuple[str, str]], source_footer: str) -> str:
    s, n = re.subn(r'<meta charset="utf-8">\s*', lambda m: HEAD, src, count=1, flags=re.I)
    if n != 1:
        raise ValueError('<meta charset="utf-8">가 없습니다')
    s = re.sub(r"<title>.*?</title>", lambda m: f"<title>{title}</title>", s, count=1, flags=re.S)
    i = s.index("</style>")
    s = s[:i] + "\n" + override.strip() + "\n" + s[i:]
    for tag, layer in markers:
        if s.count(tag) != 1:
            raise ValueError(f"표식 자리 {tag}가 {s.count(tag)}개입니다")
        s = s.replace(tag, tag[:-1] + f' data-astack="{layer}">')
    s = re.sub(r'<img\b[^>]*\bsrc="(images/[^"]+)"[^>]*>',
               lambda m: f"<!-- 그림 자리: {m.group(1)} (있으면 <img src=\"…\">로 넣고, 없으면 비워 둔다) -->", s)
    s = re.sub(r'src="\{\{[^"]*\}\}"', 'src=""', s)
    s = re.sub(r'data-img="[^"]*"', 'data-img=""', s)
    if source_footer:
        j = s.rindex("</body>")
        s = s[:j] + source_footer + "\n" + s[j:]
    return s


def main(name: str) -> None:
    job = JOBS[name]
    out = ROOT / f"skills/{name}/assets/template.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    html = port(job["src"].read_text(encoding="utf-8"), OVERRIDE.read_text(encoding="utf-8"),
                job["title"], job["markers"], job["footer"])
    out.write_text(html, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])
```

- [ ] **Step 4: Generate both templates and inspect**

Run:
```bash
python3 tools/port_template.py interview && python3 tools/port_template.py seminar
grep -c 'data-astack=' skills/interview/assets/template.html skills/seminar/assets/template.html   # 기대: 각 3
grep -o '<title>[^<]*' skills/*/assets/template.html
```
템플릿에 원본 에피소드 문구(예: 옛 `<title>`의 실제 제목)가 남았는지 본문을 훑는다. 남았으면 자리표시로 고친다(공개 레포).

- [ ] **Step 5: Run all tests** — `test_templates.py`가 새 템플릿 둘도 검사한다(메타 자리표시는 실패, 채우면 계약 통과).

Run: `python3 -m unittest discover -s tests`
Expected: OK

- [ ] **Step 6: 눈으로 확인** — 레퍼런스와 배치가 같은지 본다.

```bash
open skills/interview/assets/template.html docs/superpowers/specs/references/interview-reference-magazine.html
open skills/seminar/assets/template.html docs/superpowers/specs/references/seminar-reference-report.html
```
기대: 글꼴(Jost), 실 색 라벨, 진행 막대 `#ff385c`가 레퍼런스와 같다. 배치는 원본과 같다.

- [ ] **Step 7: Commit**

```bash
git add tools/port_template.py skills/interview/assets/template.html skills/seminar/assets/template.html tests/test_port.py
git commit -m "feat(templates): port podcast-magazine and seminar-report with Alto details"
```

---

### Task 6: `astack:interview` 스킬

**Files:**
- Create: `skills/interview/SKILL.md`
- Modify: `tests/test_templates.py` (`test_templates_exist`의 집합에 `interview` 추가)

**Interfaces:**
- Consumes: `astack transcript` (Task 1), `skills/interview/assets/template.html` (Task 5), `astack inline/check/done`.

- [ ] **Step 1: Failing test** — in `tests/test_templates.py` change the set to `{"spec", "change", "recall", "interview"}` and add:

```python
    def test_atom_skills_respond_only_on_request(self):
        for name in ("interview", "seminar", "paper", "repo"):
            p = ROOT / f"skills/{name}/SKILL.md"
            if not p.exists():
                continue
            front = p.read_text(encoding="utf-8").split("---", 2)[1]
            self.assertIn("요청할 때", front, name)
```

Run: `python3 -m unittest tests.test_templates -v` → Expected: FAIL (`interview` 없음)

- [ ] **Step 2: Write `skills/interview/SKILL.md`**

````markdown
---
name: interview
description: Use when 사용자가 팟캐스트, 인터뷰, 대담 영상이나 자막을 이해물(매거진)로 만들어 달라고 요청할 때. "이 팟캐스트 정리해줘", "인터뷰 아티팩트로", "/interview <링크>". 링크만 붙여넣었을 때는 쓰지 않는다.
---

# astack interview — 대화를 보존한 매거진

**약속:** 영상을 다 보지 않고도 대화 전체를 읽은 것처럼 안다. 맨 위 30초·3분만 읽어도 무엇을 얻을지 판단할 수 있다.

먼저 `astack:design`을 읽고 `astack memory search skill:interview`로 교정 기록을 본다.

## 입력과 출력
- 입력: 유튜브 링크, 자막 파일, 또는 녹취 텍스트. 진행자·게스트 이름.
- 출력: `docs/astack/interview/<날짜>-<slug>.html` 한 장 (현재 레포, 없으면 `~/personal/astack-out/`). 3시간이 넘으면 파트별 장 + 지도로 나눈다.

## 원칙 (design 색인에서)
- **convert-not-summarize**: 요약이 아니라 변환. 게스트의 주장·순서·예시·뉘앙스를 그대로. 빼는 건 군말, 반복, 광고, 겹친 말뿐. "요약해줘"라고 해도 매거진을 만든다.
- **anchor-to-source**: 타임스탬프가 있으면 챕터와 풀쿼트를 `원본URL&t=초s`로 잇는다.
- **one-name-per-concept**, 20.2 글쓰기 지침.

## 워크플로
1. 자막: `astack transcript <url> --lang <언어>`. 첫 줄을 확인한다(자동 자막은 언어가 틀리기 쉽다). 실패하면 `--lang en-orig`, `--lang ko`를 시도한다.
2. 파트(3~6)와 챕터(질문 하나 = 챕터 하나)로 나눈다. 파트마다 짧은 제목 + 게스트의 대표 한 문장.
3. 챕터마다: 앞 챕터와 잇는 리드(`.ch-deck`) 2~3문장, "구조 한눈에"(3~5 노드), 대화 턴(`turn q` 진행자 질문, `turn a` 게스트 답, `turn n` 내레이션), 풀쿼트 하나.
4. `assets/template.html`을 복사해 채운다. `<style>`과 `<script>`는 고치지 않는다. 블록 패턴은 복제한다(`data-pnav` id = `.partdiv id`).
5. 그림: 마스트헤드는 영상 썸네일(`transcript` 출력의 thumbnail)을 내려받아 문서 옆 폴더에 둔다. 게스트 사진은 깨끗한 출처가 있을 때만. 없으면 그림 자리를 비운다(C8). 의미 없는 그림·캐릭터 금지.
6. `<head>` 메타 세 개를 채운다(`rooms:created`는 `date -Iseconds`, `rooms:machine`은 `scutil --get ComputerName`).
7. `astack inline <f>` → `astack check <f>`(에러 0) → `astack done <f> --skill interview` → 채팅에 경로 한 줄.

## 완료 전 체크
- [ ] 게스트 답변이 원문 순서·내용을 지키는가(무작위 챕터 두 개를 자막과 대조)
- [ ] 30초(`cover`)와 3분(`standfirst`)만 읽고 무엇을 얻을지 알 수 있는가
- [ ] 그림 자리가 비었으면 빈 채로, 넣었으면 내장되었는가
- [ ] 출처 줄(`foot`)에 원본 링크, 요청 원문, "Claude Code가 썼습니다"
- [ ] `astack check` 에러 0
- [ ] 사용자가 선호·제외·교정을 말했으면 `astack memory add`

## Gotchas
- 유튜브 자동 자막만 있으면 언어 코드를 명시해야 한다. 첫 줄이 엉뚱한 언어면 다시 받는다.
- 화자 표시가 없으면 맥락으로 정한다(묻는 쪽이 진행자). 애매한 턴은 내레이션으로 두지 말고 화자를 정한다.
- 이미지 검색이 막히면 Openverse(`https://api.openverse.org/v1/images/?q=<검색어>&page_size=6&aspect_ratio=wide`)를 쓴다. 그래도 없으면 비운다.
- 결과물에는 제3자 발언과 사진이 들어간다. 공개 레포에 커밋하지 않는다.
````

- [ ] **Step 3: Run tests**

Run: `python3 -m unittest discover -s tests`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add skills/interview/SKILL.md tests/test_templates.py
git commit -m "feat(skills): interview atom on the approved magazine template"
```

---

### Task 7: `astack:seminar` 스킬

**Files:**
- Create: `skills/seminar/SKILL.md`
- Modify: `tests/test_templates.py` (`test_templates_exist` 집합에 `seminar`)

**Interfaces:**
- Consumes: `astack transcript` (Task 1), `astack slides` (Task 2), `data-img` 내장 (Task 4), seminar 템플릿 (Task 5).

- [ ] **Step 1: Failing test** — set becomes `{"spec", "change", "recall", "interview", "seminar"}`. Run → FAIL.

- [ ] **Step 2: Write `skills/seminar/SKILL.md`**

````markdown
---
name: seminar
description: Use when 사용자가 슬라이드 발표, 세미나, 강연, 컨퍼런스 영상을 이해물(스크롤하면 슬라이드가 바뀌는 리포트)로 만들어 달라고 요청할 때. "이 세미나 리포트로", "/seminar <링크>". 슬라이드 없는 대담은 interview. 링크만 붙여넣었을 때는 쓰지 않는다.
---

# astack seminar — 슬라이드가 따라오는 리포트

**약속:** 발표를 옆자리에서 들은 것처럼 안다. 글을 읽는 동안 그 순간의 슬라이드가 옆에 떠 있다.

먼저 `astack:design`을 읽고 `astack memory search skill:seminar`로 교정 기록을 본다.

## 지키는 순서
1. 화자에게 충실: 화자의 논지·순서·강조를 그대로. 화자의 결론이 결론이다. 새 주장을 얹지 않는다.
2. 가장 잘 전하기: 논지를 맨 앞에, 낯선 용어는 한 줄로 풀고, 제목만 읽어도 논증이 보이게.
3. 아래 규칙.

## 입력과 출력
- 입력: 발표 영상 링크(또는 파일).
- 출력: `docs/astack/seminar/<날짜>-<slug>.html` + 같은 이름의 `-slides/` 폴더(내장 전 원본).

## 워크플로
1. 슬라이드: `astack slides <url> <slug>-slides/`. `slides.tsv`의 시각을 기억한다. 비슷한 슬라이드가 합쳐졌거나(문턱 낮추기 `--threshold 0.05`) 빌드 애니메이션 중간 프레임이 섞였으면(마지막 완성 프레임만 남김) 손으로 고른다. 방송 화면 테두리(행사 로고, 화자 작은 화면)는 `astack pdf crop`으로 슬라이드 영역만 자른다.
2. 자막: `astack transcript <url>`. 슬라이드 시각 사이의 가운데를 경계로 자막을 장면에 나눈다.
3. 화자: 웹에서 약력을 찾아 3~4줄(현재 역할, 배경, 이전 일, 커리어를 꿰는 질문). 사진은 출처가 깨끗할 때만.
4. 쓰기: 챕터 = 논증의 뼈대, 슬라이드 하나 = 장면 하나(`<section class="scene" data-img="<slug>-slides/slide-NNN.jpg">`). 장면마다 제목, 통찰 먼저인 본문, 화자 원문 인용(`.excerpt`, 타임스탬프). 맨 위에 논증 지도.
5. `assets/template.html`을 복사해 채운다. `<style>`과 `<script>`는 고치지 않는다. `{{…}}` 자리표시를 모두 채운다(남으면 check가 막는다).
6. 메타 세 개 → `astack inline <f>`(슬라이드가 data URI로 들어간다) → `astack check <f>` → `astack done <f> --skill seminar`.

## 글쓰기 (원본에서 옮김)
- 짧은 문장, 생각 하나. 접속어(그래서, 그런데, 즉)로 논리를 겉으로 드러낸다.
- 시간순 중계가 아니라 통찰 먼저. 배경 → 큰 그림 → 세부 순서로 가르친다.
- 두 목소리를 구분: `.callout`(내 해설)과 `.excerpt`(화자 원문). 원문 인용은 원문 그대로.
- 도입은 짧게: 큰 질문 → 3~4문장 → 기대를 남기는 마무리. "이 글은 ~를 정리한 리포트다" 금지.

## 완료 전 체크
- [ ] 스크롤하면 장면마다 자기 슬라이드가 뜨는가(세 군데 확인)
- [ ] 제목만 읽어도 논증이 이어지는가
- [ ] 화자 원문 인용에 타임스탬프가 있는가
- [ ] `astack check` 에러 0, `{{` 없음

## Gotchas
- 장면 활성 기준은 "화면 가운데에 가장 가까운 장면"이다. 템플릿 JS를 고치지 않는다.
- 슬라이드 수십 장이면 파일이 3~4MB가 된다. 정상이다.
- 결과물에는 제3자 슬라이드·사진이 들어간다. 공개 레포에 커밋하지 않는다.
````

- [ ] **Step 3: Run tests** → OK

- [ ] **Step 4: Commit**

```bash
git add skills/seminar/SKILL.md tests/test_templates.py
git commit -m "feat(skills): seminar atom with scroll-synced slides"
```

---

### Task 8: `astack:paper` 스킬과 템플릿

**Files:**
- Create: `skills/paper/SKILL.md`, `skills/paper/assets/template.html`
- Modify: `tests/test_templates.py` (집합에 `paper`)

**Interfaces:**
- Consumes: `astack pdf pages|crop` (Task 3), `details.postit` (Task 4), 키트 마커 `<!--astack:css-->`/`<!--astack:js-->`.

**결정(사용자 확인 필요):** 승인된 paper 템플릿이 없다(C6). spec과 같은 키트(본문 | 그림)로 시작하고, 첫 실제 결과물을 사용자에게 보여 확정한다.

- [ ] **Step 1: Failing test** — set adds `paper`. Also add to `TemplateTest`:

```python
    def test_paper_template_has_postit_and_figure_slots(self):
        html = (ROOT / "skills/paper/assets/template.html").read_text(encoding="utf-8")
        self.assertIn('<details class="postit">', html)
        self.assertIn('class="vis" data-v="1"', html)
```

Run → FAIL.

- [ ] **Step 2: Write `skills/paper/assets/template.html`**

```html
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="description" content="[이 논문이 무엇을 보였는지 한 줄]">
<meta name="rooms:created" content="[RFC3339 지금 시각]">
<meta name="rooms:machine" content="[머신 이름]">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>[논문 제목] 리더</title>
<!--astack:css-->
</head><body data-depth="all">
<div class="top"><div class="top-in"><span class="mark">[학회 · 연도] <span>paper</span></span><span class="where" id="where"></span><span class="sp"></span></div><div class="prog" id="prog"></div></div>
<nav class="toc" aria-label="목차">
  <a href="#p0" data-sec="p0"><i></i><span>한눈에 보기</span></a>
  <a href="#p1" data-sec="p1"><i></i><span>[1 원문 섹션 제목]</span></a>
</nav>
<div class="wrap">
<header class="cover" id="p0" data-astack="30s">
  <div class="kick">Paper · [저자 외] · [학회 · 연도]</div>
  <h1>[원제] </h1>
  <div class="meta">paper · [쪽 수]쪽 · [읽는 시간]분</div>
  <p class="l30">[무엇을 풀었고, 어떻게, 얼마나 좋아졌나 두 줄. 수치는 원문 그대로]</p>
</header>
<section class="overview" data-astack="3m">
  <div><div class="kick">3분 · 한눈에 보기</div>
    <ul><li><b>문제.</b> [무엇이 안 됐나]</li><li><b>방법.</b> [핵심 아이디어]</li><li><b>결과.</b> [핵심 수치, baseline 대비]</li><li><b>한계.</b> [저자가 밝힌 한계]</li></ul></div>
  <div>[전체 방법 그림 SVG]</div>
</section>

<div class="reader"><div class="scenes">
  <div class="secHead" id="p1"><div class="n">1</div><h2>[원문 섹션 제목 그대로]</h2></div>
  <section class="scene lvl2" id="p1-1" data-i="1" data-sec="p1">
    <h3 class="st"><span class="no">1.1</span><span>[원문 하위 섹션 제목 그대로]</span></h3>
    <div class="lead"><p>[이 절이 주장하는 것 한 줄]</p></div>
    <div class="d2">
      <ul><li>[원문 내용을 구조로 펼친 줄. 수치·전제는 그대로]</li></ul>
      <p>[용어] <details class="postit"><summary>조사 ①</summary>[이 논문이 기대는 선행연구: 무엇을 했고, 왜 기대나(빌림·넘어섬·반박), 핵심 수치, 출처 링크]</details></p>
    </div>
  </section>
</div><aside class="stage">
  <div class="vis" data-v="1"><figure><!-- figs/fig-1.png --><img src="" alt="[Figure 1 캡션]"><figcaption>[Figure 1. 원문 캡션]</figcaption></figure></div>
</aside></div>
<footer data-astack="source">원문 [arXiv 또는 DOI 링크] · 요청 "[요청 원문]" · Claude Code가 썼습니다</footer>
</div>
<!--astack:js-->
</body></html>
```

그림 칸의 `<img src="">`는 템플릿이 계약 테스트를 통과하게 비워 둔 것이다. 실제 결과물에서는 `src="figs/fig-N.png"`로 채우고 `astack inline`이 내장한다.

- [ ] **Step 3: Write `skills/paper/SKILL.md`**

````markdown
---
name: paper
description: Use when 사용자가 논문 PDF나 arXiv 링크를 읽기 쉬운 이해물(무손실 리더)로 만들어 달라고 요청할 때. "이 논문 리더로", "논문 html", "/paper <링크>". 링크만 붙여넣었을 때는 쓰지 않는다.
---

# astack paper — 논문 무손실 리더

**약속:** 훑으면 결론이 튀어나오고, 파고들면 원문의 모든 수치·figure가 그 자리에 있다.

먼저 `astack:design`을 읽고 `astack memory search skill:paper`로 교정 기록을 본다.

## 불변식 (다른 규칙보다 먼저)
1. 정보량은 그대로. 수치·근거·사례·수식·figure·table 하나도 빠지지 않는다. "무엇을 뺄까"가 떠오르면 틀린 방향이다.
2. 섹션 구조 그대로. 제목·순서는 원문 그대로. 재구성은 섹션 안에서만. 더하는 것은 앞의 "한눈에 보기"와 포스트잇뿐.

## 마찰 → 처방 (힘을 쏟는 순서)
1. 줄글에 묻힌 논리 구조 → **구조화**: 계층은 중첩 목록, 병렬은 나란한 목록, 단계는 번호, 비교는 표.
2. 머릿속으로 그려야 하는 관계 → **시각화**: 아키텍처·데이터 흐름·ablation·비교는 SVG로 그린다. 원문 수치·라벨은 그림 안에 그대로.
3. 흩어진 정보 → **응집**: 결과 하나를 이해하는 데 필요한 figure·수치·전제를 한 장면에 모은다. "Figure 3 참조"로 보내지 않는다.
4. 생략된 전제 → **선해소**: 용어·기호는 처음 나온 자리에서 한 줄로 푼다. 수식은 "무엇을 계산하나" 한 줄 먼저, 기호는 원문 그대로.
5. (보조) 선행연구 → **포스트잇**: 이해가 기대는 소수만 웹으로 확인해 `<details class="postit">`에. 기본은 접힘. 본문에 섞지 않는다.

## 워크플로
1. 본문: arXiv면 `https://ar5iv.org/abs/<id>`를 읽어 섹션·수식·캡션을 얻는다. 아니면 PDF를 Read 도구로 쪽마다 읽는다.
2. 쪽 이미지: `astack pdf pages <pdf> <slug>-pages/`.
3. figure 전량: 쪽 이미지를 보고 상자를 정해 `astack pdf crop <page.png> x y w h figs/fig-N.png`. 애매하면 캡션 위 블록까지 넓게 자른다(누락보다 낫다). 개수를 본문의 "Figure N/Table N" 개수와 맞춘다.
4. 매핑: 어떤 figure·수치가 어떤 주장을 받치는지 표로 적고, 원문 수치 목록을 만든다(6번 검증에 쓴다).
5. `assets/template.html`을 복사해 섹션마다 `.secHead`, 하위 섹션마다 장면(`data-i`)과 그림 칸(`data-v`)을 늘린다. figure는 `<img src="figs/fig-N.png">`.
6. 무손실 검증(게이트): figure·table 개수와 수치 목록을 결과물과 대조한다. 하나라도 빠지면 채우고 다시.
7. 메타 → `astack inline` → `astack check` → `astack done <f> --skill paper`.

## 문체
- 어미 `~다`. 수치·고유명사·인용은 원문 그대로(외국어 인용은 번역 병기). 원문의 참조 번호([12])는 옮기지 않는다.
- 번역투 금지: "~를 통해"→"~로", "~에 의해 ~된"→능동, "~을 가지고 있다"→"~이 있다".
- 강조(`<mark>`, `<b>`)는 아껴 쓴다.

## 완료 전 체크
- [ ] figure·table 개수 = 원문 캡션 개수
- [ ] 수치 목록이 모두 결과물에 있다
- [ ] 섹션 제목·순서가 원문과 같다
- [ ] 포스트잇은 접혀 있고, 원문 내용은 하나도 접혀 있지 않다
- [ ] `astack check` 에러 0

## Gotchas
- 수식이 많으면 KaTeX를 쓰고 싶어지지만 외부 스크립트는 check가 막는다. 수식은 HTML로 조판하거나 원문 쪽 이미지를 잘라 넣는다.
- `astack pdf pages`는 첫 실행에 swift 컴파일로 10초쯤 걸린다.
- 결과물에는 논문 figure가 들어간다. 공개 레포에 커밋하지 않는다.
- **템플릿은 잠정이다.** 첫 실제 결과물을 사용자에게 보여 확정한다(C6).
````

- [ ] **Step 4: Run tests** → `python3 -m unittest discover -s tests` OK

- [ ] **Step 5: Commit**

```bash
git add skills/paper tests/test_templates.py
git commit -m "feat(skills): paper atom, lossless reader on the Alto kit (provisional template)"
```

---

### Task 9: `astack:repo` 스킬과 템플릿

**Files:**
- Create: `skills/repo/SKILL.md`, `skills/repo/assets/template.html`
- Modify: `tests/test_templates.py` (집합에 `repo`)

**Interfaces:**
- Consumes: 키트, `<pre data-lang data-start data-path data-who>` 코드 강조(기존 inline), `~/.cache/astack/repos/`.

**결정(사용자 확인 필요):** spec과 같은 키트(본문 | 시각화)를 쓴다. 남의 레포를 "학습 자료"로 읽는 구성이라 spec의 관심사·흐름 장과 모양이 같다.

- [ ] **Step 1: Failing test** — set adds `repo`; add:

```python
    def test_repo_template_has_evidence_tiers_and_weakness(self):
        html = (ROOT / "skills/repo/assets/template.html").read_text(encoding="utf-8")
        for s in ("ev ev-ok", "ev ev-mid", "ev ev-bad", 'id="r5"'):
            self.assertIn(s, html)
```

Run → FAIL.

- [ ] **Step 2: Write `skills/repo/assets/template.html`**

```html
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="description" content="[이 레포가 무엇이고 어디가 영리한지 한 줄]">
<meta name="rooms:created" content="[RFC3339 지금 시각]">
<meta name="rooms:machine" content="[머신 이름]">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>[owner/repo] 레포 읽기</title>
<!--astack:css-->
</head><body data-depth="all">
<div class="top"><div class="top-in"><span class="mark">[owner/repo] <span>repo</span></span><span class="where" id="where"></span><span class="sp"></span></div><div class="prog" id="prog"></div></div>
<nav class="toc" aria-label="목차">
  <a href="#r0" data-sec="r0"><i></i><span>0 · Overview</span></a>
  <a href="#r1" data-sec="r1"><i></i><span>1 · 아키텍처</span></a>
  <a href="#r2" data-sec="r2"><i></i><span>2 · 핵심 루프</span></a>
  <a href="#r3" data-sec="r3"><i></i><span>3 · 데이터 흐름</span></a>
  <a href="#r4" data-sec="r4"><i></i><span>4 · 영리한 부분과 왜</span></a>
  <a href="#r5" data-sec="r5"><i></i><span>5 · 약점</span></a>
</nav>
<div class="wrap">
<header class="cover" id="r0" data-astack="30s">
  <div class="kick">Repo · [owner/repo]</div>
  <h1>[이 레포가 하는 일 한 문장]</h1>
  <div class="meta">repo · [커밋 해시 7자리] · [읽는 시간]분</div>
  <p class="l30">[무엇을, 어떤 구조로, 어디가 영리한지 두 줄]</p>
  <div class="legend">실선 = 이 레포의 코드 · 점선 = 바깥(사용자, 외부 API, OS) · 빨간 실 = 지금 보는 단계</div>
</header>
<section class="overview" data-astack="3m">
  <div><div class="kick">3분 · 큰 그림</div><p>[주요 부품과 그 사이 흐름 두세 줄]</p></div>
  <div>[부품 지도 SVG]</div>
</section>

<div class="reader"><div class="scenes">
  <div class="secHead" id="r1"><div class="n">§1</div><h2>아키텍처와 폴더 구조</h2></div>
  <section class="scene lvl2" id="arch" data-i="1" data-sec="r1">
    <h3 class="st"><span class="no">1.1</span><span>[부품: 무엇을 맡나]</span></h3>
    <div class="lead"><p>[폴더 → 부품 대응 한 줄]</p></div>
    <div class="d2"><pre class="tree">[실제 폴더 트리, 중요한 것만]</pre></div>
  </section>

  <div class="secHead" id="r2"><div class="n">§2</div><h2>핵심 루프</h2></div>
  <section class="scene lvl2" id="loop" data-i="2" data-sec="r2">
    <h3 class="st"><span class="no">2.1</span><span>[루프 한 바퀴: 입력 → 처리 → 출력]</span></h3>
    <div class="lead"><p>[한 바퀴에 무슨 일이 일어나나]</p></div>
    <div class="d2"><p class="why"><b>왜 이렇게 만들었나.</b> [이유] <span class="ev ev-ok">확인</span> [커밋·PR·이슈 링크]</p></div>
    <div class="codes"><pre data-lang="ts" data-start="1" data-path="[파일]" data-who="[부품]"><code>[실제 코드]</code></pre></div>
  </section>

  <div class="secHead" id="r3"><div class="n">§3</div><h2>데이터 흐름</h2></div>
  <section class="scene lvl2" id="flow1" data-i="3" data-sec="r3">
    <h3 class="st"><span class="no">3.1</span><span>[사용자가 X를 하면]</span></h3>
    <div class="lead"><p>[누가, 언제, 무엇을 넘기나]</p></div>
    <div class="codes"><pre data-lang="ts" data-start="1" data-path="[파일]" data-who="[부품]"><code>[실제 코드]</code></pre></div>
  </section>

  <div class="secHead" id="r4"><div class="n">§4</div><h2>영리한 부분과 왜</h2></div>
  <section class="scene lvl2" id="clever1" data-i="4" data-sec="r4">
    <h3 class="st"><span class="no">4.1</span><span>[영리한 부분]</span></h3>
    <div class="lead"><p>[무엇이 영리한가, 보통은 어떻게 하나]</p></div>
    <div class="d2"><p class="why"><b>왜.</b> [의도] <span class="ev ev-mid">추론</span> [근거: 커밋 메시지·PR 설명·이슈. 코드는 동작의 증거이지 의도의 증거가 아니다]</p>
      <p class="why"><b>모름.</b> <span class="ev ev-bad">모름</span> [근거를 못 찾은 것]</p></div>
    <div class="codes"><pre data-lang="ts" data-start="1" data-path="[파일]" data-who="[부품]"><code>[실제 코드]</code></pre></div>
  </section>

  <div class="secHead" id="r5"><div class="n">§5</div><h2>약점과 내 일에 쓰면</h2></div>
  <section class="scene lvl2" id="weak1" data-i="5" data-sec="r5">
    <h3 class="st"><span class="no">5.1</span><span>[약점: 언제 깨지나]</span></h3>
    <div class="lead"><p>[조건과 결과. 이슈 링크]</p></div>
  </section>
</div><aside class="stage">
  <div class="vis" data-v="1">[부품 관계 SVG]</div>
  <div class="vis" data-v="2">[루프 시퀀스 SVG]</div>
  <div class="vis" data-v="3">[흐름 시퀀스 SVG]</div>
  <div class="vis" data-v="4">[영리한 부분 전후 비교 SVG]</div>
  <div class="vis" data-v="5"></div>
</aside></div>
<footer data-astack="source">원문 [레포 URL @ 커밋] · 요청 "[요청 원문]" · Claude Code가 썼습니다</footer>
</div>
<!--astack:js-->
</body></html>
```

Before writing, confirm the kit has `.ev-mid` and `pre.tree`: `grep -o 'ev-mid\|pre.tree\|\.tree' skills/design/assets/alto.css`. 없는 것은 `alto-ext.css`에 추가한다:

```css
.ev-mid{background:#fff4d6;color:#7a5600}
pre.tree{font-family:var(--mono);font-size:13px;line-height:1.6;background:var(--surface);border-radius:10px;padding:10px 12px;overflow-x:auto;margin:0}
```

(이미 있으면 추가하지 않는다. 기존 `.ev`, `.ev-ok`, `.ev-bad` 모양에 맞춰 색만 정한다.)

- [ ] **Step 3: Write `skills/repo/SKILL.md`**

````markdown
---
name: repo
description: Use when 사용자가 외부 GitHub 레포를 학습 자료로 읽어 이해물로 만들어 달라고 요청할 때. "이 레포 분석해줘", "어떻게 만들었는지 HTML로", "/repo <링크>". 내 코드베이스 동작 설명이나 링크만 붙여넣었을 때는 쓰지 않는다.
---

# astack repo — 남의 레포를 학습 자료로

**약속:** 레포를 클론하지 않고도 구조, 핵심 루프, 영리한 부분(파일:줄), 그렇게 만든 이유와 근거 등급, 약점을 안다.

먼저 `astack:design`을 읽고 `astack memory search skill:repo`로 교정 기록을 본다.

## 원칙
- **evidence-tiers**: 이유에는 등급을 단다. 확인(커밋·PR·이슈·문서에 적힘) / 추론(정황) / 모름. 코드는 동작의 증거이지 의도의 증거가 아니다.
- **anchor-to-source**: 모든 코드는 실제 파일과 실제 줄 번호. `data-path`에 `파일:줄`, 커밋 고정 링크.
- **definition-then-case**: 낯선 개념은 통용 이름과 일반 정의 → 이 레포의 사례.
- **build-up-diagrams**: 부품이 셋 이상이면 하나씩 쌓아 그린다.

## 워크플로
1. 클론: `git clone --depth 200 <url> ~/.cache/astack/repos/<owner>__<repo>` (있으면 `git -C … pull`). 커밋 해시를 적는다. 작업 폴더에 클론하지 않는다(레포 안 HTML이 이해물로 잡히는 오염).
2. 지도: README, 진입점, 폴더 구조. 부품 3~7개를 정한다.
3. 핵심 루프: 진입점부터 한 바퀴를 따라간다(`rg`). 실제 호출부를 발췌.
4. 데이터 흐름: 유저가 하는 대표 동작 2~3개.
5. 영리한 부분: 보통 방식과 다른 곳. `git log -S`, `git blame`, PR·이슈(`gh` 있으면)로 이유를 찾고 등급을 단다.
6. 약점: 열린 이슈, TODO, 테스트가 약한 곳, 확장이 막히는 곳. 근거 링크.
7. `assets/template.html`을 채운다 → 메타 → `astack inline` → `astack check` → `astack done <f> --skill repo`.

## 완료 전 체크
- [ ] 코드 발췌의 줄 번호가 실제 파일과 맞다(두 군데 연다)
- [ ] 모든 "왜"에 등급이 있다. 근거 없는 의도를 단정하지 않았다
- [ ] 약점에 근거 링크가 있다
- [ ] `astack check` 에러 0

## Gotchas
- 큰 레포는 `--depth 200`으로도 무겁다. 루프와 흐름에 필요한 경로만 읽는다.
- 스타 수는 참고만. 실사용·최근 활동·신뢰하는 사람의 언급이 더 낫다.
- **템플릿은 잠정이다.** 첫 실제 결과물을 사용자에게 보여 확정한다(C6).
````

- [ ] **Step 4: Run tests** → OK

- [ ] **Step 5: Commit**

```bash
git add skills/repo skills/design/assets/alto-ext.css tests/test_templates.py
git commit -m "feat(skills): repo atom with evidence-tiered why (provisional template)"
```

---

### Task 10: 능력 지도, README, 원칙 색인, 실제 소스 실행

**Files:**
- Create: `skills/design/references/capabilities.md`, `docs/superpowers/plans/2026-10-05-astack-p2-dogfood.md`
- Modify: `skills/design/SKILL.md` (원칙 색인 행 추가), `README.md` ("지금 있는 것"), `.gitignore`

- [ ] **Step 1: `skills/design/references/capabilities.md`**

```markdown
# 능력 지도

스킬 본문에는 능력 이름만 쓴다. 호스트 차이는 여기 한 곳에.

| 능력 | Claude Code · Codex (터미널) | Aside | 주의 |
|---|---|---|---|
| transcript | `astack transcript <url> --lang en` | `youtube.getTranscript(id,{lang,includeTimestamp:true})` | 자동 자막만 있으면 lang 명시. 첫 줄 확인 |
| slides | `astack slides <url> <dir>` | 브라우저 프레임 스캔 | 비슷한 슬라이드 합쳐짐 → `--threshold 0.05` |
| pdf-pages | `astack pdf pages <pdf> <dir>` | `aside.pdf.read` | macOS(PDFKit). 첫 실행 10초 |
| pdf-crop | `astack pdf crop <png> x y w h <out>` | canvas 크롭 | 좌표는 쪽 이미지 픽셀 |
| clone | `git clone --depth 200 <url> ~/.cache/astack/repos/<owner>__<repo>` | Bash git | 작업 폴더에 클론하지 않는다 |
| subagent | Agent(`general-purpose`) / Codex `spawn_agent` | subagent 도구 | 없으면 순차 |
| inline-assets | `astack inline <f>` | 같음 | `img src`, `data-img` |
| rooms-link | `astack done`이 `rooms link` 호출 | 같음 | 없으면 건너뜀 |
| memory | `astack memory add|search` | 같음 | |
```

- [ ] **Step 2: 원칙 색인** — `skills/design/SKILL.md`의 `## 원칙 색인` 표 끝에 추가:

```markdown
| convert-not-summarize | 모든 원자 | 정보량은 그대로, 형식만 바꾼다. "요약해줘"여도 변환 |
| speaker-first | interview, seminar | 화자의 논지·순서·강조가 주인공. 내 해설은 따로 |
| lossless-gate | paper | figure·table·수치 개수를 원문과 대조해야 끝난다 |
| build-up-diagrams | 부품 3개 이상 | 한 장에 다 그리지 말고 하나씩 쌓는다 |
```

- [ ] **Step 3: README** — "지금 있는 것" 제목을 `## 지금 있는 것 (P0~P2)`로 바꾸고 목록에 추가:

```markdown
- `astack:interview` 팟캐스트·인터뷰 → 대화를 보존한 매거진
- `astack:seminar` 슬라이드 발표 → 슬라이드가 따라오는 리포트
- `astack:paper` 논문 → 무손실 리더 (템플릿 잠정)
- `astack:repo` 남의 레포 → 구조·루프·영리한 부분·왜·약점 (템플릿 잠정)
- `bin/astack` transcript · slides · pdf (원자용 능력, `skills/design/references/capabilities.md`)
- 외부 도구: `yt-dlp`, `ffmpeg` (brew), macOS `swift`·`sips`
```

- [ ] **Step 4: `.gitignore`** — 원자 결과물(제3자 내용)을 막는다:

```
docs/astack/interview/
docs/astack/seminar/
docs/astack/paper/
docs/astack/repo/
```

- [ ] **Step 5: 실제 소스로 한 번씩 실행 (§15 P2 완료 기준)** — 사용자가 고른 소스로, 각 스킬을 실제로 부른다. 소스가 정해지지 않았으면 아래 기본값을 쓴다:
  - interview: 사용자가 최근에 본 팟캐스트 한 편 (없으면 가장 최근 `~/.aside/u/0/agents/main/artifacts/`의 매거진 원본 영상)
  - seminar: 같은 폴더의 세미나 리포트 원본 영상
  - paper: arXiv 논문 하나 (사용자 지정)
  - repo: `openai/codex` (P3 quest 예시와 이어진다)

  각각 `astack check` 에러 0, `astack done`까지. 결과물은 커밋하지 않는다(4단계 `.gitignore`).

- [ ] **Step 6: Dogfood 기록** — `docs/superpowers/plans/2026-10-05-astack-p2-dogfood.md`:

```markdown
# P2 dogfood

| 원자 | 소스 | 걸린 시간 | check | 사용자 판정 | 고칠 것 |
|---|---|---|---|---|---|
| interview | | | | | |
| seminar | | | | | |
| paper | | | | | |
| repo | | | | | |

paper·repo 템플릿 확정 여부: (사용자 결정)
```

- [ ] **Step 7: Run all tests and commit**

```bash
python3 -m unittest discover -s tests
git add skills/design README.md .gitignore docs/superpowers/plans/2026-10-05-astack-p2-dogfood.md
git commit -m "docs: capabilities map, principles, README for P2 atoms"
```

---

## 기본값과 열린 결정

| 항목 | 이 계획의 기본값 | 근거 | 확인 |
|---|---|---|---|
| paper·repo 템플릿 | spec과 같은 Alto 키트 | 승인 템플릿 없음(C6), 사용자가 본문 \| 시각화를 목표로 함 | 첫 결과물로 사용자 확정 |
| 원자 결과물 위치 | `docs/astack/<원자>/`, git 제외 | 공개 레포, 제3자 내용 | |
| 슬라이드 추출 | ffmpeg 장면 전환 | 원본은 브라우저 프레임 스캔(Aside 전용) | 첫 세미나 실행에서 문턱 조정 |
| PDF 렌더 | swift PDFKit | Python 표준 라이브러리로 불가, 이 맥에 poppler 없음 | |
| 수식 | HTML 조판 또는 쪽 이미지 | 외부 스크립트(KaTeX CDN)는 check가 막음 | |
