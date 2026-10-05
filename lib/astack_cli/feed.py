"""feed 재료: 화이트리스트 채널(memory의 told 기록)의 새 영상 중 아직 이해물이 없는 것."""
import json
import re
import subprocess
import sys
from pathlib import Path

from . import memory, paths
from .media import MediaError, _yt

YT_ID = re.compile(r"(?:v=|youtu\.be/|/shorts/|/live/)([\w-]{11})")
CHANNEL_URL = re.compile(r"https://www\.youtube\.com/(?:@[^/\s]+|channel/[^/\s]+|c/[^/\s]+|user/[^/\s]+)/?$")
PREFIX = "feed:youtube:"


def whitelist() -> list[dict]:
    excluded = {r["key"][len("channel:"):] for r in memory.search("channel:") if r.get("type") == "exclude"}
    out, names = [], set()
    for r in memory.search(PREFIX):
        if r.get("type") != "whitelist":
            continue
        name = r["key"][len(PREFIX):]
        m = CHANNEL_URL.search(str(r.get("insight", "")))
        if not m or name in excluded or name in names:
            continue
        names.add(name)
        out.append({"name": name, "url": m.group(0).rstrip("/")})
    return out


def seed(name: str, url: str) -> bool:
    if not CHANNEL_URL.fullmatch(url):
        raise ValueError(f"YouTube 채널 URL이 아닙니다: {url}")
    if any(w["name"] == name for w in whitelist()):
        return False
    memory.add(json.dumps({"type": "whitelist", "key": PREFIX + name, "insight": f"아침 feed 화이트리스트 {url.rstrip('/')}",
                           "source": "told"}, ensure_ascii=False))
    return True


def seen_ids() -> set[str]:
    log = paths.outputs_log()
    ids: set[str] = set()
    if not log.exists():
        return ids
    for line in log.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        p = Path(parts[2])
        if p.is_file():
            ids |= set(YT_ID.findall(p.read_text(encoding="utf-8", errors="ignore")))
    return ids


def latest(url: str, limit: int = 5, cookies: str | None = None, runner=subprocess.run) -> list[dict]:
    cmd = ["yt-dlp", "--flat-playlist", "--playlist-end", str(limit), "--extractor-args",
           "youtubetab:approximate_date", "-J", url.rstrip("/") + "/videos"]
    try:
        r = _yt(cmd, cookies, runner)
    except MediaError:
        raise
    out = []
    try:
        entries = json.loads(r.stdout or "{}").get("entries", []) or []
    except ValueError:
        raise MediaError(f"채널 목록을 읽지 못했습니다: {url}")
    for e in entries:
        if e.get("id"):
            out.append({"id": e["id"], "title": e.get("title", ""), "url": f"https://www.youtube.com/watch?v={e['id']}",
                        "duration": e.get("duration") or 0, "upload_date": e.get("upload_date") or ""})
    return out


def candidates(since: str | None = None, per_channel: int = 5, cookies: str | None = None, runner=subprocess.run) -> list[dict]:
    seen = seen_ids()
    cut = (since or "").replace("-", "")
    out = []
    for ch in whitelist():
        try:
            vids = latest(ch["url"], per_channel, cookies=cookies, runner=runner)
        except MediaError as e:
            print(f"astack feed: 건너뜀 {ch['name']}: {e}", file=sys.stderr)
            continue
        for v in vids:
            if v["id"] in seen or (cut and v["upload_date"] and v["upload_date"] < cut):
                continue
            out.append({**v, "channel": ch["name"]})
    out.sort(key=lambda v: v["upload_date"], reverse=True)
    return out
