# astack P5 호스트 (setup · 레시피 · 밤 goal · 남은 기능) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** astack을 한 명령으로 설치하는 `./setup`, 호스트 레시피(Codex, Hermes, Aside), 밤 goal 실행기 `astack goal`, 그리고 P2~P4에서 미룬 기능(기억 정리 HTML 보고서, paper 무손실 검사, 모바일 그림, 작은 수정)을 만들고, 이 맥에 설치까지 끝낸다.

**Architecture:** 설치 로직은 `lib/astack_cli/setup.py`(테스트 가능)에 두고, 레포 맨 위 `setup`은 그걸 부르는 얇은 실행 파일이다. 호스트마다 하는 일은 링크·복사·스니펫 추가뿐이고, 모두 되돌릴 수 있다(`--uninstall`). 밤 goal은 `astack goal`이 큐와 상태 파일만 다루고, 실제 일은 호스트 CLI(`claude -p` 또는 `codex exec`)가 astack 스킬로 한다. Hermes는 이 맥에 없으므로 레시피 파일만 만들고 표시한다.

**Tech Stack:** Python 3 표준 라이브러리 + unittest. 외부 명령은 주입 가능한 runner로만 부른다.

**Spec:** `docs/superpowers/specs/2026-10-05-astack-v1-handoff.md` (§9.4 스케줄, §9.5 밤 goal, §9.6 예산, §11.2 호스트, §13 레포 구조, §15 P5, §20)

## Global Constraints

- P2~P4 계획의 Global Constraints를 따른다 (stdlib, `bin/astack` 하나, README 영어·짧게, 레포에 개인 데이터 없음).
- 설치는 되돌릴 수 있어야 한다. 사용자 파일을 덮어쓰지 않는다. 스니펫은 표식(`<!-- astack:begin -->` … `<!-- astack:end -->`) 사이에만 쓰고, 다시 실행해도 한 번만 들어간다 (idempotent).
- Aside는 평평한 스킬 폴더라 `~/.aside/u/0/skills/user/astack-<이름>`으로 **복사**한다(심볼릭 링크 아님). 계정 스킬은 머신 간 동기화되지 않으므로 setup이 매번 복사한다 (§11.2).
- 밤 goal은 최대 3개. 결정 기록과 체크포인트를 남기고, 끊기면 이어서 한다. 아침에 goal별 성공 여부·핵심 3줄·지도 링크 (§9.5).
- 무거운 자동 작업은 밤에만, 개수로 상한 (§9.6).
- Hermes 레시피는 이 맥에서 검증할 수 없다. 파일 머리에 "맥미니에서 검증 전"이라고 적는다.

## Review Focus

1. setup을 두 번 실행 — 스니펫이 두 번 들어가거나 링크가 중복되면 안 된다. (Task 1 `test_install_is_idempotent`)
2. 사용자가 이미 같은 이름의 스킬 폴더를 가진 경우(`~/.codex/skills/astack-spec`이 일반 폴더) — 덮어쓰지 않고 건너뛰며 알린다. (Task 1 `test_existing_user_dir_is_not_overwritten`)
3. `--uninstall`은 setup이 만든 것만 지운다 — 사용자 스킬과 스니펫 밖 내용은 남는다. (Task 1 `test_uninstall_removes_only_ours`)
4. 밤 goal 실행 도중 프로세스가 죽음 — 다음 `goal run`이 그 goal을 이어서 하고, 4번째 goal은 시작하지 않는다. (Task 3 `test_dead_running_goal_resumes`, `test_max_three_per_night`)
5. goal 결과 파일이 없거나 깨짐 — 실패로 기록되고 아침 보고에 이유가 나온다. (Task 3 `test_missing_result_is_failure`)

---

### Task 1: `./setup` — 호스트별 설치와 되돌리기

**Files:**
- Create: `lib/astack_cli/setup.py`, `setup` (레포 맨 위, 실행 파일)
- Modify: `lib/astack_cli/cli.py` (하위 명령 `setup`도 같은 함수를 부르게)
- Test: `tests/test_setup.py`

