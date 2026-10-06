"""밤 goal 큐와 실행기. 상태는 ~/.astack/goals/<id>/ 아래 파일에만 둔다."""
import datetime
import json
import os
import re
import subprocess
from pathlib import Path

from . import paths
from .memory import _write_atomic

PROMPT = (
    "astack:quest 스킬로 다음 질문을 밤 goal로 처리해: {q}. "
    "결정과 진행은 {d}/progress.md에 계속 남기고(끊기면 이 파일을 읽고 이어서), "
    "끝나면 {d}/result.json에 {{\"success\": true|false, \"summary\": [핵심 3줄], \"map\": \"<지도 경로>\"}}를 써. "
    "이어서 하는 중이면 progress.md를 먼저 읽어."
)


def _save(g: dict) -> None:
    d = paths.goals_dir() / g["id"]
    d.mkdir(parents=True, exist_ok=True)
    _write_atomic(d / "goal.json", json.dumps(g, ensure_ascii=False).encode("utf-8"))


def _slug(q: str) -> str:
    return re.sub(r"\W+", "-", q).strip("-")[:20].strip("-") or "goal"


def add(question: str, now=None) -> dict:
    now = now or datetime.datetime.now()
    base = f"{now:%Y%m%d-%H%M%S}-{_slug(question)}"
    gid, n = base, 1
    while (paths.goals_dir() / gid).exists():
        n += 1
        gid = f"{base}-{n}"
    g = {"id": gid, "question": question, "added": now.isoformat(timespec="seconds"), "status": "queued",
         "host": None, "attempts": 0, "pid": None, "started": None, "finished": None, "reason": None}
    _save(g)
    return g


def list_goals() -> list[dict]:
    out = []
    for f in paths.goals_dir().glob("*/goal.json"):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return sorted(out, key=lambda g: (g.get("added", ""), g.get("id", "")))


def _alive(pid) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _cwd() -> str:
    notes = Path.home() / "personal" / "notes"
    return str(notes if notes.is_dir() else Path.home())


def _command(host: str, prompt: str) -> list[str]:
    if host == "codex":
        return ["codex", "exec", prompt]
    return ["claude", "-p", prompt, "--permission-mode", "acceptEdits"]


def _judge(d: Path) -> tuple[bool, str | None]:
    f = d / "result.json"
    if not f.is_file():
        return False, "result.json 없음"
    try:
        r = json.loads(f.read_text(encoding="utf-8"))
        ok = isinstance(r, dict) and r.get("success") is True
    except (OSError, ValueError):
        return False, "result.json 깨짐"
    if ok:
        return True, None
    return False, "success=false"


def _run_one(g: dict, host, runner, now, timeout) -> dict:
    d = paths.goals_dir() / g["id"]
    g.update(status="running", host=host, attempts=g["attempts"] + 1, pid=os.getpid(),
             started=now.isoformat(timespec="seconds"), finished=None, reason=None)
    _save(g)
    (d / "result.json").unlink(missing_ok=True)  # 이전 시도의 결과가 이번 성공으로 읽히지 않게
    prompt = PROMPT.format(q=g["question"], d=d)
    reason = None
    try:
        with open(d / "run.log", "ab") as log:
            p = runner(_command(host, prompt), cwd=_cwd(), stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        code = getattr(p, "returncode", 0)
        ok, reason = _judge(d)
        if not ok and code and reason == "result.json 없음":
            reason = f"종료 코드 {code}"
    except subprocess.TimeoutExpired:
        ok, reason = False, "시간 초과"
    except OSError as e:
        ok, reason = False, f"실행 실패: {e}"
    g.update(status="done" if ok else "failed", pid=None, reason=reason,
             finished=now.isoformat(timespec="seconds"))
    _save(g)
    return g


def run(max_goals: int = 3, host: str = "claude", runner=subprocess.run, now=None,
        timeout: int = 3 * 3600) -> list[dict]:
    goals = list_goals()
    live = sum(1 for g in goals if g["status"] == "running" and _alive(g.get("pid")))
    resume = [g for g in goals if g["status"] == "running" and not _alive(g.get("pid"))]
    queued = [g for g in goals if g["status"] == "queued"]
    todo = (resume + queued)[:max(0, max_goals - live)]
    out = []
    for g in todo:
        out.append(_run_one(g, host, runner, now or datetime.datetime.now(), timeout))
    return out


def report(day: datetime.date) -> list[dict]:
    out = []
    for g in list_goals():
        if g["status"] not in ("done", "failed") or not (g.get("finished") or "").startswith(day.isoformat()):
            continue
        r = {}
        try:
            r = json.loads((paths.goals_dir() / g["id"] / "result.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        if not isinstance(r, dict):
            r = {}
        out.append({"question": g["question"], "status": g["status"], "summary": r.get("summary") or [],
                    "map": r.get("map"), "reason": g.get("reason")})
    return out


def report_text(items: list[dict]) -> str:
    lines = []
    for i in items:
        if i["status"] == "done":
            lines.append(f"✓ {i['question']}")
            lines += [f"  {s}" for s in i["summary"][:3]]
            if i["map"]:
                lines.append(f"  지도: {i['map']}")
        else:
            lines.append(f"✗ {i['question']} — {i['reason'] or '실패'}")
    return "\n".join(lines)
