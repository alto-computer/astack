"""quest 코스 폴더 검사: 지도, 장, 퀴즈, 이전/다음/지도 링크."""
import re
from pathlib import Path

from . import check
from .check import Issue

MAP = "00-지도.html"
CHAPTER = re.compile(r"^(\d{2})-.+\.html$")
HREF = re.compile(r"""href=["']([^"'#?]+\.html)(?:[#?][^"']*)?["']""", re.I)


def _links(html: str) -> set[str]:
    return {h for h in HREF.findall(html) if "/" not in h and ":" not in h}


def check_course(folder: Path) -> list[tuple[str, Issue]]:
    folder = Path(folder)
    out: list[tuple[str, Issue]] = []
    chapters = sorted(p.name for p in folder.glob("*.html") if CHAPTER.match(p.name) and p.name != MAP)
    names = set(chapters) | ({MAP} if (folder / MAP).exists() else set())
    if MAP not in names:
        out.append((MAP, Issue("error", "map", f"{MAP}이 없습니다. 지도가 코스의 입구입니다")))
    else:
        linked = _links((folder / MAP).read_text(encoding="utf-8"))
        for c in chapters:
            if c not in linked:
                out.append((MAP, Issue("error", "unlinked", f"지도가 {c}로 링크하지 않습니다")))
    for name in sorted(names):
        html = (folder / name).read_text(encoding="utf-8")
        out += [(name, i) for i in check.check_html(html)]
        for target in sorted(_links(html)):
            if target not in names:
                out.append((name, Issue("error", "nav", f"없는 장으로 링크: {target}")))
        if name == MAP:
            continue
        if not re.search(r"""<details\b[^>]*class=["'][^"']*\bquiz\b""", html, re.I):
            out.append((name, Issue("error", "quiz", "장 끝 점검(details.quiz)이 없습니다")))
        if MAP not in _links(html):
            out.append((name, Issue("error", "nav", f"{MAP}로 돌아가는 링크가 없습니다")))
    return out