**Interfaces:**
- `setup.Env` dataclass: `home: Path`, `repo: Path` (테스트가 가짜 home을 넘긴다)
- `setup.install(hosts: list[str], env: Env, dry_run: bool = False) -> list[str]` — 한 일을 한 줄씩 돌려준다
- `setup.uninstall(hosts: list[str], env: Env, dry_run: bool = False) -> list[str]`
- `setup.detect(env: Env) -> list[str]` — `auto`일 때: 언제나 `cli`, `claude`; `~/.codex` 있으면 `codex`; `~/.aside/u/0/skills/user` 있으면 `aside`; `~/.hermes` 있고 `hermes` 명령이 있으면 `hermes`
- 호스트별 동작:
  - `cli`: `~/.local/bin/astack` → `<repo>/bin/astack` 심볼릭 링크. `~/.astack/roots`가 없으면 `<home>/personal` 한 줄.
  - `claude`: `~/.claude/CLAUDE.md`에 `recipes/claude/CLAUDE.md.snippet`을 표식 사이로 넣는다(없으면 파일 생성). 플러그인 설치는 Claude Code 프롬프트에서만 되므로, 할 일 줄에 `/plugin marketplace add <repo>`와 `/plugin install astack@astack-dev`를 "직접 실행" 표시로 돌려준다.
  - `codex`: `skills/<이름>`마다 `~/.codex/skills/astack-<이름>` → 레포 폴더 심볼릭 링크. `~/.codex/AGENTS.md`에 `recipes/codex/AGENTS.md.snippet`을 표식 사이로.
  - `aside`: `skills/<이름>`마다 `~/.aside/u/0/skills/user/astack-<이름>`으로 **복사**(이미 있고 우리 표식 파일 `.astack-managed`가 있으면 지우고 다시 복사, 표식 없으면 건너뜀). 복사본마다 `.astack-managed` 파일을 둔다.
  - `hermes`: 이 맥에서는 할 일 줄만 돌려준다(`recipes/hermes/README.md` 참고).
- 이미 존재하는 대상: 우리 링크(같은 대상)면 그대로, 다른 링크·일반 폴더면 건너뛰고 "건너뜀: <경로> (사용자 것)".
- CLI: `./setup [--host claude|codex|aside|hermes|cli|auto ...] [--dry-run] [--uninstall]` (기본 `auto`). 한 일을 줄마다 출력, 실패 0이면 종료 코드 0.

- [ ] **Step 1: Failing tests** — `tests/test_setup.py`

