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


def chapters(folder: Path) -> list[str]:
    return sorted(p.name for p in Path(folder).glob("*.html") if CHAPTER.match(p.name) and p.name != MAP)


def _read(path: Path, name: str, out: list) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        out.append((name, Issue("error", "io", str(e))))
        return None


def check_course(folder: Path) -> list[tuple[str, Issue]]:
    folder = Path(folder)
    out: list[tuple[str, Issue]] = []
    chs = chapters(folder)
    pages = sorted(p.name for p in folder.glob("*.html"))
    texts = {name: _read(folder / name, name, out) for name in pages}
    if MAP not in texts:
        out.append((MAP, Issue("error", "map", f"{MAP}이 없습니다. 지도가 코스의 입구입니다")))
    elif texts[MAP] is not None:
        linked = _links(texts[MAP])
        for c in chs:
            if c not in linked:
                out.append((MAP, Issue("error", "unlinked", f"지도가 {c}로 링크하지 않습니다")))
    for name in pages:
        html = texts[name]
        if html is None:
            continue
        out += [(name, i) for i in check.check_html(html)]
        for target in sorted(_links(html)):
            if not (folder / target).is_file():
                out.append((name, Issue("error", "nav", f"없는 파일로 링크: {target}")))
        if name not in chs:
            continue
        if not re.search(r"""<details\b[^>]*class=["'][^"']*\bquiz\b""", html, re.I):
            out.append((name, Issue("error", "quiz", "장 끝 점검(details.quiz)이 없습니다")))
        if MAP not in _links(html):
            out.append((name, Issue("error", "nav", f"{MAP}로 돌아가는 링크가 없습니다")))
    return out
