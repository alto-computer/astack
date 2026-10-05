import os
import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path

from . import paths
from .check import _meta

HEAD = 64 * 1024
SKIP_DIRS = {"node_modules", "target", "dist", "build", ".git", ".next", "coverage"}


@dataclass
class Item:
    path: Path
    skill: str
    ts: str
    title: str
    description: str
    score: int


def project_root(start: Path) -> Path:
    p = Path(start).resolve()
    for d in [p, *p.parents]:
        if (d / ".git").exists():
            return d
    return p


def _head(p: Path) -> tuple[str, str, str]:
    with open(p, "rb") as f:
        t = f.read(HEAD).decode("utf-8", "ignore")
    title = re.search(r"<title[^>]*>(.*?)</title>", t, re.S | re.I)
    desc = _meta(t, "description")
    created = _meta(t, "rooms:created")
    return (unescape(title.group(1).strip()) if title else p.stem,
            unescape(desc) if desc else "",
            created or "")


def _from_log() -> dict[Path, tuple[str, str]]:
    log = paths.outputs_log()
    out: dict[Path, tuple[str, str]] = {}
    if not log.exists():
        return out
    for line in log.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        ts, skill, p = parts
        out[Path(p).resolve()] = (ts, skill)
    return out


def _from_roots() -> dict[Path, tuple[str, str]]:
    rf = paths.roots_file()
    roots = [Path(l.strip()).expanduser() for l in rf.read_text(encoding="utf-8").splitlines() if l.strip()] \
        if rf.exists() else [Path.home() / "personal"]
    out: dict[Path, tuple[str, str]] = {}
    for root in roots:
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
            parts = Path(d).parts
            # docs/astack/<스킬>/… 위치만 본다. 레포 이름이 astack이어도(~/personal/astack/docs/astack) 맞게 찾는다
            idx = [k for k in range(1, len(parts) - 1) if parts[k] == "astack" and parts[k - 1] == "docs"]
            if not idx:
                continue
            i = idx[-1]
            for f in files:
                if f.endswith(".html"):
                    p = (Path(d) / f).resolve()
                    out[p] = ("", parts[i + 1])
    return out


def recall(query: str = "", project: Path | None = None, since: str | None = None, limit: int = 10) -> list[Item]:
    entries = _from_log()
    if not any(p.is_file() for p in entries):
        entries = _from_roots()  # 로그가 없거나, 로그의 파일이 모두 사라졌다(레포 이동·다른 머신)
    terms = [t.lower() for t in query.split() if t]
    items: list[Item] = []
    for p, (ts, skill) in entries.items():
        if not p.is_file():
            continue
        if project is not None and not str(p).startswith(str(Path(project).resolve()) + os.sep):
            continue
        title, desc, created = _head(p)
        ts = ts or created
        if since and ts[:10] < since:
            continue
        score = sum(2 * title.lower().count(t) + desc.lower().count(t) for t in terms)
        if terms and score == 0:
            continue
        items.append(Item(p, skill, ts, title, desc, score))
    items.sort(key=lambda i: (i.score, i.ts), reverse=True)
    return items[:limit]