```python
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from astack_cli import setup  # noqa: E402

BEGIN, END = "<!-- astack:begin -->", "<!-- astack:end -->"


class SetupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        (self.home / ".codex/skills").mkdir(parents=True)
        (self.home / ".aside/u/0/skills/user").mkdir(parents=True)
        self.env = setup.Env(home=self.home, repo=ROOT)

    def tearDown(self):
        self.tmp.cleanup()

    def skills(self):
        return sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))

    def test_detect_finds_hosts(self):
        self.assertEqual(setup.detect(self.env)[:2], ["cli", "claude"])
        self.assertIn("codex", setup.detect(self.env))
        self.assertIn("aside", setup.detect(self.env))

    def test_cli_links_binary_and_roots(self):
        setup.install(["cli"], self.env)
        link = self.home / ".local/bin/astack"
        self.assertEqual(link.resolve(), (ROOT / "bin/astack").resolve())
        self.assertEqual((self.home / ".astack/roots").read_text().strip(), str(self.home / "personal"))

    def test_claude_snippet_once_and_plugin_todo(self):
        md = self.home / ".claude/CLAUDE.md"
        md.parent.mkdir(parents=True)
        md.write_text("# mine\n")
        out = setup.install(["claude"], self.env)
        out2 = setup.install(["claude"], self.env)
        text = md.read_text()
        self.assertTrue(text.startswith("# mine\n"))
        self.assertEqual(text.count(BEGIN), 1)
        self.assertTrue(any("/plugin install astack@astack-dev" in l for l in out + out2))

    def test_codex_links_every_skill(self):
        setup.install(["codex"], self.env)
        for name in self.skills():
            p = self.home / f".codex/skills/astack-{name}"
            self.assertTrue(p.is_symlink(), name)
            self.assertEqual(p.resolve(), (ROOT / "skills" / name).resolve())
        self.assertEqual((self.home / ".codex/AGENTS.md").read_text().count(BEGIN), 1)

    def test_aside_copies_with_marker(self):
        setup.install(["aside"], self.env)
        d = self.home / ".aside/u/0/skills/user/astack-spec"
        self.assertTrue(d.is_dir() and not d.is_symlink())
        self.assertTrue((d / "SKILL.md").is_file())
        self.assertTrue((d / ".astack-managed").is_file())

    def test_install_is_idempotent(self):
        setup.install(["cli", "claude", "codex", "aside"], self.env)
        setup.install(["cli", "claude", "codex", "aside"], self.env)
        self.assertEqual((self.home / ".claude/CLAUDE.md").read_text().count(BEGIN), 1)
        self.assertEqual(len(list((self.home / ".codex/skills").glob("astack-*"))), len(self.skills()))

    def test_existing_user_dir_is_not_overwritten(self):
        mine = self.home / ".codex/skills/astack-spec"
        mine.mkdir()
        (mine / "SKILL.md").write_text("mine")
        out = setup.install(["codex"], self.env)
        self.assertEqual((mine / "SKILL.md").read_text(), "mine")
        self.assertTrue(any("건너뜀" in l and "astack-spec" in l for l in out))
        aside_mine = self.home / ".aside/u/0/skills/user/astack-spec"
        aside_mine.mkdir()
        (aside_mine / "SKILL.md").write_text("mine")
        setup.install(["aside"], self.env)
        self.assertEqual((aside_mine / "SKILL.md").read_text(), "mine")

    def test_uninstall_removes_only_ours(self):
        md = self.home / ".claude/CLAUDE.md"
        md.parent.mkdir(parents=True)
        md.write_text("# mine\n")
        (self.home / ".codex/skills/other").mkdir()
        setup.install(["cli", "claude", "codex", "aside"], self.env)
        setup.uninstall(["cli", "claude", "codex", "aside"], self.env)
        self.assertEqual(md.read_text(), "# mine\n")
        self.assertTrue((self.home / ".codex/skills/other").is_dir())
        self.assertEqual(list((self.home / ".codex/skills").glob("astack-*")), [])
        self.assertEqual(list((self.home / ".aside/u/0/skills/user").glob("astack-*")), [])
        self.assertFalse((self.home / ".local/bin/astack").exists())

    def test_dry_run_changes_nothing(self):
        out = setup.install(["cli", "claude", "codex", "aside"], self.env, dry_run=True)
        self.assertTrue(out)
        self.assertFalse((self.home / ".local/bin/astack").exists())
        self.assertEqual(list((self.home / ".codex/skills").glob("astack-*")), [])

    def test_setup_script_runs(self):
        import subprocess
        r = subprocess.run([str(ROOT / "setup"), "--host", "codex", "--dry-run"], capture_output=True, text=True,
                           env={**os.environ, "ASTACK_SETUP_HOME": str(self.home)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("astack-spec", r.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run** → FAIL (ImportError)

- [ ] **Step 3: `lib/astack_cli/setup.py`**

```python
"""호스트별 설치와 되돌리기. 링크·복사·스니펫만 한다. 사용자 것은 건드리지 않는다."""
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

BEGIN, END = "<!-- astack:begin -->", "<!-- astack:end -->"
MARK = ".astack-managed"
HOSTS = ["cli", "claude", "codex", "aside", "hermes"]


@dataclass
class Env:
    home: Path
    repo: Path


def default_env() -> Env:
    home = Path(os.environ.get("ASTACK_SETUP_HOME") or Path.home())
    return Env(home=home, repo=Path(__file__).resolve().parents[2])


def detect(env: Env) -> list[str]:
    hosts = ["cli", "claude"]
    if (env.home / ".codex").is_dir():
        hosts.append("codex")
    if (env.home / ".aside/u/0/skills/user").is_dir():
        hosts.append("aside")
    if (env.home / ".hermes").is_dir() and shutil.which("hermes"):
        hosts.append("hermes")
    return hosts


def _skills(env: Env) -> list[Path]:
    return sorted(p.parent for p in (env.repo / "skills").glob("*/SKILL.md"))


def _link(target: Path, link: Path, dry: bool, out: list[str]) -> None:
    if link.is_symlink() and link.resolve() == target.resolve():
        out.append(f"그대로: {link}")
        return
    if link.exists() or link.is_symlink():
        out.append(f"건너뜀: {link} (사용자 것)")
        return
    out.append(f"링크: {link} → {target}")
    if not dry:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target)


def _unlink(target: Path, link: Path, dry: bool, out: list[str]) -> None:
    if link.is_symlink() and link.resolve() == target.resolve():
        out.append(f"지움: {link}")
        if not dry:
            link.unlink()


def _put_snippet(file: Path, snippet: str, dry: bool, out: list[str]) -> None:
    text = file.read_text(encoding="utf-8") if file.exists() else ""
    block = f"{BEGIN}\n{snippet.strip()}\n{END}\n"
    if BEGIN in text and END in text:
        a, rest = text.split(BEGIN, 1)
        _, b = rest.split(END, 1)
        new = a + block + b.lstrip("\n")
    else:
        new = text + ("\n" if text and not text.endswith("\n") else "") + ("\n" if text else "") + block
    if new == text:
        out.append(f"그대로: {file}")
        return
    out.append(f"스니펫: {file}")
    if not dry:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(new, encoding="utf-8")


