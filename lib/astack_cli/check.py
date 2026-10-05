import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path

HEAD_LIMIT = 64 * 1024
RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")
SLOP = ["핵심은", "사실상", "TL;DR", "결론적으로", "매우 ", "해당 "]
MAX_WORDS = 25
CONTENT = re.compile(r"""content=(["'])((?:(?!\1).)*?)\1""", re.I | re.S)


@dataclass
class Issue:
    level: str
    code: str
    message: str


def _meta(text: str, name: str):
    m = re.search(r"""<meta\s+[^>]*name=(["'])""" + re.escape(name) + r"""\1[^>]*>""", text, re.I)
    if not m:
        return None
    c = CONTENT.search(m.group(0))
    return c.group(2).strip() if c else ""  # group(2) is the captured value


def prose_text(html: str) -> str:
    h = re.sub(r"<(script|style|pre|code|svg|table)\b.*?</\1>", " ", html, flags=re.S | re.I)
    # Remove HTML comments
    h = re.sub(r"<!--.*?-->", " ", h, flags=re.S)
    # Add newlines at block boundaries (before removing other tags)
    h = re.sub(r"</?(p|li|h[1-6]|div|section|header|footer|dt|dd|tr|br|blockquote)\b[^>]*>", "\n", h, flags=re.I)
    # Remove other HTML tags
    h = re.sub(r"<[^>]+>", " ", h)
    # Unescape HTML entities
    h = unescape(h)
    # Normalize whitespace on each line but preserve newlines
    lines = [re.sub(r"\s+", " ", line).strip() for line in h.split("\n")]
    # Remove empty lines but keep newlines where they were
    result = "\n".join(line for line in lines if line)
    return result


def sentences(text: str) -> list[str]:
    # Split on period + space after Korean sentence endings, or on newlines
    return [s.strip() for s in re.split(r"(?<=[다요음함됨])\.\s+|\n", text) if s.strip()]


def _strip_non_prose(html: str) -> str:
    """Remove script, style, pre, code, svg, table, and comments from HTML."""
    h = re.sub(r"<(script|style|pre|code|svg|table)\b.*?</\1>", "", html, flags=re.S | re.I)
    h = re.sub(r"<!--.*?-->", "", h, flags=re.S)
    return h


def check_html(html: str) -> list[Issue]:
    issues: list[Issue] = []
    first = html.encode("utf-8")[:HEAD_LIMIT].decode("utf-8", "ignore")
    hm = re.search(r"<head[^>]*>(.*?)(</head>|$)", first, re.S | re.I)
    head = hm.group(1) if hm else ""
    for name in ("description", "rooms:created", "rooms:machine"):
        v = _meta(head, name)
        if v is None:
            if _meta(html, name) is not None:
                # Meta exists but is outside 64KB
                issues.append(Issue("error", "meta", f'<meta name="{name}">가 앞 64KB 밖에 있습니다. <head> 맨 앞, 64KB 안에 두세요'))
            else:
                # Meta is completely missing
                issues.append(Issue("error", "meta", f'<meta name="{name}">가 없습니다'))
        elif not v:
            issues.append(Issue("error", "meta", f"{name} 값이 비었습니다"))
        elif re.fullmatch(r"\[[^\]]*\]", v):
            issues.append(Issue("error", "meta", f"{name}: 자리표시가 채워지지 않았습니다: {v}"))
        elif name == "rooms:created" and not RFC3339.match(v):
            issues.append(Issue("error", "meta", f"rooms:created가 RFC3339가 아닙니다: {v}"))

    html_without_non_prose = _strip_non_prose(html)
    n_titles = len(re.findall(r"<title[\s>]", html_without_non_prose, re.I))
    if n_titles != 1:
        issues.append(Issue("error", "title", f"<title>이 {n_titles}개입니다. 본문의 <title> 글자는 &lt;title&gt;로 쓰세요"))

    for tag in ("script", "img", "iframe", "source", "video", "audio"):
        for m in re.finditer(rf"""<{tag}\b[^>]*\bsrc=["']([^"']+)["']""", html, re.I):
            if not m.group(1).startswith(("data:", "#")):
                issues.append(Issue("error", "external", f'<{tag} src="{m.group(1)[:80]}">가 파일을 불러옵니다. astack inline으로 내장하세요'))
    for m in re.finditer(r"<link\b[^>]*>", html, re.I):
        if re.search(r"""rel=["'][^"']*(stylesheet|preload|preconnect|icon)""", m.group(0), re.I):
            issues.append(Issue("error", "external", f"{m.group(0)[:80]}가 파일을 불러옵니다"))

    # Scan url() only in <style> blocks and style attributes
    style_content = ""
    # Extract <style>...</style> blocks
    for m in re.finditer(r"<style[^>]*>(.*?)</style>", html, re.S | re.I):
        style_content += m.group(1) + "\n"
    # Extract style attributes (use backreference to handle quotes inside value)
    for m in re.finditer(r"""\bstyle=(["'])(.*?)\1""", html, re.I | re.S):
        style_content += m.group(2) + "\n"

    for m in re.finditer(r"""url\(\s*["']?([^)"']+)""", style_content):
        if not m.group(1).startswith(("data:", "#")):
            issues.append(Issue("error", "external", f"url({m.group(1)[:60]})가 파일을 불러옵니다"))

    if "<!--astack:" in html:
        issues.append(Issue("error", "marker", "<!--astack:...--> 표식이 남아 있습니다. astack inline을 먼저 실행하세요"))
    for layer in ("30s", "3m"):
        if not re.search(rf"""data-astack=["']{layer}["']""", html):
            issues.append(Issue("error", "layer", f'data-astack="{layer}" 요소가 없습니다'))
    if not re.search(r"""data-astack=["']source["']""", html):
        issues.append(Issue("error", "source", 'data-astack="source" 요소(원문, 요청, "Claude Code가 썼습니다")가 없습니다'))

    text = prose_text(html)
    for p in SLOP:
        if p in text:
            issues.append(Issue("warn", "slop", f'AI 말투: "{p.strip()}"'))
    for s in sentences(text):
        n = len(s.split())
        if n > MAX_WORDS:
            issues.append(Issue("warn", "long", f"{n}어절 문장: {s[:40]}…"))
    return issues


def check_file(path) -> list[Issue]:
    return check_html(Path(path).read_text(encoding="utf-8"))
