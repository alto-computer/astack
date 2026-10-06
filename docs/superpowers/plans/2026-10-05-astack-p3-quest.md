# astack P3 탐구와 수렴 (quest · study · map · astack 입구) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 한 줄 질문을 코스(지도 + 장)로 만드는 quest, 이해물에 덧붙여 깊게 파는 study, 방마다 수렴하는 map, 무엇이든 던지면 알맞은 스킬로 보내는 입구 `astack`을 만든다.

**Architecture:** 판단은 스킬(에이전트), 형식은 CLI. CLI에는 결정적인 부분만 넣는다: 입력 분류(`astack route`), 코스 구조 검사(`astack course check`), 점검 퀴즈 컴포넌트(키트). 코스 장 집필은 quest 스킬이 서브에이전트로 병렬 처리하고, 원자(P2)를 부품으로 부른다.

**Tech Stack:** Python 3 표준 라이브러리 + unittest, 키트(alto.css, alto-ext.css, reader.js) + 새 quiz.js.

**Spec:** `docs/superpowers/specs/2026-10-05-astack-v1-handoff.md` (§6.3 quest·study, §6.5 map, §6.6 astack, §8 내장 점검, §10 원칙, §15 P3, §20)

## Global Constraints

- P2 계획(`2026-10-05-astack-p2-atoms.md`)의 Global Constraints를 모두 따른다.
- 코스 폴더: `docs/astack/quest/<날짜>-<slug>/00-지도.html`, `01-….html` ~ `NN-….html` (§6.3).
- 한 장 = 질문 하나, 10~15분. 장마다 30초·3분·본문 + 끝에 점검. 이전/다음/지도 링크. 같은 개념은 같은 이름 (§6.3).
- 깊이: Quick 지도+5장 / Standard(기본) 지도+10~12장(why 장, 실험 또는 실습 장 포함) / Deep 지도+20장 이상 (§6.3).
- quest는 비동기: 확인을 기다리지 않는다. 분해 결과를 첫 응답으로 보여주고 바로 진행 (§6.3).
- 내장 점검: 객관식은 즉시 채점 + 오답마다 "흔한 오해" 해설 + 원문 링크. 주관식은 정답 공개. 서술형은 모범답안 + 핵심 포인트. 질문은 이해형(왜, 만약, 비교, 적용). 상태는 페이지 안에서만 — localStorage 금지 (§8).
- 실험 브라우저 가드레일: 로그인 사이트는 읽기만, 실제 프로필 캐시·쿠키 지우지 않음, 프로필 쓰는 작업은 순차, 반복 측정은 로컬 페이지 (§6.3).
- map은 문서가 쌓여도 두꺼워지지 않고 정확해진다(converge). 사용자는 20개 대신 지도 한 장을 읽는다 (§6.5).
- 입구 라우팅: YouTube 대담→interview, 슬라이드 발표→seminar, arXiv/PDF→paper, GitHub→repo, 스펙 md→spec, 질문→quest, "오늘 정리"→dream (§6.6).

## Review Focus

1. 코스의 장 파일이 지도에서 링크되지 않음 — 독자가 장에 도달할 수 없다. `course check`가 잡는다. (Task 3 `test_unlinked_chapter_is_error`)
2. 장 사이 이전/다음 링크가 끊김(마지막 장의 "다음", 지운 장을 가리키는 링크) — 깨진 링크 오류. (Task 3 `test_broken_nav_link_is_error`)
3. 퀴즈 객관식에서 정답을 고른 뒤 다른 보기를 다시 고름 — 채점이 갱신되고 해설이 바뀐다. 페이지를 닫으면 초기화(저장 없음). (Task 1 `test_quiz_js_has_no_storage`, 수동 확인 Step)
4. youtu.be 짧은 링크, `m.youtube.com`, `arxiv.org/pdf/…v2`, 깃허브 하위 경로(`/tree/main/…`) — 같은 원자로 간다. (Task 2 `test_url_variants`)
5. 한 장이 퀴즈 없이 끝남 — `course check`가 잡는다. (Task 3 `test_chapter_without_quiz_is_error`)

---

## 파일 구조

```
skills/design/assets/quiz.js           점검 퀴즈 동작 (Task 1)
skills/design/assets/alto-ext.css      퀴즈 스타일 추가 (Task 1)
lib/astack_cli/inline.py               astack:js 자리에 quiz.js도 붙인다 (Task 1)
lib/astack_cli/route.py                입력 → 스킬 분류 (Task 2)
lib/astack_cli/course.py               코스 폴더 검사 (Task 3)
lib/astack_cli/cli.py                  route · course 하위 명령 (Task 2, 3)
skills/quest/{SKILL.md,assets/map-template.html,assets/chapter-template.html}   (Task 4, 5)
skills/study/SKILL.md                  (Task 6)
skills/map/{SKILL.md,assets/template.html}  (Task 7)
skills/astack/SKILL.md                 입구 (Task 8)
tests/test_route.py, tests/test_course.py (+ test_kit, test_inline, test_templates)
```

---

### Task 1: 점검 퀴즈 컴포넌트

**Files:**
- Create: `skills/design/assets/quiz.js`
- Modify: `skills/design/assets/alto-ext.css`, `lib/astack_cli/inline.py` (`inline_html`)
- Test: `tests/test_kit.py`, `tests/test_inline.py`

**Interfaces:**
- Produces: 마크업 계약 (Task 4·5의 템플릿이 쓴다):

```html
<details class="quiz" data-kind="mc">
  <summary>점검 · [질문 한 줄]</summary>
  <p class="q">[이해형 질문: 왜, 만약, 비교, 적용]</p>
  <ol class="opts">
    <li data-ok="1" data-why="[맞는 이유]">[보기]</li>
    <li data-why="[흔한 오해: 왜 틀렸나] · <a href='#anchor'>원문</a>">[보기]</li>
  </ol>
  <p class="verdict" aria-live="polite"></p>
</details>
<details class="quiz" data-kind="short"><summary>점검 · [질문]</summary><p class="q">[질문]</p><p class="ans">[정답]</p></details>
<details class="quiz" data-kind="essay"><summary>점검 · [질문]</summary><p class="q">[질문]</p><div class="ans"><p>[모범답안]</p><ul><li>[핵심 포인트]</li></ul></div></details>
```

