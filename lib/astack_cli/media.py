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
