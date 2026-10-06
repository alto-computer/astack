import re
from html import unescape
from pathlib import Path

LABEL = re.compile(r"\b(Figure|Fig\.|Table|Algorithm)\s*([0-9]+[A-Za-z0-9]*|[A-Z][0-9]+[A-Za-z0-9]*)", re.I)
KIND = {"figure": "Figure", "fig.": "Figure", "table": "Table", "algorithm": "Algorithm"}


def strip_tags(html: str) -> str:
    h = re.sub(r"<(script|style)\b.*?</\1>|<!--.*?-->", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def labels(text: str) -> set[str]:
    return {f"{KIND[m.group(1).lower()]} {m.group(2).upper() if m.group(2)[0].isalpha() else m.group(2)}"
            for m in LABEL.finditer(text)}


def paper(out_html: str, source_text: str, numbers=()) -> list[str]:
    out_text = strip_tags(out_html)
    out_labels = labels(out_text)
    src = labels(source_text)
    missing = [f"{l}이 결과물에 없다" for l in sorted(src - out_labels)]
    figs = sum(1 for l in src if l.startswith("Figure "))
    imgs = len(re.findall(r"<img\b", re.sub(r"<!--.*?-->", " ", out_html, flags=re.S), re.I))
    if imgs < figs:
        missing.append(f"<img {imgs}개 < 원문 Figure {figs}개")
    missing += [f"수치 {n}가 결과물에 없다" for n in numbers if n and n not in out_text]
    return missing


def source_text(path) -> str:
    p = Path(path)
    t = p.read_text(encoding="utf-8")
    return strip_tags(t) if p.suffix.lower() in (".html", ".htm") else t