- `inline_html`은 `<!--astack:js-->`를 `<script>{reader.js}\n{quiz.js}</script>`로 바꾼다.

- [ ] **Step 1: Failing tests**

`tests/test_kit.py` (KitTest 안):

```python
    def test_quiz_js_grades_and_has_no_storage(self):
        js = (KIT / "quiz.js").read_text(encoding="utf-8")
        for s in ["details.quiz", "data-ok", "data-why", ".verdict"]:
            self.assertIn(s, js, s)
        for banned in ["localStorage", "sessionStorage", "indexedDB", "fetch("]:
            self.assertNotIn(banned, js, banned)

    def test_ext_css_styles_quiz(self):
        css = (KIT / "alto-ext.css").read_text(encoding="utf-8")
        self.assertIn("details.quiz", css)
```

`tests/test_inline.py` (InlineTest 안):

```python
    def test_js_marker_includes_quiz(self):
        out = inline.inline_html(GOOD.replace("</body>", "<!--astack:js--></body>"), self.dir)
        self.assertIn("details.quiz", out)
```

Run: `python3 -m unittest tests.test_kit tests.test_inline` → Expected: 3 failures.

- [ ] **Step 2: Write `skills/design/assets/quiz.js`**

```js
/* astack 점검 퀴즈. 상태는 페이지 안에서만(닫으면 초기화). 저장소·네트워크를 쓰지 않는다. */
(function(){
  [].slice.call(document.querySelectorAll('details.quiz[data-kind="mc"]')).forEach(function(q){
    var opts=[].slice.call(q.querySelectorAll('.opts li')),out=q.querySelector('.verdict');
    opts.forEach(function(li){
      li.tabIndex=0;li.setAttribute('role','button');
      function pick(){
        opts.forEach(function(o){o.classList.remove('picked','ok','no')});
        var ok=li.hasAttribute('data-ok');
        li.classList.add('picked',ok?'ok':'no');
        if(out){out.innerHTML=(ok?'<b>맞아요.</b> ':'<b>아니에요.</b> ')+(li.getAttribute('data-why')||'')}
      }
      li.addEventListener('click',pick);
      li.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();pick()}});
    });
  });
})();
```

- [ ] **Step 3: Append to `skills/design/assets/alto-ext.css`**

```css
/* 점검 퀴즈 */
details.quiz{margin:18px 0;border:1px solid var(--hairline);border-radius:12px;padding:10px 14px;background:var(--canvas)}
details.quiz>summary{cursor:pointer;font-size:14px;color:var(--ink-2)}
details.quiz[open]>summary{margin-bottom:8px}
details.quiz .q{font-weight:500;margin:0 0 8px}
details.quiz .opts{margin:0;padding-left:22px;display:grid;gap:6px}
details.quiz .opts li{cursor:pointer;border-radius:8px;padding:4px 8px}
details.quiz .opts li:hover,details.quiz .opts li:focus-visible{background:var(--surface)}
details.quiz .opts li.ok{background:#e7f5ec}
details.quiz .opts li.no{background:var(--accent-soft)}
details.quiz .verdict{margin:8px 0 0;font-size:14px}
details.quiz .ans{margin:8px 0 0;padding:8px 12px;background:var(--surface);border-radius:8px}
```

- [ ] **Step 4: `inline.py`** — in `inline_html` replace the js read/replace with:

```python
    js = (kit / "reader.js").read_text(encoding="utf-8")
    quiz = kit / "quiz.js"
    if quiz.exists():
        js += "\n" + quiz.read_text(encoding="utf-8")
```

(the existing `html.replace("<!--astack:js-->", f"<script>{js}</script>")` line stays).

- [ ] **Step 5: Run tests** → `python3 -m unittest discover -s tests` OK

- [ ] **Step 6: 수동 확인** — 임시 파일에 위 마크업 세 개를 넣고 `astack inline` 후 브라우저로 연다. 객관식에서 보기를 바꿔 고르면 판정이 바뀌고, 새로고침하면 초기화되는지 본다.

- [ ] **Step 7: Commit**

```bash
git add skills/design/assets/quiz.js skills/design/assets/alto-ext.css lib/astack_cli/inline.py tests/test_kit.py tests/test_inline.py
git commit -m "feat(kit): in-page retrieval quiz (mc, short, essay) without storage"
```

---

### Task 2: `astack route` — 무엇이든 던지면 어디로 갈지

**Files:**
- Create: `lib/astack_cli/route.py`
- Modify: `lib/astack_cli/cli.py`
- Test: `tests/test_route.py`

**Interfaces:**
- Produces: `route.Route` dataclass `(skill: str, reason: str, needs_judgment: bool)`, `route.route(text: str, cwd: Path | None = None) -> Route`. CLI `astack route "<입력>"` → 한 줄 JSON `{"skill":…, "reason":…, "needs_judgment":…}`.
- 규칙: YouTube는 대담인지 발표인지 링크만으로 알 수 없다 → `skill="interview"`, `needs_judgment=True`, reason에 "슬라이드 발표면 seminar". 입구 스킬(Task 8)이 영상 제목·썸네일로 판단한다.

- [ ] **Step 1: Failing tests** — `tests/test_route.py`

