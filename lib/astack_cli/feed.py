"""feed 재료: 화이트리스트 채널(memory의 told 기록)의 새 영상 중 아직 이해물이 없는 것."""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import memory, paths
from .media import MediaError, _yt

YT_ID = re.compile(r"(?:v=|youtu\.be/|/shorts/|/live/)([\w-]{11})")
CHANNEL_URL = re.compile(r"https://www\.youtube\.com/(?:@[^/\s]+|channel/[^/\s]+|c/[^/\s]+|user/[^/\s]+)/?$")
PREFIX = "feed:youtube:"


def whitelist() -> list[dict]:
    """채널마다 가장 최근 told 기록(날짜, 같으면 줄 순서)이 이긴다. 제외 뒤 다시 seed하면 돌아온다."""
    last: dict[str, tuple] = {}
    for i, r in enumerate(memory.parse(memory.read_lines())):
        if r.get("source") != "told" or not isinstance(r.get("key"), str):
            continue
        if r.get("type") == "whitelist" and r["key"].startswith(PREFIX):
            m = CHANNEL_URL.search(str(r.get("insight", "")))
            if not m:
                continue
            name, url = r["key"][len(PREFIX):], m.group(0).rstrip("/")
        elif r.get("type") == "exclude" and r["key"].startswith("channel:"):
            name, url = r["key"][len("channel:"):], None
        else:
            continue
        rank = (str(r.get("date", "")), i)
        if name not in last or rank >= last[name][0]:
            last[name] = (rank, url)
    return [{"name": n, "url": url} for n, (_, url) in sorted(last.items(), key=lambda kv: kv[1][0]) if url]


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
                        "duration": e.get("duration") or 0, "upload_date": _entry_date(e)})
    return out


def _entry_date(e: dict) -> str:
    """upload_date 우선, 없으면 timestamp(UTC)를 YYYYMMDD로. 둘 다 없으면 ""(날짜 없음)."""
    if e.get("upload_date"):
        return str(e["upload_date"])
    ts = e.get("timestamp")
    if isinstance(ts, (int, float)) and not isinstance(ts, bool) and ts > 0:
        try:
            return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y%m%d")
        except (OverflowError, OSError, ValueError):
            return ""
    return ""


def fill_dates(vids: list[dict], cookies: str | None = None, runner=subprocess.run) -> int:
    """날짜 없는 항목의 upload_date를 yt-dlp 한 번으로 채운다(제자리 수정). 채운 개수를 돌려준다.

    비공개·멤버십 영상이 섞이면 yt-dlp는 나머지를 찍고 exit 1이라, 실패해도 stdout은 읽는다.
    하나도 못 읽었을 때만 MediaError(원인은 _yt가 붙인 메시지)."""
    if not vids:
        return 0
    cmd = ["yt-dlp", "--skip-download", "--no-warnings", "--ignore-errors", "--print", "%(id)s %(upload_date)s"] \
        + [v["url"] for v in vids]
    last = []

    def capture(*a, **kw):
        last.append(runner(*a, **kw))
        return last[-1]

    err = None
    try:
        r = _yt(cmd, cookies, capture)
    except MediaError as e:
        if not last:
            raise
        r, err = last[-1], e
    dates = {}
    for line in (r.stdout or "").splitlines():
        parts = line.split()
        if len(parts) == 2 and re.fullmatch(r"\d{8}", parts[1]):
            dates[parts[0]] = parts[1]
    if not dates and err:
        raise err
    n = 0
    for v in vids:
        if v["id"] in dates:
            v["upload_date"] = dates[v["id"]]
            n += 1
    return n


def candidates(since: str | None = None, per_channel: int = 5, cookies: str | None = None, runner=subprocess.run) -> list[dict]:
    seen = seen_ids()
    cut = (since or "").replace("-", "")
    out = []
    taken = set(seen)
    for ch in whitelist():
        try:
            vids = latest(ch["url"], per_channel, cookies=cookies, runner=runner)
        except MediaError as e:
            print(f"astack feed: 건너뜀 {ch['name']}: {e}", file=sys.stderr)
            continue
        todo = [v for v in vids if not v["upload_date"] and v["id"] not in seen]
        if todo and cut:
            try:
                fill_dates(todo, cookies=cookies, runner=runner)
            except MediaError as e:
                print(f"astack feed: 날짜를 못 읽음 {ch['name']}: {e}", file=sys.stderr)
        for v in vids:
            if v["id"] in taken or (cut and v["upload_date"] and v["upload_date"] < cut):
                continue
            taken.add(v["id"])
            out.append({**v, "channel": ch["name"]})
    undated = [v for v in out if not v["upload_date"]]
    if undated and cut:
        print(f"astack feed: 날짜 없는 후보 {len(undated)}개 — since로 거르지 못함", file=sys.stderr)
    dated = sorted((v for v in out if v["upload_date"]), key=lambda v: v["upload_date"], reverse=True)
    return dated + undated
