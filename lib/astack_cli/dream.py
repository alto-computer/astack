"""dream 재료 모으기: 오늘 생긴 이해물, 간격 복습(1·7·30일 전), 주간 모음. 상태 없이 날짜로만 고른다."""
import datetime
from pathlib import Path

from . import paths, recall

SPACED = (1, 7, 30)
OWN = {"dream", "feed"}


def _entry(i) -> dict:
    return {"path": str(i.path), "skill": i.skill, "title": i.title, "description": i.description, "ts": i.ts}


def collect(day: datetime.date, items=None) -> dict:
    if items is None:
        since = (day - datetime.timedelta(days=max(SPACED))).isoformat()
        items = recall.recall(since=since, limit=100000)
    items = [i for i in items if i.skill not in OWN and i.ts]
    by_day: dict[str, list] = {}
    for i in items:
        by_day.setdefault(i.ts[:10], []).append(i)
    today = sorted(by_day.get(day.isoformat(), []), key=lambda i: i.ts)
    spaced = []
    for k in SPACED:
        same = by_day.get((day - datetime.timedelta(days=k)).isoformat())
        if same:
            spaced.append({"days_ago": k, **_entry(max(same, key=lambda i: i.ts))})
    weekly = day.weekday() == 6
    week = []
    if weekly:
        start = (day - datetime.timedelta(days=6)).isoformat()
        week = [_entry(i) for i in sorted(items, key=lambda i: i.ts) if start <= i.ts[:10] <= day.isoformat()]
    return {"date": day.isoformat(), "weekly": weekly, "today": [_entry(i) for i in today], "spaced": spaced, "week": week}


def journal_path(day: datetime.date, name: str = "dream") -> Path:
    """Rooms가 있으면 그날 Journal 폴더의 파일(링크 아님), 없으면 ~/.astack/journal/."""
    home = paths.rooms_home()
    if home is not None:
        return home / "journal" / day.isoformat() / f"{name}.html"
    suffix = "" if name == "dream" else f"-{name}"
    return paths.journal_dir() / f"{day.isoformat()}{suffix}.html"