```python
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli, route  # noqa: E402


class RouteTest(unittest.TestCase):
    def s(self, text, cwd=None):
        return route.route(text, cwd).skill

    def test_url_variants(self):
        for u in ["https://www.youtube.com/watch?v=abc", "https://youtu.be/abc", "https://m.youtube.com/watch?v=abc"]:
            r = route.route(u)
            self.assertEqual((r.skill, r.needs_judgment), ("interview", True), u)
        for u in ["https://arxiv.org/abs/2210.03629", "https://arxiv.org/pdf/2210.03629v2", "https://example.com/paper.pdf"]:
            self.assertEqual(self.s(u), "paper", u)
        for u in ["https://github.com/openai/codex", "https://github.com/openai/codex/tree/main/codex-rs"]:
            self.assertEqual(self.s(u), "repo", u)

    def test_spec_markdown_path(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "docs/superpowers/specs/2026-10-05-x.md"
            p.parent.mkdir(parents=True)
            p.write_text("# x")
            self.assertEqual(self.s(str(p)), "spec")
            self.assertEqual(self.s("docs/superpowers/specs/2026-10-05-x.md", Path(d)), "spec")

    def test_local_pdf_is_paper(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "논문.pdf"
            p.write_bytes(b"%PDF-1.4")
            self.assertEqual(self.s(str(p)), "paper")

    def test_dream_phrases(self):
        for t in ["오늘 정리", "오늘 정리해줘", "하루 정리"]:
            self.assertEqual(self.s(t), "dream", t)

    def test_question_is_quest(self):
        r = route.route("Codex CLI 공부하고 싶어")
        self.assertEqual((r.skill, r.needs_judgment), ("quest", False))

    def test_other_url_is_quest_with_judgment(self):
        r = route.route("https://blog.example.com/post")
        self.assertEqual((r.skill, r.needs_judgment), ("quest", True))

    def test_cli_prints_json(self):
        self.assertEqual(cli.main(["route", "https://youtu.be/abc"]), 0)


if __name__ == "__main__":
    unittest.main()
```

Run: `python3 -m unittest tests.test_route` → FAIL (ImportError)

- [ ] **Step 2: Write `lib/astack_cli/route.py`**

```python
"""입구: 던진 입력을 어느 스킬로 보낼지 정한다. 확실한 것만 정하고, 애매하면 needs_judgment."""
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

DREAM = re.compile(r"^(오늘|하루)\s*정리")


@dataclass
class Route:
    skill: str
    reason: str
    needs_judgment: bool = False


def route(text: str, cwd: Path | None = None) -> Route:
    t = text.strip()
    if DREAM.match(t):
        return Route("dream", "하루 정리 요청")
    if re.match(r"^https?://", t):
        u = urlparse(t)
        host = (u.hostname or "").lower().removeprefix("www.").removeprefix("m.")
        if host in ("youtube.com", "youtu.be"):
            return Route("interview", "YouTube 영상. 슬라이드 발표면 seminar", True)
        if host == "arxiv.org" or u.path.lower().endswith(".pdf"):
            return Route("paper", "논문 링크")
        if host == "github.com" and len([p for p in u.path.split("/") if p]) >= 2:
            return Route("repo", "GitHub 레포")
        return Route("quest", "일반 링크. 소스 종류를 읽고 판단", True)
    p = Path(t).expanduser()
    if not p.is_absolute() and cwd is not None:
        p = Path(cwd) / p
    if p.is_file():
        if p.suffix.lower() == ".pdf":
            return Route("paper", "PDF 파일")
        if p.suffix.lower() == ".md" and "specs" in p.parts:
            return Route("spec", "스펙 문서")
    return Route("quest", "질문")
```

- [ ] **Step 3: CLI** — `cli.py`: import `from . import route as _route`, add:

```python
def _cmd_route(args) -> int:
    r = _route.route(args.text, Path.cwd())
    print(json.dumps({"skill": r.skill, "reason": r.reason, "needs_judgment": r.needs_judgment}, ensure_ascii=False))
    return 0
```

```python
    ro = sub.add_parser("route", help="입력(링크, 파일, 질문)을 어느 스킬로 보낼지")
    ro.add_argument("text")
    ro.set_defaults(fn=_cmd_route)
```

- [ ] **Step 4: Run tests** → OK

- [ ] **Step 5: Commit**

```bash
git add lib/astack_cli/route.py lib/astack_cli/cli.py tests/test_route.py
git commit -m "feat(cli): astack route classifies links, files and questions"
```

---

### Task 3: `astack course check` — 코스 구조 검사

**Files:**
- Create: `lib/astack_cli/course.py`
- Modify: `lib/astack_cli/cli.py`
- Test: `tests/test_course.py`

**Interfaces:**
- Consumes: `check.check_html`, `check.Issue` (기존)
- Produces: `course.check_course(folder: Path) -> list[tuple[str, check.Issue]]` (파일 이름, 이슈). CLI `astack course check <folder>` → 줄마다 `<파일>: <level> <code>: <message>`, 오류 있으면 종료 코드 1.
- 규칙:
  - `00-지도.html`이 있어야 한다 (`map` 오류).
  - 장 = `NN-*.html` (NN은 01 이상 두 자리 숫자).
  - 지도가 모든 장으로 링크해야 한다 (`unlinked`).
  - 장마다 `details.quiz`가 하나 이상 (`quiz`).
  - 장마다 지도로 가는 링크(`href="00-지도.html"`) (`nav`).
  - 폴더 안 상대 링크(`href="NN-….html"`)가 가리키는 파일이 있어야 한다 (`nav`, 깨진 링크).
  - 모든 파일에 `check_html`을 돌려 그 결과도 함께 낸다.

- [ ] **Step 1: Failing tests** — `tests/test_course.py`

