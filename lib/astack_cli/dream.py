"""dream 재료 모으기: 오늘 생긴 이해물, 간격 복습(1·7·30일 전), 주간 모음. 상태 없이 날짜로만 고른다."""
import datetime
from pathlib import Path

from . import paths, recall

SPACED = (1, 7, 30)
OWN = {"dream", "feed"}


def _entry(i, source: str = "log") -> dict:
    return {"path": str(i.path), "skill": i.skill, "title": i.title, "description": i.description, "ts": i.ts, "source": source}


def _rooms_item(target: Path, skill: str, since: datetime.date):
    try:
        mtime = datetime.datetime.fromtimestamp(target.stat().st_mtime).astimezone()
        if mtime.date() < since:
            return None
        title, desc, _ = recall._head(target)
    except OSError:
        return None
    return recall.Item(target, skill, mtime.isoformat(timespec="seconds"), title, desc, 0)


def rooms_items(home: Path, since: datetime.date) -> list[recall.Item]:
    """Rooms Home 폴더만 읽는다(앱·API 없음). 방 폴더의 html 링크 + journal/<날짜>/*.html(자체 산출물 제외)."""
    found: list[recall.Item] = []
    try:
        rooms = sorted(d for d in home.iterdir() if d.is_dir() and not d.name.startswith("."))
    except OSError:
        return found
    for room in rooms:
        journal = room.name == "journal"
        if journal:
            files = [f for day in sorted(room.glob("*")) if day.is_dir() and not day.name.startswith(".")
                     for f in day.iterdir() if f.name not in ("dream.html", "feed.html") and not f.is_symlink()]
        else:
            files = list(room.iterdir())
        for f in sorted(files):
            if f.suffix.lower() not in (".html", ".htm"):
                continue
            try:
                target = f.resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if not target.is_file():
                continue
            it = _rooms_item(target, "rooms:journal" if journal else f"rooms:{room.name}", since)
            if it:
                found.append(it)
    return found


def collect(day: datetime.date, items=None) -> dict:
    source: dict[int, str] = {}
    if items is None:
        since = day - datetime.timedelta(days=max(SPACED))
        items = recall.recall(since=since.isoformat(), limit=100000)
        home = paths.rooms_home()
        if home is not None:
            seen = set()
            for i in items:
                try:
                    seen.add(Path(i.path).resolve())
                except OSError:
                    seen.add(Path(i.path))
            extra = [r for r in rooms_items(home, since) if r.path not in seen]
            source = {id(r): "rooms" for r in extra}
            items = list(items) + extra
    items = [i for i in items if i.skill not in OWN and i.ts]
    by_day: dict[str, list] = {}
    for i in items:
        by_day.setdefault(i.ts[:10], []).append(i)
    today = sorted(by_day.get(day.isoformat(), []), key=lambda i: i.ts)
    spaced = []
    for k in SPACED:
        same = by_day.get((day - datetime.timedelta(days=k)).isoformat())
        if same:
            spaced.append({"days_ago": k, **_entry(max(same, key=lambda i: i.ts), source.get(id(max(same, key=lambda i: i.ts)), "log"))})
    weekly = day.weekday() == 6
    week = []
    if weekly:
        start = (day - datetime.timedelta(days=6)).isoformat()
        week = [_entry(i, source.get(id(i), "log")) for i in sorted(items, key=lambda i: i.ts) if start <= i.ts[:10] <= day.isoformat()]
    return {"date": day.isoformat(), "weekly": weekly, "today": [_entry(i, source.get(id(i), "log")) for i in today], "spaced": spaced, "week": week}


def journal_path(day: datetime.date, name: str = "dream") -> Path:
    """Rooms가 있으면 그날 Journal 폴더의 파일(링크 아님), 없으면 ~/.astack/journal/."""
    home = paths.rooms_home()
    if home is not None:
        return home / "journal" / day.isoformat() / f"{name}.html"
    suffix = "" if name == "dream" else f"-{name}"
    return paths.journal_dir() / f"{day.isoformat()}{suffix}.html"
