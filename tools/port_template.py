"""사용자가 고른 Aside 템플릿을 astack 템플릿으로 옮긴다 (C6, C7).

배치·JS는 그대로 두고, Alto 디테일(alto-override.css)만 첫 <style> 끝에 덧붙인다.
원본이 바뀌면 다시 실행한다:
  python3 tools/port_template.py interview
  python3 tools/port_template.py seminar
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDE = ROOT / "docs/superpowers/specs/references/alto-override.css"
ASIDE = Path.home() / ".aside/u/0/skills/user"

HEAD = ('<meta charset="utf-8">\n'
        '<meta name="description" content="[이 이해물이 무엇인지 한 줄]">\n'
        '<meta name="rooms:created" content="[RFC3339 지금 시각]">\n'
        '<meta name="rooms:machine" content="[머신 이름]">\n')

ROOT_INTERVIEW = """:root{
  --bg:var(--canvas); --surface:var(--canvas); --panel:var(--surface); --tint:var(--accent-soft);
  --ink:var(--ink); --ink2:var(--ink); --muted:var(--ink-2); --faint:var(--ink-3);
  --line:var(--hairline); --line2:var(--hairline); --qborder:var(--accent-line);
  --accent:var(--accent); --accent-ink:var(--accent-ink); --accent-soft:var(--accent-soft);
  --serif:"Georgia","Noto Serif KR",serif;
  --sans:-apple-system,"Pretendard","Apple SD Gothic Neo",system-ui,sans-serif;
  --measure:720px; --wide:1120px;
}"""

ROOT_SEMINAR = """:root{
  --bg:var(--canvas); --surface:var(--canvas); --border:var(--hairline); --border-strong:var(--hairline);
  --ink:var(--ink); --muted:var(--ink-2); --faint:var(--ink-3); --accent:var(--accent);
  --tag-blue-fg:var(--accent); --tag-blue-bg:var(--accent-soft);
  --tag-green-fg:var(--accent-ink); --tag-green-bg:var(--accent-soft);
  --r:13px;
  --font:-apple-system,"Pretendard","Apple SD Gothic Neo",system-ui,sans-serif;
  --serif:"Iowan Old Style","Apple Garamond","Times New Roman",Georgia,serif;
}"""

JOBS = {
    "interview": {
        "src": ASIDE / "podcast-magazine/assets/template.html",
        "title": "[메인 제목] — 인터뷰",
        "markers": [('<header class="cover">', "30s"), ('<section class="standfirst">', "3m"), ('<footer class="foot">', "source")],
        "footer": "",
        "root": ROOT_INTERVIEW,
        "replacements": [
            ('href="SOURCE_URL"', 'href="{{SRC_URL}}"'),
            ('SHOW NAME</a>\n</footer>', 'SHOW NAME</a><br>요청 "{{요청 원문}}" · Claude Code가 썼습니다\n</footer>'),
        ],
    },
    "seminar": {
        "src": ASIDE / "seminar-report/assets/report-template.html",
        "title": "{{TITLE}} — 세미나",
        "markers": [('<header class="cover">', "30s"), ('<section class="mapwrap">', "3m")],
        "footer": '<footer class="astack-source" data-astack="source">원본 영상 {{SRC_URL}} · 요청 "{{요청 원문}}" · Claude Code가 썼습니다</footer>',
        "root": ROOT_SEMINAR,
        "replacements": [
            ("data-img/data-cap/data-ch", "data-cap/data-ch (슬라이드 경로는 .scene-fig img의 src)"),
        ],
    },
}


def port(src: str, override: str, title: str, markers: list[tuple[str, str]], source_footer: str, root: str = "",
         replacements: list[tuple[str, str]] = ()) -> str:
    s, n = re.subn(r'<meta charset="utf-8">\s*', lambda m: HEAD, src, count=1, flags=re.I)
    if n != 1:
        raise ValueError('<meta charset="utf-8">가 없습니다')
    s = re.sub(r"<title>.*?</title>", lambda m: f"<title>{title}</title>", s, count=1, flags=re.S)
    if root:
        s = re.sub(r":root\{.*?\}", lambda m: root, s, count=1, flags=re.S)
    i = s.index("</style>")
    s = s[:i] + "\n" + override.strip() + "\n" + s[i:]
    for tag, layer in markers:
        if s.count(tag) != 1:
            raise ValueError(f"표식 자리 {tag}가 {s.count(tag)}개입니다")
        s = s.replace(tag, tag[:-1] + f' data-astack="{layer}">')
    s = re.sub(r'<img\b[^>]*\bsrc="(images/[^"]+)"[^>]*>',
               lambda m: f"<!-- 그림 자리: {m.group(1)} (있으면 img 태그로 넣고, 없으면 비워 둔다) -->", s)
    s = re.sub(r'src="\{\{[^"]*\}\}"', 'src=""', s)
    s = re.sub(r'\s*data-img="[^"]*"', '', s)  # 무대는 .scene-fig img의 src만 읽는다 (C1)
    s = s.replace("감시가 아니라 X", "A가 아니라 X")
    for old, new in replacements:
        if old not in s:
            raise ValueError(f"바꿀 자리가 없습니다: {old}")
        s = s.replace(old, new)
    if source_footer:
        j = s.rindex("</body>")
        s = s[:j] + source_footer + "\n" + s[j:]
    return s


def main(name: str) -> None:
    job = JOBS[name]
    out = ROOT / f"skills/{name}/assets/template.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    html = port(job["src"].read_text(encoding="utf-8"), OVERRIDE.read_text(encoding="utf-8"),
                job["title"], job["markers"], job["footer"], job["root"], job["replacements"])
    out.write_text(html, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])