```python
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from astack_cli import cli, course  # noqa: E402

GOOD = (ROOT / "tests/fixtures/good.html").read_text(encoding="utf-8")
QUIZ = '<details class="quiz" data-kind="short"><summary>점검</summary><p class="q">왜?</p><p class="ans">그래서.</p></details>'


def page(body: str) -> str:
    return GOOD.replace("</body>", body + "</body>")


class CourseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / "00-지도.html").write_text(page('<a href="01-a.html">1</a><a href="02-b.html">2</a>'), encoding="utf-8")
        (self.d / "01-a.html").write_text(page(QUIZ + '<a href="00-지도.html">지도</a><a href="02-b.html">다음</a>'), encoding="utf-8")
        (self.d / "02-b.html").write_text(page(QUIZ + '<a href="00-지도.html">지도</a><a href="01-a.html">이전</a>'), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def codes(self):
        return [i.code for _, i in course.check_course(self.d) if i.level == "error"]

    def test_good_course_has_no_errors(self):
        self.assertEqual(self.codes(), [])

    def test_missing_map_is_error(self):
        (self.d / "00-지도.html").unlink()
        self.assertIn("map", self.codes())

    def test_unlinked_chapter_is_error(self):
        (self.d / "03-c.html").write_text(page(QUIZ + '<a href="00-지도.html">지도</a>'), encoding="utf-8")
        self.assertIn("unlinked", self.codes())

    def test_chapter_without_quiz_is_error(self):
        (self.d / "02-b.html").write_text(page('<a href="00-지도.html">지도</a>'), encoding="utf-8")
        self.assertIn("quiz", self.codes())

    def test_broken_nav_link_is_error(self):
        (self.d / "02-b.html").write_text(page(QUIZ + '<a href="00-지도.html">지도</a><a href="03-gone.html">다음</a>'), encoding="utf-8")
        self.assertIn("nav", self.codes())

    def test_chapter_without_map_link_is_error(self):
        (self.d / "01-a.html").write_text(page(QUIZ + '<a href="02-b.html">다음</a>'), encoding="utf-8")
        self.assertIn("nav", self.codes())

    def test_page_contract_errors_are_included(self):
        bad = re.sub(r'<meta name="description"[^>]*>', "", page(QUIZ + '<a href="00-지도.html">지도</a>'))
        (self.d / "02-b.html").write_text(bad, encoding="utf-8")
        self.assertIn("meta", self.codes())

    def test_cli_exit_codes(self):
        self.assertEqual(cli.main(["course", "check", str(self.d)]), 0)
        (self.d / "00-지도.html").unlink()
        self.assertEqual(cli.main(["course", "check", str(self.d)]), 1)


if __name__ == "__main__":
    unittest.main()
```

Run: `python3 -m unittest tests.test_course` → FAIL

- [ ] **Step 2: Write `lib/astack_cli/course.py`**

```python
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
```

- [ ] **Step 3: CLI** — `cli.py`: `from . import course as _course`, add:

```python
def _cmd_course(args) -> int:
    worst = 0
    for name, i in _course.check_course(Path(args.folder)):
        print(f"{name}: {i.level} {i.code}: {i.message}")
        if i.level == "error":
            worst = 1
    return worst
```

```python
    co = sub.add_parser("course", help="quest 코스 폴더 검사")
    co.add_argument("action", choices=["check"])
    co.add_argument("folder")
    co.set_defaults(fn=_cmd_course)
```

- [ ] **Step 4: Run tests** → OK

- [ ] **Step 5: Commit**

```bash
git add lib/astack_cli/course.py lib/astack_cli/cli.py tests/test_course.py
git commit -m "feat(cli): astack course check validates map, chapters, quizzes and links"
```

---

### Task 4: quest 템플릿 (지도 + 장)

**Files:**
- Create: `skills/quest/assets/map-template.html`, `skills/quest/assets/chapter-template.html`
- Modify: `tests/test_templates.py` (`test_templates_exist` 집합에 `quest`; 아래 테스트 추가)

**Interfaces:**
- Consumes: 키트 마커, 퀴즈 마크업(Task 1), `p.why`, `details.postit`.
- Produces: 두 템플릿. 장 템플릿은 장면 `data-i` ↔ 그림 칸 `data-v`가 맞는다(기존 `test_every_scene_has_a_visual_slot`).

**결정(사용자 확인 필요):** 승인된 quest 템플릿이 없다(C6). 지도는 spec의 Overview + 장 목록, 장은 spec 키트(본문 | 시각화) + 퀴즈로 시작하고 첫 코스로 확정한다.

- [ ] **Step 1: Failing test** — `test_templates.py`: 집합에 `"quest"`, 추가:

```python
    def test_quest_chapter_has_quiz_and_nav(self):
        html = (ROOT / "skills/quest/assets/chapter-template.html").read_text(encoding="utf-8")
        self.assertIn('<details class="quiz" data-kind="mc">', html)
        self.assertIn('href="00-지도.html"', html)
        self.assertIn("그래서 나한테는?", html)
```

Run → FAIL

- [ ] **Step 2: `skills/quest/assets/map-template.html`**

```html
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="description" content="[이 코스가 답하는 질문 한 줄]">
<meta name="rooms:created" content="[RFC3339 지금 시각]">
<meta name="rooms:machine" content="[머신 이름]">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>[주제] 지도</title>
<!--astack:css-->
</head><body data-depth="all">
<div class="top"><div class="top-in"><span class="mark">[주제] <span>quest</span></span><span class="where" id="where"></span><span class="sp"></span></div><div class="prog" id="prog"></div></div>
<div class="wrap">
<header class="cover" data-astack="30s">
  <div class="kick">Quest · [유형: 만들기 / 개념 / 사례 / 실험] · [깊이: Quick / Standard / Deep]</div>
  <h1>[처음 질문 그대로]</h1>
  <div class="meta">quest · [장 수]장 · [전체 읽는 시간]분</div>
  <p class="l30">[이 코스를 다 읽으면 답할 수 있는 것 두 줄]</p>
</header>
<section class="overview" data-astack="3m">
  <div><div class="kick">3분 · 전체 구조</div><p>[장들이 어떻게 이어지는지 두세 줄. 읽는 순서]</p></div>
  <div>[장 관계 그림 SVG: 장 = 노드, 선행 관계 = 화살표]</div>
</section>
<section class="chapters">
  <div class="secHead"><div class="n">장</div><h2>읽는 순서</h2></div>
  <table class="ustab"><thead><tr><th>#</th><th>질문</th><th>30초 요지</th><th>분</th></tr></thead><tbody>
    <tr><td><a href="01-[slug].html">01</a></td><td>[장 질문]</td><td>[30초 요지]</td><td>[10~15]</td></tr>
  </tbody></table>
</section>
<section class="sources">
  <div class="secHead"><div class="n">소스</div><h2>고른 소스와 이유</h2></div>
  <ul><li><a href="[URL]">[소스]</a> — [왜 골랐나: 실사용, 최근 활동, 신뢰하는 사람의 언급]</li></ul>
</section>
<footer data-astack="source">처음 질문 "[요청 원문]" · 소스 [N]개 · Claude Code가 썼습니다</footer>
</div>
<!--astack:js-->
</body></html>
```

