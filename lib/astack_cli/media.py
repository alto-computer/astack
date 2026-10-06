"""영상 소스 능력: 자막(yt-dlp)과 슬라이드(ffmpeg)."""
import html
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
            line = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", raw))).strip()
            if not line or line in recent:
                continue
            out.append((start, line))
            recent = (recent + [line])[-3:]
    return out


def _yt_error(stderr: str) -> str:
    """yt-dlp stderr에서 ERROR 줄(없으면 마지막 세 줄)을 줄 단위로 400자까지, 고칠 방법을 붙여."""
    lines = [l.strip() for l in (stderr or "").splitlines() if l.strip()]
    pick = [l for l in lines if l.startswith("ERROR:")] or lines[-3:]
    msg = pick[0] if pick else "알 수 없는 오류"
    for l in pick[1:]:
        if len(msg) + 3 + len(l) > 400:
            break
        msg += " / " + l
    if "429" in (stderr or ""):
        msg += " → 유튜브가 잠시 막았습니다. 몇 분 뒤 다시, 또는 --cookies-from-browser chrome"
    elif "403" in (stderr or "") or "Requested format is not available" in (stderr or ""):
        msg += " → yt-dlp가 오래됐을 수 있습니다: brew upgrade yt-dlp (또는 pip install -U yt-dlp)"
    return msg


def _yt(cmd: list[str], cookies: str | None, runner):
    if cookies:
        cmd = cmd[:1] + ["--cookies-from-browser", cookies] + cmd[1:]
    try:
        r = runner(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        raise MediaError("yt-dlp가 없습니다. `brew install yt-dlp`")
    if r.returncode != 0:
        raise MediaError(f"yt-dlp 실패: {_yt_error(r.stderr)}")
    return r


def _pick_vtt(d: Path, lang: str, info: dict) -> tuple[str, Path] | None:
    """사람이 만든 자막 > 원 자막(-orig) > 요청 언어 > 아무거나. 자동 번역 트랙을 피한다."""
    order = []
    if lang in (info.get("subtitles") or {}):
        order.append(lang)
    if not lang.endswith("-orig"):
        order.append(f"{lang}-orig")
    order.append(lang)
    for code in order:
        f = d / f"src.{code}.vtt"
        if f.exists():
            return code, f
    vtts = sorted(d.glob("src*.vtt"))
    if not vtts:
        return None
    return vtts[0].name.removeprefix("src.").removesuffix(".vtt"), vtts[0]


def transcript(url: str, lang: str = "en", cookies: str | None = None, runner=subprocess.run) -> dict:
    with tempfile.TemporaryDirectory() as d:
        base = Path(d) / "src"
        langs = lang if lang.endswith("-orig") else f"{lang},{lang}-orig"
        cmd = ["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", langs,
               "--sub-format", "vtt", "--write-info-json", "-o", str(base), url]
        _yt(cmd, cookies, runner)
        info_f = Path(str(base) + ".info.json")
        info = json.loads(info_f.read_text(encoding="utf-8")) if info_f.exists() else {}
        picked = _pick_vtt(Path(d), lang, info)
        if not picked:
            raise MediaError(f"'{lang}' 자막이 없습니다. --lang을 바꿔 보세요 (예: --lang ko, --lang en-orig)")
        code, vtt = picked
        lines = parse_vtt(vtt.read_text(encoding="utf-8"))
    return {"title": info.get("title", ""), "channel": info.get("channel") or info.get("uploader", ""),
            "upload_date": info.get("upload_date", ""), "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""), "url": info.get("webpage_url", url), "lang": code,
            "lines": lines}


def scene_times(stderr: str) -> list[float]:
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", stderr)]


def duration(stderr: str) -> float:
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0


def gaps(times: list[float], duration: float, limit: float = 90.0) -> list[tuple[float, float]]:
    """슬라이드가 limit초 넘게 안 바뀐 구간. 마지막 슬라이드부터 영상 끝까지도 본다."""
    edges = list(times) + ([duration] if duration and times and duration > times[-1] else [])
    return [(a, b) for a, b in zip(edges, edges[1:]) if b - a > limit]


def _download(url: str, outdir: Path, runner, cookies: str | None = None) -> Path:
    cmd = ["yt-dlp", "-f", "bv*[height<=720]/b[height<=720]/b", "-o", str(outdir / "video.%(ext)s"), url]
    try:
        _yt(cmd, cookies, runner)
    except MediaError:
        try:
            outdir.rmdir()
        except OSError:
            pass
        raise
    vids = sorted(p for p in outdir.glob("video.*") if p.suffix not in (".part", ".ytdl"))
    if not vids:
        raise MediaError("영상을 받지 못했습니다")
    return vids[0]


def slides(src: str, outdir: Path, threshold: float = 0.08, crop: str | None = None, cookies: str | None = None,
           runner=subprocess.run) -> tuple[list[tuple[str, float]], list[tuple[float, float]]]:
    """장면이 바뀌는 프레임을 slide-NNN.jpg로 뽑는다. 첫 프레임은 항상 포함.
    (프레임·시각 짝, 90초 넘게 슬라이드가 없는 구간)을 돌려준다."""
    if crop and not re.fullmatch(r"\d+:\d+:\d+:\d+", crop):
        raise MediaError(f"--crop은 W:H:X:Y (픽셀): {crop}")
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if re.match(r"^https?://", src):
        video = _download(src, outdir, runner, cookies)
    else:
        video = Path(src)
        if not video.is_file():
            raise MediaError(f"영상 파일이 없습니다: {src}")
    for f in outdir.glob("slide-*.jpg"):
        f.unlink()
    (outdir / "slides.tsv").unlink(missing_ok=True)
    vf = (f"crop={crop}," if crop else "") + f"select='eq(n\\,0)+gt(scene\\,{threshold})',showinfo"
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-y", "-i", str(video), "-vf", vf, "-vsync", "vfr", "-q:v", "3",
           str(outdir / "slide-%03d.jpg")]
    try:
        r = runner(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        raise MediaError("ffmpeg가 없습니다. `brew install ffmpeg`")
    if r.returncode != 0:
        raise MediaError(f"ffmpeg 실패: {(r.stderr or '').strip()[-300:]}")
    times = scene_times(r.stderr or "")
    files = sorted(p.name for p in outdir.glob("slide-*.jpg"))
    if len(files) != len(times):
        raise MediaError(f"프레임 {len(files)}장과 시각 {len(times)}개가 맞지 않습니다")
    pairs = list(zip(files, times))
    (outdir / "slides.tsv").write_text("".join(f"{f}\t{t:g}\n" for f, t in pairs), encoding="utf-8")
    return pairs, gaps(times, duration(r.stderr or ""))