def _drop_snippet(file: Path, dry: bool, out: list[str]) -> None:
    if not file.exists():
        return
    text = file.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        return
    a, rest = text.split(BEGIN, 1)
    _, b = rest.split(END, 1)
    new = (a.rstrip("\n") + "\n" if a.strip() else "") + b.lstrip("\n")
    out.append(f"스니펫 지움: {file}")
    if not dry:
        file.write_text(new, encoding="utf-8")


def install(hosts: list[str], env: Env, dry_run: bool = False) -> list[str]:
    out: list[str] = []
    for h in hosts:
        if h == "cli":
            _link(env.repo / "bin/astack", env.home / ".local/bin/astack", dry_run, out)
            roots = env.home / ".astack/roots"
            if not roots.exists():
                out.append(f"roots: {roots}")
                if not dry_run:
                    roots.parent.mkdir(parents=True, exist_ok=True)
                    roots.write_text(f"{env.home / 'personal'}\n", encoding="utf-8")
        elif h == "claude":
            _put_snippet(env.home / ".claude/CLAUDE.md",
                         (env.repo / "recipes/claude/CLAUDE.md.snippet").read_text(encoding="utf-8"), dry_run, out)
            out.append(f"직접 실행 (Claude Code 프롬프트): /plugin marketplace add {env.repo}")
            out.append("직접 실행 (Claude Code 프롬프트): /plugin install astack@astack-dev")
        elif h == "codex":
            for s in _skills(env):
                _link(s, env.home / f".codex/skills/astack-{s.name}", dry_run, out)
            _put_snippet(env.home / ".codex/AGENTS.md",
                         (env.repo / "recipes/codex/AGENTS.md.snippet").read_text(encoding="utf-8"), dry_run, out)
        elif h == "aside":
            base = env.home / ".aside/u/0/skills/user"
            for s in _skills(env):
                dst = base / f"astack-{s.name}"
                if dst.exists() and not (dst / MARK).exists():
                    out.append(f"건너뜀: {dst} (사용자 것)")
                    continue
                out.append(f"복사: {dst}")
                if not dry_run:
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(s, dst)
                    (dst / MARK).write_text("astack setup이 만든 복사본\n", encoding="utf-8")
        elif h == "hermes":
            out.append(f"직접 실행 (맥미니): {env.repo / 'recipes/hermes/README.md'}의 순서대로")
        else:
            raise ValueError(f"모르는 호스트: {h} (가능: {', '.join(HOSTS)}, auto)")
    return out


def uninstall(hosts: list[str], env: Env, dry_run: bool = False) -> list[str]:
    out: list[str] = []
    for h in hosts:
        if h == "cli":
            _unlink(env.repo / "bin/astack", env.home / ".local/bin/astack", dry_run, out)
        elif h == "claude":
            _drop_snippet(env.home / ".claude/CLAUDE.md", dry_run, out)
            out.append("직접 실행 (Claude Code 프롬프트): /plugin uninstall astack@astack-dev")
        elif h == "codex":
            for s in _skills(env):
                _unlink(s, env.home / f".codex/skills/astack-{s.name}", dry_run, out)
            _drop_snippet(env.home / ".codex/AGENTS.md", dry_run, out)
        elif h == "aside":
            for d in sorted((env.home / ".aside/u/0/skills/user").glob("astack-*")):
                if (d / MARK).exists():
                    out.append(f"지움: {d}")
                    if not dry_run:
                        shutil.rmtree(d)
        elif h == "hermes":
            out.append("직접 실행 (맥미니): recipes/hermes/README.md의 되돌리기 순서")
    return out


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(prog="setup", description="astack 설치 (호스트별)")
    p.add_argument("--host", nargs="+", default=["auto"])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--uninstall", action="store_true")
    a = p.parse_args(argv)
    env = default_env()
    hosts = detect(env) if a.host == ["auto"] else a.host
    try:
        lines = (uninstall if a.uninstall else install)(hosts, env, a.dry_run)
    except (ValueError, OSError) as e:
        print(f"setup: {e}", file=__import__("sys").stderr)
        return 2
    for l in lines:
        print(("(dry-run) " if a.dry_run else "") + l)
    return 0