- [ ] **Step 3: `skills/quest/assets/chapter-template.html`**

```html
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="description" content="[이 장의 질문과 답 한 줄]">
<meta name="rooms:created" content="[RFC3339 지금 시각]">
<meta name="rooms:machine" content="[머신 이름]">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>[NN] [장 질문]</title>
<!--astack:css-->
</head><body data-depth="all">
<div class="top"><div class="top-in"><span class="mark"><a href="00-지도.html">[주제]</a> <span>[NN]/[MM]</span></span><span class="where" id="where"></span><span class="sp"></span></div><div class="prog" id="prog"></div></div>
<div class="wrap">
<header class="cover" data-astack="30s">
  <div class="kick">[NN] · [장 질문]</div>
  <h1>[답 한 문장]</h1>
  <div class="meta">quest · [읽는 시간]분</div>
  <p class="l30">[왜 이 답인가 두 줄]</p>
</header>
<section class="overview" data-astack="3m">
  <div><div class="kick">3분 · 핵심 구조</div><p>[일반 정의(통용 이름) → 이 사례 → 깊이 순서 요약]</p></div>
  <div>[핵심 그림 SVG]</div>
</section>
<div class="reader"><div class="scenes">
  <section class="scene lvl2" id="s1" data-i="1">
    <h3 class="st"><span class="no">[NN].1</span><span>[소제목]</span></h3>
    <div class="lead"><p>[결론 먼저]</p></div>
    <div class="d2"><p>[설명. 원문 위치 링크]</p><p class="why"><b>왜 이렇게 만들었나.</b> [이유] <span class="ev ev-ok">확인</span> [근거]</p></div>
  </section>
</div><aside class="stage">
  <div class="vis" data-v="1">[이 장면 그림]</div>
</aside></div>
<section class="tome">
  <div class="secHead"><div class="n">끝</div><h2>그래서 나한테는?</h2></div>
  <p>[지금 하는 일에 어떻게 연결되나 한두 줄]</p>
</section>
<details class="quiz" data-kind="mc">
  <summary>점검 · [질문 한 줄]</summary>
  <p class="q">[이해형 질문: 왜, 만약, 비교, 적용]</p>
  <ol class="opts">
    <li data-ok="1" data-why="[맞는 이유]">[보기]</li>
    <li data-why="[흔한 오해: 왜 틀렸나]">[보기]</li>
    <li data-why="[흔한 오해: 왜 틀렸나]">[보기]</li>
  </ol>
  <p class="verdict" aria-live="polite"></p>
</details>
<nav class="chnav"><a href="[이전 장].html">← 이전</a> · <a href="00-지도.html">지도</a> · <a href="[다음 장].html">다음 →</a></nav>
<footer data-astack="source">소스 [URL, 타임스탬프, 파일:줄] · 요청 "[요청 원문]" · Claude Code가 썼습니다</footer>
</div>
<!--astack:js-->
</body></html>
```

Add to `alto-ext.css`:

```css
.chnav{margin:28px 0 8px;font-size:14px;color:var(--ink-2)}
.chnav a{color:var(--ink)}
.tome{margin:32px 0 0}
```

- [ ] **Step 4: Run tests** → OK (`test_inlined_template_passes_contract`가 두 템플릿도 본다)

- [ ] **Step 5: Commit**

```bash
git add skills/quest/assets skills/design/assets/alto-ext.css tests/test_templates.py
git commit -m "feat(templates): quest map and chapter templates with quiz and nav"
```

---

### Task 5: `astack:quest` 스킬

**Files:**
- Create: `skills/quest/SKILL.md`
- Test: `tests/test_manifest.py` 기존 규칙(Use when, 500자)이 검사한다.

**Interfaces:**
- Consumes: 원자 스킬(P2), `astack route`, `astack course check`, 템플릿(Task 4), `astack done`.

- [ ] **Step 1: Write `skills/quest/SKILL.md`**

````markdown
---
name: quest
description: Use when 사용자가 무언가를 공부하거나 알아봐 달라고 맡길 때 — "Codex CLI 공부", "타입 좁히기가 뭐지", "Harvey는 리서치 랩을 어떻게 굴렸나", "브라우저별 속도 비교". 질문 한 줄이나 소스를 받아 나중에 읽을 코스를 만들어 둔다.
---

# astack quest — 만들어 두기

**약속:** 질문 한 줄을 던지면 기다리지 않아도 지도 한 장 + 장들로 된 코스가 생긴다. 지도만 읽어도 전체가 잡히고, 장마다 10~15분이면 한 질문이 풀린다.

먼저 `astack:design`을 읽고 `astack memory search skill:quest`, `astack memory search topic:`으로 기록을 본다.

## 1. 판별
- 소스 하나(링크, 파일)면 `astack route "<입력>"`. 원자가 나오면 그 원자 스킬로 바로 간다(코스 아님).
- 질문이면 유형을 정한다:

| 유형 | 예 | 결과 |
|---|---|---|
| 만들기 | "jev dream 만들고 싶다" | 레포 분해, 하위 질문 × 소스 비교, 스타터 플랜 |
| 개념 | "타입 좁히기가 뭐지" | 교본: 일반 정의(통용 이름) → 사례 → 깊이 |
| 사례 | "Harvey는 리서치 랩을 어떻게 굴렸나" | 케이스 스터디 |
| 실험 | "브라우저별 벤치 속도 비교" | 실험 보고서 + 다시 돌릴 수 있는 벤치 코드 |

- 깊이: 기본 Standard(지도+10~12장, why 장과 실험 또는 실습 장 포함). "빠르게"면 Quick(지도+5장), "깊게"면 Deep(지도+20장 이상).

## 2. 분해하고 바로 알린다
- 하위 질문 3~6개를 정한다. 채팅에 첫 응답 한 번: "받았어요, 이렇게 쪼개서 볼게요: ① ② ③. 방향 바꾸려면 답장 주세요." **답을 기다리지 않는다.** 이 응답이 사용자의 열린 고리를 닫는다.

## 3. 수집과 선별
- GitHub, 엔지니어링 블로그, 발표, 논문, X에서 상위 3~5개. 기준: 실사용, 최근 활동, 신뢰하는 사람의 언급. 스타 수는 참고만.
- 클론은 `~/.cache/astack/repos/`에 한 번만 받아 장끼리 공유한다.

## 4. 장 설계 → 병렬 집필
1. 지도 초안: 장 목록(한 장 = 질문 하나, 10~15분), 장 사이 선행 관계, 읽는 순서.
2. 장마다 서브에이전트 하나(Claude Code: Agent `general-purpose`)를 병렬로 띄운다. 각자 받는 것: 장 질문, 쓸 소스(필요하면 원자 스킬 `astack:repo`/`seminar`/`interview`/`paper`의 방식으로 읽기), `assets/chapter-template.html`, 공통 용어표, 이 SKILL의 장 규칙. 서브에이전트가 없으면 순서대로 쓴다.
3. 모이면: 같은 개념은 같은 이름으로 통일, 겹치는 설명 제거, 이전/다음 링크 연결.
4. 지도 확정(`assets/map-template.html`): 장별 30초 요지, 읽는 순서, 고른 소스와 이유.

## 장 규칙
- 30초(`cover`) · 3분(`overview`) · 본문 · "그래서 나한테는?" · 점검 퀴즈(`details.quiz`, 이해형: 왜, 만약, 비교, 적용. 암기 금지. 오답 해설 = 흔한 오해).
- 개념은 definition-then-case. 부품 3개 이상은 build-up-diagrams. 사실 주장은 evidence-tiers. 모든 주장에 원문 위치.
- 장 제목이 질문 하나로 말해져야 한다. 15분을 넘으면 쪼개고, 너무 짧으면 합친다.

## 실험 유형
1. 가설과 지표(페이지 로드, 스냅샷 시간, 액션 지연, 메모리 등).
2. 기존 벤치를 찾는다. 쓸 만하면 재사용.
3. 없으면 다시 돌릴 수 있는 스크립트를 만든다(build-the-lever). 벤치는 코스 폴더 `bench/`에 남긴다.
4. 환경 고정: 머신, 버전, 워밍업, 교차 실행, 반복 횟수를 기록.
5. 실행(무거우면 밤에). 6. 분석: 숫자를 제한하는 요인, 엉뚱한 걸 잰 건 아닌지(explain-the-number). 7. 보고서 장: 방법, 차트, 원자료, 재현 명령, 한계.
- 브라우저 실험 가드레일: 로그인 사이트는 읽기와 이동만(쓰기·구매·삭제·설정 변경 금지), 실제 프로필의 캐시·쿠키를 지우지 않는다, 실제 프로필 쓰는 작업은 한 번에 하나, 반복 측정은 로컬 테스트 페이지로. 비교는 "실사용 조건"과 "깨끗한 조건"을 함께 잰다.

## 5. 적재와 알림
1. 폴더: `docs/astack/quest/<날짜>-<slug>/` (`00-지도.html`, `01-….html` …).
2. 파일마다 메타 → `astack inline`.
3. `astack course check <폴더>` 에러 0.
4. 지도와 장마다 `astack done <f> --skill quest`.
5. 시작한 곳으로 알린다: 지도 경로 + 30초 두 줄.

## 완료 전 체크
- [ ] 지도에서 모든 장에 갈 수 있다(`course check`)
- [ ] 장마다 퀴즈와 "그래서 나한테는?"
- [ ] Standard면 why 장과 실험 또는 실습 장이 있다
- [ ] 같은 개념이 장마다 같은 이름
- [ ] 사용자가 선호·제외·교정을 말했으면 `astack memory add`

## Gotchas
- 장 서브에이전트가 각자 클론하면 느리고 디스크를 먹는다. 클론은 먼저 한 번.
- 장끼리 용어가 갈리는 게 가장 흔한 실패다. 공통 용어표를 집필 전에 만들어 함께 넘긴다.
- **템플릿은 잠정이다.** 첫 코스를 사용자에게 보여 확정한다(C6).
````

- [ ] **Step 2: Run tests** → `python3 -m unittest tests.test_manifest` OK

- [ ] **Step 3: Commit**

```bash
git add skills/quest/SKILL.md
git commit -m "feat(skills): quest builds a course (map + chapters) without waiting"
```

---

### Task 6: `astack:study` 스킬

**Files:**
- Create: `skills/study/SKILL.md`

- [ ] **Step 1: Write `skills/study/SKILL.md`**

````markdown
---
name: study
description: Use when 사용자가 집중 공부 시간에 이미 있는 이해물(코스의 장, 매거진, 리더) 하나를 펴 놓고 후속 질문을 하거나 더 파 달라고 할 때. "이 장에서 X가 왜 그래?", "이거 더 깊게", "study".
---

# astack study — 깊게 이해하기

**약속:** 묻는 것마다 답이 그 이해물에 남는다. 다음에 열면 내가 물었던 것과 답이 같은 자리에 있다(공리 1: 모든 답은 HTML로).

먼저 `astack:design`을 읽는다. 동기 작업이다. 사용자가 요청한 시간에만.

## 입력과 출력
- 입력: 이해물 하나(경로 또는 `astack recall --query`로 찾기) + 후속 질문.
- 출력: 같은 파일에 섹션을 덧붙인다. 답이 길거나 새 개념이면 하위 교본을 같은 방(같은 폴더)에 만들고 원래 파일에서 링크한다.