```

- [ ] **Step 4: `setup`** (레포 맨 위, `chmod +x`)

```python
#!/usr/bin/env python3
"""astack 설치: ./setup --host auto | claude codex aside cli hermes [--dry-run] [--uninstall]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from astack_cli.setup import main  # noqa: E402

sys.exit(main())
```

`cli.py`: add a `setup` subparser that forwards remaining args: `s = sub.add_parser("setup", help="호스트별 설치 (./setup과 같다)"); s.add_argument("rest", nargs=argparse.REMAINDER); s.set_defaults(fn=lambda a: __import__("astack_cli.setup", fromlist=["main"]).main(a.rest))` — or the equivalent with a named handler `_cmd_setup`.

- [ ] **Step 5:** `recipes/codex/AGENTS.md.snippet` (Task 2 writes it; for this task create a minimal placeholder line `## astack` so tests pass, Task 2 fills it).

- [ ] **Step 6: Run tests → OK; commit** `feat(setup): one-command install per host with dry-run and uninstall`

---

### Task 2: 호스트 레시피 (Codex, Hermes, Aside)

**Files:**
- Create/replace: `recipes/codex/AGENTS.md.snippet`, `recipes/hermes/README.md`, `recipes/hermes/cron.yaml`, `recipes/hermes/telegram-topics.yaml`, `recipes/aside/permissions.md`
- Test: `tests/test_recipes.py`

- [ ] **Step 1: `recipes/codex/AGENTS.md.snippet`** — Codex용 흐름 속 자동 조건(§9.2와 같은 뜻, Codex 표현):

```markdown
## astack
- 스펙·설계 문서를 저장하면 astack-spec 스킬로 이해물을 만든다.
- 여러 단계 구현이 끝나거나 PR을 열면 astack-change 스킬로 변경 요약을 만든다.
- 5분 넘게 걸릴 작업을 시작할 때 `astack recall --now --query "<핵심 단어>" --json`으로 지금 읽을 것 하나를 알려준다.
- 스킬 이름은 `astack-<이름>`이다. 공통 규칙은 astack-design.
```

- [ ] **Step 2: `recipes/hermes/cron.yaml`** — §9.4 스케줄. 머리 주석: `# 맥미니에서 검증 전. Hermes cron 형식: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron`

```yaml
# 맥미니에서 검증 전 (2026-10-06). 작업 위치: ~/personal/notes
jobs:
  - name: astack-feed
    schedule: "0 5 * * *"
    prompt: "astack:feed 스킬로 오늘 30분을 만들어. 끝나면 30초 층 두 줄과 경로만 남겨."
  - name: astack-morning
    schedule: "0 7 * * *"
    script: "astack goal report --date yesterday --text"   # stdout이 비면 보내지 않음
  - name: astack-dream
    schedule: "0 20 * * *"
    prompt: "astack:dream 스킬로 오늘 Journal을 만들어. 일요일이면 주간 수렴까지. 30초 층 두 줄과 경로만 남겨."
  - name: astack-consolidate
    schedule: "30 20 * * *"
    script: "astack memory consolidate --html ~/.astack/journal/$(date +%F)-memory.html --quiet-if-unchanged"
  - name: astack-ask-tonight
    schedule: "0 21 * * *"
    prompt: "오늘 이해물의 남은 질문과 dream의 새 질문에서 오늘 밤 돌릴 질문 후보 3개를 번호로 보여줘. 답이 오면 `astack goal add`로 넣는다. 답이 없으면 1번만 넣는다."
  - name: astack-night
    schedule: "0 1 * * *"
    script: "astack goal run --max 3 --host claude"
```

- [ ] **Step 3: `recipes/hermes/telegram-topics.yaml`**

```yaml
# 맥미니에서 검증 전. platforms.telegram.extra.dm_topics 에 붙인다.
dm_topics:
  - name: Quest
    skill: astack     # 링크·질문을 던지면 입구가 판단 (quest 기본)
    silent: true      # 완료 알림은 무음
  - name: Journal
    skill: dream
```

- [ ] **Step 4: `recipes/hermes/README.md`** — 설치 순서(맥미니): ① `git clone` → `./setup --host cli claude` ② `hermes plugins install obra/superpowers --enable` ③ cron.yaml, telegram-topics.yaml 적용 ④ `astack feed seed`로 화이트리스트 ⑤ 하루 사이클 확인 체크리스트(05:00→07:00→20:00→20:30→21:00→01:00). 되돌리기 순서. 머리에 "맥미니에서 검증 전".

- [ ] **Step 5: `recipes/aside/permissions.md`** — `writableRoots`에 `~/rooms`, 작업 위치(`~/personal`) 추가 방법, Aside 스킬은 setup이 복사(동기화 안 됨, 바뀌면 `./setup --host aside` 다시), 실험 가드레일 요약.

- [ ] **Step 6: Tests** — `tests/test_recipes.py`: 파일 존재; cron.yaml에 §9.4의 6개 job 이름과 시각(`0 5`, `0 7`, `0 20`, `30 20`, `0 21`, `0 1`); Hermes 파일 머리에 "검증 전"; AGENTS 스니펫에 `astack-spec`, `astack recall --now`. YAML 파서 없이 텍스트로 검사.

- [ ] **Step 7: commit** `docs(recipes): codex, hermes, aside recipes`

---

### Task 3: `astack goal` — 밤 goal 실행기

**Files:**
- Create: `lib/astack_cli/goal.py`
- Modify: `lib/astack_cli/cli.py`, `lib/astack_cli/paths.py` (`goals_dir()` = `home()/"goals"`)
- Test: `tests/test_goal.py`

**Interfaces:**
- 상태: `~/.astack/goals/<id>/goal.json` = `{"id","question","added","status": "queued|running|done|failed","host","attempts","pid","started","finished","reason"}`; 같은 폴더에 `progress.md`(결정 기록·체크포인트, 스킬이 씀), `result.json`(`{"success": bool, "summary": [3줄], "map": "<경로>"}`, 스킬이 씀), `run.log`.
- `goal.add(question: str, now=None) -> dict` — id = `YYYYMMDD-HHMMSS-<slug 앞 20자>`
- `goal.list_goals() -> list[dict]` (added 순)
- `goal.run(max_goals: int = 3, host: str = "claude", runner=subprocess.run, now=None, timeout: int = 3*3600) -> list[dict]`
  - 이번 실행 대상: ① `running`인데 pid가 살아 있지 않은 것(이어서), ② `queued`, 순서대로, 합쳐 최대 `max_goals`. 살아 있는 `running`이 있으면 그 수만큼 상한에서 뺀다.
  - 각 goal: 상태 `running`, `attempts+=1`, pid 기록 → 호스트 명령 실행(`claude -p <prompt> --permission-mode acceptEdits` / `codex exec <prompt>`, cwd = 작업 위치 `~/personal/notes`가 있으면 거기, 없으면 home) → 끝나면 `result.json` 읽기: 있고 `success`가 true면 `done`, 아니면 `failed` + `reason`(“result.json 없음”, “result.json 깨짐”, “success=false”, “시간 초과”, “종료 코드 N”).
  - 프롬프트(한국어, 고정 문자열 + 경로): "astack:quest 스킬로 다음 질문을 밤 goal로 처리해: <질문>. 결정과 진행은 <dir>/progress.md에 계속 남기고(끊기면 이 파일을 읽고 이어서), 끝나면 <dir>/result.json에 {\"success\": true|false, \"summary\": [핵심 3줄], \"map\": \"<지도 경로>\"}를 써. 이어서 하는 중이면 progress.md를 먼저 읽어." 
- `goal.report(day: date) -> list[dict]` — 그날(01:00 실행분 = `finished`가 그날) goal별 `{"question","status","summary","map","reason"}`.
- CLI: `astack goal add "<질문>"`, `astack goal list [--json]`, `astack goal run [--max 3] [--host claude|codex]`, `astack goal report [--date YYYY-MM-DD|yesterday|today] [--text]` — `--text`는 Telegram용 짧은 글(goal마다 ✓/✗ 질문, 3줄, 지도 경로). 보고할 게 없으면 아무것도 출력하지 않는다(Hermes가 보내지 않게).

- [ ] **Step 1: Failing tests** — `tests/test_goal.py` (ASTACK_HOME 격리, 가짜 runner):
  - `test_add_and_list`
  - `test_run_marks_done_from_result` — runner가 `<dir>/result.json`에 success true를 쓰고 0 반환 → done, summary 보존
  - `test_missing_result_is_failure` — runner가 아무것도 안 씀 → failed, reason "result.json 없음"; 깨진 JSON → "result.json 깨짐"
  - `test_max_three_per_night` — queued 5개 → 3개만 실행, 2개 queued로 남음
  - `test_dead_running_goal_resumes` — status running, pid 999999(죽은 pid) → 다음 run이 먼저 그 goal을 다시 실행, attempts 2
  - `test_live_running_goal_counts_against_cap` — status running, pid = os.getpid() → 상한에서 1 빠짐, 그 goal은 건드리지 않음
  - `test_prompt_mentions_progress_and_result` — runner가 받은 명령의 프롬프트에 `progress.md`, `result.json`, 질문이 들어 있음; host codex면 `["codex","exec",…]`
  - `test_timeout_is_failure` — runner가 `subprocess.TimeoutExpired`를 던짐 → failed "시간 초과"
  - `test_report_text_is_empty_when_nothing` — CLI `goal report --text`가 아무것도 출력하지 않고 0
  - `test_report_text_lists_goals` — done/failed 각각 ✓/✗ 줄

- [ ] **Step 2–4:** 구현(`goal.py`, `paths.goals_dir`, CLI 하위 명령 `goal`), 테스트 통과. pid 생존 확인은 `os.kill(pid, 0)`(ProcessLookupError → 죽음, PermissionError → 살아 있음). 상태 파일은 tmp + `os.replace`로 쓴다.

- [ ] **Step 5: commit** `feat(cli): astack goal queues and runs up to 3 night goals with resume`

---

### Task 4: 기억 정리 HTML 보고서

**Files:** Modify `lib/astack_cli/memory.py` (보고서 렌더 함수), `lib/astack_cli/cli.py` (`memory consolidate --html PATH --quiet-if-unchanged`). Test `tests/test_memory_ops.py`.

- `memory.render_report(rep: dict, day: date) -> str` — self-contained HTML(키트 마커 `<!--astack:css-->`, 메타 세 개, `data-astack` 30s/3m/source, "Claude Code가 썼습니다" 서명): 30초 = "기록 N→M, 합침 a, 대체 b, 감쇠 c, 지움 d, 승격 e"; 3분 = 승격 목록 + **패치 제안(제안만, 자동 적용 안 함)**; 본문 = 대체·감쇠·지움 목록(key). 아무 변화가 없으면 30초에 "바뀐 것 없음".
- CLI: `--html PATH`이면 보고서를 쓰고 `astack inline` 처리(같은 함수 호출) 후 경로 출력. `--quiet-if-unchanged`이면 변화가 없을 때 아무것도 출력·저장하지 않는다(Hermes가 보내지 않게). JSON 출력은 `--html`이 없을 때만.
- Tests: 보고서가 `check_html` 에러 0(메타 채운 상태로 렌더); 패치 제안 문구에 "제안"; 변화 없음 + quiet → 파일 없음, stdout 빈 문자열.
- commit `feat(memory): consolidate writes an HTML change report`

---

### Task 5: paper 무손실 검사 `astack gate paper`

**Files:** Create `lib/astack_cli/gate.py`; modify `cli.py`, `skills/paper/SKILL.md` (6단계에서 이 명령 사용). Test `tests/test_gate.py`.

- `gate.labels(text: str) -> set[str]` — `Figure N`, `Fig. N`(→ `Figure N`), `Table N`, `Algorithm N`(N은 숫자, 부록 `A1` 같은 영숫자 포함) 정규화.
- `gate.paper(out_html: str, source_text: str, numbers: list[str] = ()) -> list[str]` — 원문 레이블 중 결과물 텍스트에 없는 것, 결과물의 `<img` 개수가 원문 Figure 개수보다 적으면 그 사실, `numbers` 중 결과물에 없는 것 → 빠진 것 목록.
- CLI: `astack gate paper <out.html> --source <원문.html|.txt> [--numbers <파일, 한 줄에 하나>]` → 빠진 게 없으면 "gate: 통과" 종료 0, 있으면 줄마다 `빠짐: …` 종료 1. 원문이 HTML이면 태그를 벗겨 텍스트로.
- Tests: Fig./Figure 정규화; 빠진 Table 검출; img 부족 검출; numbers; CLI 종료 코드.
- commit `feat(cli): astack gate paper checks figures, tables and numbers against the source`

---

### Task 6: paper·repo 모바일 그림 칸

**Files:** `skills/paper/assets/template.html`, `skills/repo/assets/template.html`, 두 SKILL.md, `tests/test_templates.py`.

- quest 장 템플릿과 같은 방식: 각 `.scene` 끝에 `<div class="inl vis-inl"><!-- 좁은 화면용: 오른쪽 그림 칸과 같은 그림. SVG id·marker id는 -m 접미사로 바꾼다 --></div>`.
- SKILL에 한 줄: "그림은 오른쪽 칸(`.vis`)과 장면 안 모바일 칸(`.vis-inl`)에 둘 다 넣는다. 복사한 SVG의 id는 바꾼다(check가 dup-id로 잡는다)."
- Test: 두 템플릿의 `data-i` 장면마다 `vis-inl`이 있다.
- commit `feat(templates): mobile figure slots for paper and repo`

---

### Task 7: 작은 수정 묶음

**Files:** `lib/astack_cli/route.py`, `lib/astack_cli/memory.py` (`search`), `lib/astack_cli/cli.py` (`inline`, `done`), `lib/astack_cli/done.py`, `skills/recall/SKILL.md`, `recipes/claude/CLAUDE.md.snippet`, 테스트들.

1. **recall 오분류**: `route.RECALL`에서 `뭐`를 빼고, 시간어와 `거|것` 사이 간격을 6자 이하로. 테스트: "최근 나온 모델 중 뭐가 제일 빠른지 알아봐" → quest, "지난주 거 보여줘"·"에이전트 관련 뭐 쌓였지" → recall(“쌓였지” 패턴은 유지).
2. **`memory.search` UTF-8**: `_split(f.read_bytes())`(surrogateescape)로 읽는다. 테스트: 잘못된 바이트가 든 기록이 있어도 search가 다른 기록을 찾고 종료 0.
3. **여러 파일·폴더**: `astack inline <f|폴더>...`, `astack done <f|폴더>... --skill <s>` — 폴더면 그 안의 `*.html`(정렬). done은 파일마다 결과 줄, 하나라도 실패면 종료 1. 테스트 추가.
4. **recall now 선생성(§9.2)**: `skills/recall/SKILL.md` now 모드에 "결과가 없으면 지금 작업과 같은 맥락의 이해물 하나를 백그라운드 서브에이전트로 만든다(작업당 1개, quest Quick 또는 해당 원자)" 추가; CLAUDE 스니펫의 recall 줄에 "없으면 하나 만들어 둬"를 덧붙임. 테스트: SKILL에 "작업당 1개".
- commit(s) `fix: tighter recall phrases, tolerant memory search, folder inline/done, recall pre-generation`

---

### Task 8: README와 이 맥 설치

**Files:** `README.md`, `docs/superpowers/plans/2026-10-06-astack-p5-install.md`

- [ ] **Step 1: README** (English, very short): Install 절을 `./setup` 한 줄로 바꾼다:

```markdown
## Install

```bash
git clone https://github.com/alto-computer/astack ~/personal/astack
~/personal/astack/setup            # auto: cli, claude, codex, aside if present
```

Then in Claude Code: `/plugin marketplace add ~/personal/astack` and `/plugin install astack@astack-dev`.
Undo: `./setup --uninstall`. Mac mini scheduling: `recipes/hermes/README.md`.
```

Skills 표에 `goal` 행은 넣지 않는다(스킬이 아니라 CLI). CLI 줄에 `goal | gate | setup` 추가.

- [ ] **Step 2: 이 맥에 설치** (실제 실행, 컨트롤러 확인 후):
  1. `./setup --dry-run` 출력 확인 → 2. `./setup` → 3. `ls ~/.codex/skills/astack-*`, `ls ~/.aside/u/0/skills/user/astack-*`, `grep -c "astack:begin" ~/.claude/CLAUDE.md ~/.codex/AGENTS.md` → 4. 기존 `~/.claude/CLAUDE.md`의 스니펫(P1에서 표식 없이 넣은 것)을 표식 블록으로 정리(중복 제거) → 5. `codex exec "astack-recall 스킬이 보이면 '보임'이라고만 답해"`로 Codex가 스킬을 읽는지 확인 → 6. Claude 플러그인 두 명령은 사용자가 직접.
- [ ] **Step 3:** 결과를 `2026-10-06-astack-p5-install.md`에 기록하고 커밋.

## 기본값과 열린 결정

| 항목 | 기본값 | 근거 |
|---|---|---|
| Codex 설치 방식 | `~/.codex/skills/astack-*` 심볼릭 링크 (`.codex-plugin/` 대신) | 이 맥의 Codex가 이미 그 폴더를 읽음, 플러그인 형식은 검증 불가 |
| Hermes | 레시피만 (`.hermes-plugin/` 없음) | 이 맥에 Hermes 없음, 형식 검증 불가 |
| 밤 goal 권한 | `claude -p --permission-mode acceptEdits` | 무인 실행이지만 위험 명령 우회는 하지 않음 |
| 밤 goal 작업 위치 | `~/personal/notes` (없으면 home) | §11.2 |