## 워크플로
1. 이해물을 읽고, 질문이 어느 장면에 붙는지 정한다.
2. 답한다: 결론 먼저, 근거 등급(확인 / 추론 / 모름), 원문 위치.
3. 덧붙이기: 원래 파일의 해당 장면 아래 또는 끝의 `<section class="study">`에
   ```html
   <section class="study" id="q-[날짜]-[n]">
     <h3 class="st"><span class="no">질문</span><span>[사용자 질문 그대로]</span></h3>
     <div class="lead"><p>[답 한 줄]</p></div>
     <div class="d2"><p>[설명]</p></div>
     <details class="quiz" data-kind="short"><summary>점검 · [질문]</summary><p class="q">[질문]</p><p class="ans">[정답]</p></details>
   </section>
   ```
4. 하위 교본이 필요하면 `astack:quest`의 장 템플릿으로 한 장을 만들고 원래 파일에서 링크.
5. `astack inline <f>` → `astack check <f>` → `astack done <f> --skill study`.

## 완료 전 체크
- [ ] 원래 내용을 지우거나 바꾸지 않았다(덧붙이기만)
- [ ] 답마다 근거 등급과 원문 위치
- [ ] `astack check` 에러 0

## Gotchas
- 원본이 이미 inline된 파일이면 키트 CSS가 안에 들어 있다. 덧붙일 때 `<!--astack:css-->`를 다시 넣지 않는다.
````

- [ ] **Step 2: Run tests** → OK

- [ ] **Step 3: Commit**

```bash
git add skills/study/SKILL.md
git commit -m "feat(skills): study appends follow-up answers to the same document"
```

---

### Task 7: `astack:map` 스킬과 템플릿

**Files:**
- Create: `skills/map/SKILL.md`, `skills/map/assets/template.html`
- Modify: `tests/test_templates.py` (집합에 `map`)

- [ ] **Step 1: Failing test** — 집합에 `"map"`, 추가:

```python
    def test_map_template_has_converge_sections(self):
        html = (ROOT / "skills/map/assets/template.html").read_text(encoding="utf-8")
        for s in ('id="known"', 'id="agree"', 'id="conflict"', 'id="open"', 'id="decided"'):
            self.assertIn(s, html)
```

Run → FAIL

- [ ] **Step 2: `skills/map/assets/template.html`**

```html
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="description" content="[방 이름]: 지금까지 알게 된 것 한 줄">
<meta name="rooms:created" content="[RFC3339 처음 만든 시각 — 갱신해도 바꾸지 않는다]">
<meta name="rooms:machine" content="[머신 이름]">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>[방 이름] 지도</title>
<!--astack:css-->
</head><body data-depth="all">
<div class="top"><div class="top-in"><span class="mark">[방 이름] <span>map</span></span><span class="where" id="where"></span><span class="sp"></span></div><div class="prog" id="prog"></div></div>
<div class="wrap">
<header class="cover" data-astack="30s">
  <div class="kick">Map · [방 이름] · 이해물 [N]개에서</div>
  <h1>[이 주제에 대해 지금 말할 수 있는 것 한 문장]</h1>
  <div class="meta">map · [마지막 갱신 날짜] · [읽는 시간]분</div>
  <p class="l30">[가장 최근에 바뀐 것 두 줄]</p>
</header>
<section class="overview" data-astack="3m">
  <div><div class="kick">3분 · 구조</div><p>[개념들의 관계 두세 줄]</p></div>
  <div>[개념 지도 SVG]</div>
</section>
<section id="known"><div class="secHead"><div class="n">1</div><h2>알게 된 것</h2></div>
  <ul><li>[사실] <span class="ev ev-ok">확인</span> <a href="[이해물 경로]">[출처]</a></li></ul></section>
<section id="agree"><div class="secHead"><div class="n">2</div><h2>소스들이 합의하는 것</h2></div>
  <ul><li>[합의] — <a href="[a]">[a]</a>, <a href="[b]">[b]</a></li></ul></section>
<section id="conflict"><div class="secHead"><div class="n">3</div><h2>부딪히는 주장</h2></div>
  <table class="ustab"><thead><tr><th>주장 A</th><th>주장 B</th><th>왜 다른가</th></tr></thead><tbody><tr><td>[A + 출처]</td><td>[B + 출처]</td><td>[조건·시점·정의 차이]</td></tr></tbody></table></section>
<section id="open"><div class="secHead"><div class="n">4</div><h2>남은 질문</h2></div>
  <ul><li>[질문] — quest 후보</li></ul></section>
<section id="decided"><div class="secHead"><div class="n">5</div><h2>내가 내린 결정</h2></div>
  <ul><li>[결정] ([날짜], [근거])</li></ul></section>
<section id="changes"><div class="secHead"><div class="n">기록</div><h2>바뀐 것</h2></div>
  <ul><li>[날짜]: [무엇이 바뀌었나, 어떤 이해물이 들어와서]</li></ul></section>
<footer data-astack="source">이해물 [N]개 · 방 [경로] · Claude Code가 썼습니다</footer>
</div>
<!--astack:js-->
</body></html>
```

- [ ] **Step 3: `skills/map/SKILL.md`**

````markdown
---
name: map
description: Use when 한 주제(방)에 이해물이 여러 개 쌓였고 사용자가 그걸 한 장으로 엮어 달라고 할 때, 또는 dream이 하루 정리에서 새 이해물이 들어온 방의 지도를 갱신할 때. "이 방 지도 만들어줘", "지금까지 알게 된 거 한 장으로".
---

# astack map — 주제 지도

**약속:** 그 방의 이해물 20개 대신 지도 한 장을 읽는다. 이해물이 늘어도 지도는 두꺼워지지 않고 더 정확해진다(converge).

먼저 `astack:design`을 읽는다.

## 입력과 출력
- 입력: 방(폴더) 경로, 또는 주제어(`astack recall --query "<주제어>" --limit 50 --json`).
- 출력: 그 방의 `map.html` 한 장. 이미 있으면 **갱신**한다(새로 쓰지 않는다). quest 코스면 `00-지도.html`이 첫 판.

## 갱신 규칙 (converge)
1. 새 이해물에서 사실·주장·질문·결정을 뽑는다.
2. 이미 있는 줄과 같은 내용이면 출처만 더한다(줄을 늘리지 않는다).
3. 기존 줄과 부딪히면 "부딪히는 주장"으로 옮기고 왜 다른지(조건, 시점, 정의) 적는다.
4. 답이 나온 "남은 질문"은 지우고 "알게 된 것"으로 올린다.
5. 오래되어 틀린 것은 지우고 "바뀐 것"에 한 줄.
6. 전체 길이가 지난번보다 크게 늘었으면 합칠 곳을 찾는다. 목표는 읽는 시간 10분 이내.

## 워크플로
1. 방의 이해물 목록을 모은다(recall 또는 폴더).
2. 기존 `map.html`이 있으면 읽는다. 없으면 `assets/template.html`.
3. 갱신 규칙대로 고친다. `rooms:created`는 처음 값을 유지한다.
4. `astack inline` → `astack check` → `astack done <f> --skill map`.

## 완료 전 체크
- [ ] 모든 줄에 출처 링크
- [ ] 부딪히는 주장마다 "왜 다른가"
- [ ] 읽는 시간 10분 이내

## Gotchas
- 지도에 요약을 쌓으면 금방 두꺼워진다. 줄을 더하기 전에 합칠 줄을 먼저 찾는다.
````

- [ ] **Step 4: Run tests** → OK

- [ ] **Step 5: Commit**

```bash
git add skills/map tests/test_templates.py
git commit -m "feat(skills): map converges a room into one page"
```

---

### Task 8: `astack` 입구 스킬, README, 원칙 색인

**Files:**
- Create: `skills/astack/SKILL.md`
- Modify: `README.md`, `skills/design/SKILL.md` (원칙 색인), `skills/design/references/capabilities.md` (route, course 행)

- [ ] **Step 1: `skills/astack/SKILL.md`**

````markdown
---
name: astack
description: Use when 사용자가 무엇을 원하는지 스킬 이름 없이 던질 때 — 링크 하나, 파일 하나, 질문 한 줄, "오늘 정리" — 그리고 어느 astack 스킬로 처리할지 정해야 할 때. "astack <무엇이든>", "이거 처리해줘"와 함께 링크·질문만 줄 때.
---

# astack — 입구

**약속:** 무엇을 던져도 알맞은 스킬이 받는다. 사용자는 스킬 이름을 몰라도 된다.

## 워크플로
1. `astack route "<입력>"` → `{"skill", "reason", "needs_judgment"}`.
2. `needs_judgment`가 false면 그 스킬을 바로 부른다(`astack:<skill>`).
3. true면 판단한다:
   - YouTube: 제목·설명·썸네일을 본다(`astack transcript <url> --json`의 title). 슬라이드 발표·강연·컨퍼런스 talk면 `seminar`, 대담·팟캐스트·인터뷰면 `interview`.
   - 일반 링크: 글 하나면 `quest`(사례 또는 개념 유형, Quick), 레포·논문이 본문이면 해당 원자.
4. 고른 스킬과 이유를 채팅에 한 줄로 알리고 진행한다. 확인을 기다리지 않는다.

## 라우팅 표
| 입력 | 스킬 |
|---|---|
| YouTube 대담·팟캐스트 | interview |
| YouTube 슬라이드 발표 | seminar |
| arXiv, PDF | paper |
| GitHub 레포 | repo |
| `docs/**/specs/*.md` | spec |
| "오늘 정리", "하루 정리" | dream |
| 질문, 공부하고 싶은 것 | quest |
| "지난주 거", "X 관련 뭐 쌓였지" | recall |
````

- [ ] **Step 2: README** — English, very short. Add rows to `## Skills`:

```markdown
| `astack` | Anything: a link, a file, a question | Sends it to the right skill |
| `quest` | A question | A course: a map and chapters with quizzes |
| `study` | One page and a follow-up question | The answer, added to that page |
| `map` | A topic folder | One page that sums up the topic |
```

CLI line adds `route | course`.

- [ ] **Step 3: 원칙 색인** — `skills/design/SKILL.md` 표 끝에:

```markdown
| definition-then-case | 개념 설명 | 일반 정의(통용 이름) → 지금 사례 → 깊이 |
| retrieval-check | 장 끝 | 이해를 묻는 질문. 암기 금지. 오답 = 오해 진단 |
| converge | map, dream | 쌓여도 두꺼워지지 않고 정확해진다 |
| explain-the-number | 실험 | 숫자를 제한하는 요인, 엉뚱한 걸 잰 건 아닌지 |
| build-the-lever | 실험 | 손으로 재지 말고 다시 돌릴 벤치를 만든다 |
```

- [ ] **Step 4: capabilities.md** — 표 끝에:

```markdown
| route | `astack route "<입력>"` | 같음 | YouTube는 needs_judgment |
| course-check | `astack course check <폴더>` | 같음 | 지도·장·퀴즈·링크 |
```

- [ ] **Step 5: Run tests and commit**

```bash
python3 -m unittest discover -s tests
git add skills/astack skills/design README.md
git commit -m "feat(skills): astack entry router; docs for P3"
```

---

### Task 9: 실제 실행 (§15 P3 완료 기준)

이 Task는 코드가 아니라 실제 사용이다. 결과물은 git에서 제외(`docs/astack/quest/`를 `.gitignore`에 추가).

- [ ] **Step 1:** `.gitignore`에 `docs/astack/quest/` 추가, 커밋.
- [ ] **Step 2:** `astack:quest`로 "Codex CLI 공부" 코스를 만든다. 깊이는 Standard(지도 + 10~12장). `astack course check` 에러 0.
- [ ] **Step 3:** 실험 1건: "브라우저 자동화 도구별 페이지 로드 속도 비교(축소판)" — 로컬 테스트 페이지, 깨끗한 프로필만, 반복 3회. 보고서 장 + `bench/` 재현 코드.
- [ ] **Step 4:** `docs/superpowers/plans/2026-10-05-astack-p3-dogfood.md`에 걸린 시간, 장 수, course check 결과, 실패한 점을 적고 커밋.
