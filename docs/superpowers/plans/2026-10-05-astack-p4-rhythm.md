# astack P4 리듬과 기억 (memory · dream · feed) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기억을 정리하는 `memory prune|consolidate|restore`, 하루를 엮는 dream(간격 복습, 내 말로 한 줄, 주간 수렴), 화이트리스트 채널로 "오늘 30분"을 만드는 feed를 만든다. 모두 Rooms 없이 동작한다.

**Architecture:** 상태는 `~/.astack/`의 파일뿐(memory.jsonl, outputs.log, archive/). 결정적인 일(수집, 날짜 계산, 중복 제거, 원자적 교체)은 CLI, 엮고 쓰는 일은 스킬. 스케줄(cron, Telegram)은 P5 호스트 몫이라 여기서는 명령이 한 번에 끝나게만 만든다.

**Tech Stack:** Python 3 표준 라이브러리 + unittest, `yt-dlp`(feed), 키트(alto.css, alto-ext.css, reader.js, quiz.js).

**Spec:** `docs/superpowers/specs/2026-10-05-astack-v1-handoff.md` (§6.5 feed·dream·memory, §7 상태와 기억, §9.4~9.6, §15 P4, §20)

## Global Constraints

- P2, P3 계획의 Global Constraints를 따른다.
- `memory.jsonl`이 기억의 진실(SSOT). 한 줄에 기록 하나. consolidate 직전 상태는 `archive/YYYY-MM-DD.jsonl` (§7).
- `.lock`은 consolidate 중에만 잡는다 (§7).
- consolidate: 중복 합치기, 최신 told > 오래된 observed, 오래된 observed는 confidence 감쇠, told는 취소 전까지 유지, 반복 교정 승격, 스킬 결함은 패치 **제안만**(자동 적용 금지), 임시 파일 + rename으로 원자적 교체 (§7).
- 기억에는 기록에서 다시 알 수 없는 것만: 사용자가 말한 선호·제외·피드백·교정, dream이 발견한 관심 변화(observed). 만든/읽은 것, 구독, 좋아요는 쓰지 않는다 (§7).
- dream: 입력은 오늘 생긴 이해물(outputs.log + rooms:created). 간격 복습은 1일·7일·30일 전 이해물에서 1문항씩, 날짜로 고르므로 상태 불필요. 주 1회 주간 수렴: 이번 주 map 변화 + "이번 주 내 일에 쓸 것 3가지". 관심 변화는 `memory add`로 관찰만, consolidate는 하지 않는다. Rooms가 있으면 `rooms link --journal <날짜>` (§6.5).
- feed: 화이트리스트 YouTube 채널만. 화이트리스트는 memory의 told 기록이고 레포에 커밋하지 않는다. 이미 이해물이 있는 소스는 건너뜀(outputs.log + 본문 원문 링크). 30분 분량만: 깊은 매거진 1~2개(~20분) + 짧은 카드 2~3개(각 3분 층), 읽는 순서대로. 밀린 목록 없음 (§6.5).
- 예산: feed는 아침 30분 분량. 무거운 자동 작업은 밤에 (§9.6).

## Review Focus

1. consolidate 도중 다른 프로세스가 `memory add` — 그 줄이 사라지면 안 된다. (Task 2 `test_append_during_consolidate_is_kept`)
2. consolidate를 매일 돌림 — observed의 confidence가 날마다 거듭 깎이면 안 된다(나이로 다시 계산). (Task 2 `test_decay_is_not_compounded`)
3. 깨진 줄(JSON 아님)이 섞인 memory.jsonl — consolidate가 죽지 않고, 깨진 줄은 archive에 남는다. (Task 2 `test_broken_lines_survive_in_archive`)
4. 30일 전 이해물이 없는 날 — 간격 복습이 빈 칸 없이 있는 것만 낸다. (Task 3 `test_spaced_review_skips_missing_days`)
5. 영상 ID가 이미 다른 이해물 본문에 있음(youtu.be 짧은 링크로) — feed가 다시 만들지 않는다. (Task 5 `test_seen_ids_from_short_links`)

---

## 파일 구조

```
lib/astack_cli/memory.py     prune, restore, consolidate, 잠금, 원자적 쓰기 (Task 1, 2)
lib/astack_cli/dream.py      오늘 이해물·간격 복습·주간 모음 (Task 3)
lib/astack_cli/feed.py       화이트리스트, 채널 최신 영상, 이미 본 영상 (Task 5)
lib/astack_cli/paths.py      archive_dir, lock_file, journal_dir (Task 1)
lib/astack_cli/cli.py        memory 옵션, dream collect, feed seed|candidates (Task 1~5)
skills/dream/{SKILL.md,assets/template.html}   (Task 4)
skills/feed/{SKILL.md,assets/template.html}    (Task 6)
tests/test_memory_ops.py, test_dream.py, test_feed.py
```

---

### Task 1: `memory prune` · `memory restore`, 잠금과 원자적 쓰기

**Files:**
- Modify: `lib/astack_cli/memory.py`, `lib/astack_cli/paths.py`, `lib/astack_cli/cli.py` (`_memory`, `build_parser`)
- Test: `tests/test_memory_ops.py`

**Interfaces:**
- Produces:
  - `paths.archive_dir() -> Path` (`home()/"archive"`), `paths.lock_file() -> Path` (`home()/".lock"`), `paths.journal_dir() -> Path` (`home()/"journal"`)
  - `memory.MemoryLocked(Exception)`, `memory.lock()` 컨텍스트 매니저(`O_CREAT|O_EXCL`, 10분 넘은 잠금은 치운다)
  - `memory.read_lines() -> list[str]` (원문 줄 그대로), `memory.parse(lines) -> list[dict]` (깨진 줄 건너뜀)
  - `memory.archive(today: date) -> Path` (오늘 archive가 이미 있으면 덮지 않는다 — 하루의 첫 상태를 남긴다)
  - `memory.replace_lines(lines: list[str], since_size: int) -> None` (임시 파일에 쓰고, 그 사이 늘어난 꼬리를 붙여 `os.replace`)
  - `memory.prune(key: str | None = None, type_: str | None = None, before: str | None = None, today=None) -> int`
  - `memory.restore(date: str, today=None) -> Path`
  - `memory.add`는 잠금이 있으면 최대 5초 기다린 뒤 쓴다.
  - CLI: `astack memory prune [--key K] [--type T] [--before YYYY-MM-DD]`, `astack memory restore YYYY-MM-DD`

- [ ] **Step 1: Failing tests** — `tests/test_memory_ops.py`

```python
import datetime
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli, memory, paths  # noqa: E402

D = datetime.date(2026, 10, 5)


def rec(**kw):
    base = {"type": "correction", "key": "skill:interview", "insight": "x", "source": "told", "date": "2026-10-01", "host": "h"}
    base.update(kw)
    return json.dumps(base, ensure_ascii=False)


class MemoryOpsBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get("ASTACK_HOME")
        os.environ["ASTACK_HOME"] = self.tmp.name

    def tearDown(self):
        if self.old is None:
            os.environ.pop("ASTACK_HOME", None)
        else:
            os.environ["ASTACK_HOME"] = self.old
        self.tmp.cleanup()

    def write(self, *lines):
        paths.memory_file().write_text("".join(l + "\n" for l in lines), encoding="utf-8")


class PruneTest(MemoryOpsBase):
    def test_prune_by_key_prefix_and_archives(self):
        self.write(rec(key="channel:a"), rec(key="channel:b"), rec(key="skill:x"))
        self.assertEqual(memory.prune(key="channel:", today=D), 2)
        keys = [r["key"] for r in memory.parse(memory.read_lines())]
        self.assertEqual(keys, ["skill:x"])
        self.assertEqual(len((paths.archive_dir() / "2026-10-05.jsonl").read_text().splitlines()), 3)

    def test_prune_by_type_and_before(self):
        self.write(rec(type="taste", source="observed", date="2026-08-01"), rec(type="taste", source="observed", date="2026-10-04"))
        self.assertEqual(memory.prune(type_="taste", before="2026-09-01", today=D), 1)

    def test_prune_needs_a_filter(self):
        self.write(rec())
        with self.assertRaises(ValueError):
            memory.prune(today=D)

    def test_restore_brings_back_archive(self):
        self.write(rec(key="a"), rec(key="b"))
        memory.prune(key="a", today=D)
        memory.restore("2026-10-05", today=D)
        self.assertEqual(len(memory.read_lines()), 2)

    def test_restore_missing_date_is_error(self):
        with self.assertRaises(FileNotFoundError):
            memory.restore("2026-01-01", today=D)

    def test_archive_keeps_first_state_of_the_day(self):
        self.write(rec(key="a"))
        memory.archive(D)
        self.write(rec(key="a"), rec(key="b"))
        memory.archive(D)
        self.assertEqual(len((paths.archive_dir() / "2026-10-05.jsonl").read_text().splitlines()), 1)


class LockTest(MemoryOpsBase):
    def test_lock_is_exclusive(self):
        with memory.lock():
            with self.assertRaises(memory.MemoryLocked):
                with memory.lock():
                    pass
        self.assertFalse(paths.lock_file().exists())

    def test_stale_lock_is_cleared(self):
        paths.lock_file().write_text("1")
        old = paths.lock_file().stat().st_mtime - 3600
        os.utime(paths.lock_file(), (old, old))
        with memory.lock():
            pass

    def test_replace_lines_keeps_appended_tail(self):
        self.write(rec(key="a"))
        size = paths.memory_file().stat().st_size
        with open(paths.memory_file(), "a", encoding="utf-8") as f:
            f.write(rec(key="late") + "\n")
        memory.replace_lines([rec(key="a2")], since_size=size)
        keys = [r["key"] for r in memory.parse(memory.read_lines())]
        self.assertEqual(keys, ["a2", "late"])


class CliTest(MemoryOpsBase):
    def test_cli_prune_and_restore(self):
        self.write(rec(key="channel:a"), rec(key="skill:x"))
        self.assertEqual(cli.main(["memory", "prune", "--key", "channel:"]), 0)
        self.assertEqual(cli.main(["memory", "prune"]), 2)
        today = datetime.date.today().isoformat()
        self.assertEqual(cli.main(["memory", "restore", today]), 0)
        self.assertEqual(cli.main(["memory", "restore", "1999-01-01"]), 2)

    def test_cli_add_still_works(self):
        self.assertEqual(cli.main(["memory", "add", '{"type":"preference","key":"k","insight":"i","source":"told"}']), 0)


if __name__ == "__main__":
    unittest.main()
```

Run: `python3 -m unittest tests.test_memory_ops` → FAIL (AttributeError)

- [ ] **Step 2: `paths.py`** — append:

```python
def archive_dir() -> Path:
    return home() / "archive"


def lock_file() -> Path:
    return home() / ".lock"


def journal_dir() -> Path:
    return home() / "journal"
```

- [ ] **Step 3: `memory.py`** — add imports `contextlib`, `shutil`, `time`, then append:

```python
STALE_LOCK = 600  # 초. 이보다 오래된 잠금은 죽은 프로세스가 남긴 것으로 본다


class MemoryLocked(RuntimeError):
    pass


@contextlib.contextmanager
def lock():
    lf = paths.lock_file()
    lf.parent.mkdir(parents=True, exist_ok=True)
    if lf.exists() and time.time() - lf.stat().st_mtime > STALE_LOCK:
        lf.unlink(missing_ok=True)
    try:
        fd = os.open(lf, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise MemoryLocked("다른 consolidate가 돌고 있습니다") from None
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        lf.unlink(missing_ok=True)


def read_lines() -> list[str]:
    f = paths.memory_file()
    return f.read_text(encoding="utf-8").splitlines() if f.exists() else []


def parse(lines: list[str]) -> list[dict]:
    out = []
    for line in lines:
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(r, dict):
            out.append(r)
    return out


def archive(today: datetime.date) -> Path:
    d = paths.archive_dir()
    d.mkdir(parents=True, exist_ok=True)
    a = d / f"{today.isoformat()}.jsonl"
    if not a.exists() and paths.memory_file().exists():
        shutil.copyfile(paths.memory_file(), a)
    return a


def replace_lines(lines: list[str], since_size: int) -> None:
    f = paths.memory_file()
    tmp = f.with_name(f.name + ".tmp")
    body = "".join(l + "\n" for l in lines)
    with open(f, "rb") as cur:
        cur.seek(since_size)
        tail = cur.read().decode("utf-8", "ignore")  # 읽은 뒤에 add로 붙은 줄
    tmp.write_text(body + tail, encoding="utf-8")
    os.replace(tmp, f)


def _dump(r: dict) -> str:
    return json.dumps(r, ensure_ascii=False, separators=(",", ":"))


def prune(key: str | None = None, type_: str | None = None, before: str | None = None, today=None) -> int:
    if not (key or type_ or before):
        raise ValueError("--key, --type, --before 중 하나는 있어야 합니다")
    today = today or datetime.date.today()
    with lock():
        f = paths.memory_file()
        size = f.stat().st_size if f.exists() else 0
        lines = read_lines()
        archive(today)
        keep, removed = [], 0
        for line in lines:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                keep.append(line)
                continue
            hit = isinstance(r, dict) \
                and (key is None or str(r.get("key", "")).startswith(key)) \
                and (type_ is None or r.get("type") == type_) \
                and (before is None or str(r.get("date", "")) < before)
            if hit:
                removed += 1
            else:
                keep.append(line)
        if removed:
            replace_lines(keep, size)
        return removed


def restore(date: str, today=None) -> Path:
    a = paths.archive_dir() / f"{date}.jsonl"
    if not a.exists():
        raise FileNotFoundError(f"archive가 없습니다: {a}")
    today = today or datetime.date.today()
    with lock():
        if today.isoformat() != date:
            archive(today)
        tmp = paths.memory_file().with_name("memory.jsonl.tmp")
        shutil.copyfile(a, tmp)
        os.replace(tmp, paths.memory_file())
    return a
```

and at the top of `add`'s write (just before `fd = os.open(...)`):

```python
    for _ in range(100):  # consolidate 중이면 최대 5초 기다린다
        if not paths.lock_file().exists():
            break
        time.sleep(0.05)
```

- [ ] **Step 4: CLI** — replace the `memory` subparser and `_memory`:

```python
def _memory(args) -> int:
    try:
        if args.action == "add":
            rec = memory.add(args.value or "")
            print(json.dumps(rec, ensure_ascii=False))
        elif args.action == "search":
            for rec in memory.search(args.value or ""):
                print(json.dumps(rec, ensure_ascii=False))
        elif args.action == "prune":
            print(f"지운 기록 {memory.prune(key=args.key, type_=args.type, before=args.before)}개")
        elif args.action == "restore":
            print(memory.restore(args.value or ""))
        elif args.action == "consolidate":
            return _consolidate(args)
    except (memory.InvalidRecord, ValueError, FileNotFoundError, memory.MemoryLocked) as e:
        print(f"astack memory: {e}", file=sys.stderr)
        return 2
    return 0


def _consolidate(args) -> int:
    print("consolidate는 Task 2에서 붙는다", file=sys.stderr)
    return 2
```

```python
    m = sub.add_parser("memory", help="기억 쓰기·찾기·정리")
    m.add_argument("action", choices=["add", "search", "prune", "restore", "consolidate"])
    m.add_argument("value", nargs="?")
    m.add_argument("--key")
    m.add_argument("--type")
    m.add_argument("--before")
    m.add_argument("--dry-run", action="store_true")
    m.set_defaults(fn=_memory)
```

(`InvalidRecord`는 `ValueError`의 하위 클래스라 순서와 무관하다.)

- [ ] **Step 5: Run tests** → `python3 -m unittest tests.test_memory_ops tests.test_memory tests.test_cli` OK, then full suite.

- [ ] **Step 6: Commit**

```bash
git add lib/astack_cli/memory.py lib/astack_cli/paths.py lib/astack_cli/cli.py tests/test_memory_ops.py
git commit -m "feat(memory): prune and restore with archive, lock and atomic replace"
```

---

### Task 2: `memory consolidate`

**Files:**
- Modify: `lib/astack_cli/memory.py`, `lib/astack_cli/cli.py` (`_consolidate`)
- Test: `tests/test_memory_ops.py` (클래스 추가)

**Interfaces:**
- Consumes: Task 1의 `lock`, `read_lines`, `parse`, `archive`, `replace_lines`, `_dump`.
- Produces: `memory.consolidate(today=None, dry_run=False) -> dict` 보고서
  `{"before": int, "after": int, "merged": int, "superseded": [key…], "decayed": [[key, c0, c]…], "dropped": [key…], "promoted": [key…], "patch_suggestions": [{"key", "count", "insights"}…], "broken": int}`.
- 규칙:
  1. 깨진 줄은 결과에서 빠지고(`broken` 수) archive에 남는다.
  2. 중복: `(type, key, insight, source)`가 같으면 가장 최근 `date` 하나만.
  3. 같은 `key`에 `told`가 있고 그 `date`가 `observed`의 `date`보다 늦거나 같으면 그 `observed`를 뺀다(`superseded`).
  4. `observed` 감쇠: `c0 = rec.get("confidence0", rec.get("confidence", 0.5))`, `age = (today - date).days`, `c = round(c0 * 0.5 ** (age / 30), 3)`. 결과에 `confidence0 = c0`, `confidence = c`를 쓴다(나이로 다시 계산 → 매일 돌려도 겹쳐 깎이지 않는다). `c < 0.2`면 뺀다(`dropped`).
  5. 승격: `type == "correction"`이고 같은 `key`가 3개 이상이면, 그 key의 `preference` 기록 `{"type":"preference","key":key,"insight":"규칙: " + 가장 최근 insight 3개를 " / "로 이은 것,"source":"told","date":today,"host":paths.host(),"promoted_from":n}`을 더한다(이미 `promoted_from`이 있는 같은 key의 preference가 있으면 더하지 않는다). key가 `skill:`로 시작하면 `patch_suggestions`에도 넣는다 — 레포 패치는 제안만.
  6. `dry_run`이면 파일을 바꾸지 않고 보고서만.
- CLI: `astack memory consolidate [--dry-run]` → 보고서 JSON 한 줄.

- [ ] **Step 1: Failing tests** (append to `tests/test_memory_ops.py`, before `if __name__`)

```python
class ConsolidateTest(MemoryOpsBase):
    def keys(self):
        return [(r["type"], r["key"]) for r in memory.parse(memory.read_lines())]

    def test_duplicates_merge_to_latest(self):
        self.write(rec(date="2026-10-01"), rec(date="2026-10-03"))
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["merged"], 1)
        self.assertEqual([r["date"] for r in memory.parse(memory.read_lines())], ["2026-10-03"])

    def test_newer_told_supersedes_observed(self):
        self.write(rec(type="taste", key="topic:a", source="observed", date="2026-10-01", confidence=0.9),
                   rec(type="preference", key="topic:a", source="told", date="2026-10-02"))
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["superseded"], ["topic:a"])
        self.assertEqual(self.keys(), [("preference", "topic:a")])

    def test_decay_is_not_compounded(self):
        self.write(rec(type="taste", key="topic:b", source="observed", date="2026-09-05", confidence=0.8))
        memory.consolidate(today=D)
        memory.consolidate(today=D)
        r = memory.parse(memory.read_lines())[0]
        self.assertEqual((r["confidence0"], r["confidence"]), (0.8, 0.4))

    def test_old_observed_is_dropped(self):
        self.write(rec(type="taste", key="topic:c", source="observed", date="2026-06-01", confidence=0.5))
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["dropped"], ["topic:c"])
        self.assertEqual(self.keys(), [])

    def test_told_is_kept_regardless_of_age(self):
        self.write(rec(type="exclude", key="channel:z", source="told", date="2025-01-01"))
        memory.consolidate(today=D)
        self.assertEqual(self.keys(), [("exclude", "channel:z")])

    def test_repeated_corrections_promote_once(self):
        self.write(rec(insight="a", date="2026-10-01"), rec(insight="b", date="2026-10-02"), rec(insight="c", date="2026-10-03"))
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["promoted"], ["skill:interview"])
        self.assertEqual(rep["patch_suggestions"][0]["count"], 3)
        rep2 = memory.consolidate(today=D)
        self.assertEqual(rep2["promoted"], [])
        self.assertEqual(sum(1 for t, _ in self.keys() if t == "preference"), 1)

    def test_broken_lines_survive_in_archive(self):
        self.write(rec(key="ok"), "{not json")
        rep = memory.consolidate(today=D)
        self.assertEqual(rep["broken"], 1)
        self.assertIn("{not json", (paths.archive_dir() / "2026-10-05.jsonl").read_text())

    def test_dry_run_changes_nothing(self):
        self.write(rec(date="2026-10-01"), rec(date="2026-10-03"))
        before = paths.memory_file().read_text()
        memory.consolidate(today=D, dry_run=True)
        self.assertEqual(paths.memory_file().read_text(), before)

    def test_append_during_consolidate_is_kept(self):
        self.write(rec(key="a"))
        real = memory.replace_lines

        def racing(lines, since_size):
            with open(paths.memory_file(), "a", encoding="utf-8") as f:
                f.write(rec(key="late") + "\n")
            real(lines, since_size)

        memory.replace_lines = racing
        try:
            memory.consolidate(today=D)
        finally:
            memory.replace_lines = real
        self.assertIn(("correction", "late"), self.keys())

    def test_cli_consolidate_prints_report(self):
        self.write(rec())
        self.assertEqual(cli.main(["memory", "consolidate", "--dry-run"]), 0)
```

Note: `test_append_during_consolidate_is_kept` needs `consolidate` to call `replace_lines` through the module attribute (`replace_lines(...)` inside the module resolves at call time — keep it a plain module-level call).

Run → FAIL (`consolidate` missing)

- [ ] **Step 3: Implement in `memory.py`** (append)

```python
def _decay(r: dict, today: datetime.date) -> dict:
    c0 = r.get("confidence0", r.get("confidence", 0.5))
    try:
        age = (today - datetime.date.fromisoformat(str(r.get("date", ""))[:10])).days
    except ValueError:
        age = 0
    return {**r, "confidence0": c0, "confidence": round(c0 * 0.5 ** (max(age, 0) / 30), 3)}


def consolidate(today=None, dry_run: bool = False) -> dict:
    today = today or datetime.date.today()
    with lock():
        f = paths.memory_file()
        size = f.stat().st_size if f.exists() else 0
        lines = read_lines()
        recs = parse(lines)
        rep = {"before": len(lines), "after": 0, "merged": 0, "superseded": [], "decayed": [], "dropped": [],
               "promoted": [], "patch_suggestions": [], "broken": len([l for l in lines if l.strip()]) - len(recs)}
        latest: dict[tuple, dict] = {}
        for r in recs:
            k = (r.get("type"), r.get("key"), r.get("insight"), r.get("source"))
            if k in latest:
                rep["merged"] += 1
                if str(r.get("date", "")) < str(latest[k].get("date", "")):
                    continue
            latest[k] = r
        recs = list(latest.values())
        told_date: dict[str, str] = {}
        for r in recs:
            if r.get("source") == "told":
                told_date[r["key"]] = max(told_date.get(r["key"], ""), str(r.get("date", "")))
        out = []
        for r in recs:
            if r.get("source") == "observed":
                if r.get("key") in told_date and told_date[r["key"]] >= str(r.get("date", "")):
                    rep["superseded"].append(r["key"])
                    continue
                d = _decay(r, today)
                if d["confidence"] < 0.2:
                    rep["dropped"].append(r["key"])
                    continue
                if d["confidence"] != r.get("confidence"):
                    rep["decayed"].append([r["key"], d["confidence0"], d["confidence"]])
                r = d
            out.append(r)
        groups: dict[str, list[dict]] = {}
        for r in out:
            if r.get("type") == "correction":
                groups.setdefault(r["key"], []).append(r)
        promoted_keys = {r["key"] for r in out if r.get("type") == "preference" and "promoted_from" in r}
        for key, rs in sorted(groups.items()):
            if len(rs) < 3:
                continue
            rs.sort(key=lambda r: str(r.get("date", "")))
            if key.startswith("skill:"):
                rep["patch_suggestions"].append({"key": key, "count": len(rs), "insights": [r["insight"] for r in rs]})
            if key in promoted_keys:
                continue
            out.append({"type": "preference", "key": key, "insight": "규칙: " + " / ".join(r["insight"] for r in rs[-3:]),
                        "source": "told", "date": today.isoformat(), "host": paths.host(), "promoted_from": len(rs)})
            rep["promoted"].append(key)
        rep["after"] = len(out)
        if not dry_run:
            archive(today)
            replace_lines([_dump(r) for r in out], size)
        return rep
```

CLI — replace `_consolidate`:

```python
def _consolidate(args) -> int:
    print(json.dumps(memory.consolidate(dry_run=args.dry_run), ensure_ascii=False))
    return 0
```

- [ ] **Step 4: Run tests** → OK

- [ ] **Step 5: Commit**

```bash
git add lib/astack_cli/memory.py lib/astack_cli/cli.py tests/test_memory_ops.py
git commit -m "feat(memory): consolidate merges, supersedes, decays by age and promotes repeated corrections"
```

---

### Task 3: `astack dream collect`

**Files:**
- Create: `lib/astack_cli/dream.py`
- Modify: `lib/astack_cli/cli.py`
- Test: `tests/test_dream.py`

**Interfaces:**
- Consumes: `recall.recall(query="", project=None, since=None, limit=…) -> list[Item]` (`Item.path, skill, ts, title, description`)
- Produces: `dream.collect(day: date, items=None) -> dict`
  `{"date": "YYYY-MM-DD", "weekly": bool, "today": [entry…], "spaced": [{"days_ago": 1|7|30, **entry}…], "week": [entry…]}`, entry = `{"path", "skill", "title", "description", "ts"}`. `weekly`는 일요일. `week`는 weekly일 때만 지난 7일(오늘 포함). 간격 복습은 그날 이해물 중 가장 늦게 만든 것 하나. 없는 날은 건너뛴다. dream·feed 자신의 결과(`skill in {"dream","feed"}`)는 오늘 목록·복습에서 뺀다.
- CLI: `astack dream collect [--date YYYY-MM-DD]` → JSON 한 줄.

- [ ] **Step 1: Failing tests** — `tests/test_dream.py`

```python
import datetime
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli, dream  # noqa: E402
from astack_cli.recall import Item  # noqa: E402

D = datetime.date(2026, 10, 4)  # 일요일


def item(day: str, skill="spec", hour="10"):
    return Item(Path(f"/x/{skill}-{day}-{hour}.html"), skill, f"{day}T{hour}:00:00+09:00", f"t {day}", f"d {day}", 0)


class DreamTest(unittest.TestCase):
    def test_today_and_spaced(self):
        items = [item("2026-10-04"), item("2026-10-04", "change", "15"), item("2026-10-03"), item("2026-09-27"), item("2026-09-04")]
        got = dream.collect(D, items=items)
        self.assertEqual(len(got["today"]), 2)
        self.assertEqual([s["days_ago"] for s in got["spaced"]], [1, 7, 30])

    def test_spaced_picks_latest_of_that_day(self):
        got = dream.collect(D, items=[item("2026-10-03", hour="09"), item("2026-10-03", "change", "18")])
        self.assertEqual(got["spaced"][0]["skill"], "change")

    def test_spaced_review_skips_missing_days(self):
        got = dream.collect(D, items=[item("2026-09-27")])
        self.assertEqual([s["days_ago"] for s in got["spaced"]], [7])

    def test_weekly_on_sunday_only(self):
        items = [item("2026-09-28"), item("2026-10-04"), item("2026-09-27")]
        self.assertEqual(len(dream.collect(D, items=items)["week"]), 2)
        self.assertFalse(dream.collect(datetime.date(2026, 10, 5), items=items)["weekly"])

    def test_own_outputs_are_excluded(self):
        got = dream.collect(D, items=[item("2026-10-04", "dream"), item("2026-10-04", "feed")])
        self.assertEqual(got["today"], [])

    def test_cli(self):
        self.assertEqual(cli.main(["dream", "collect", "--date", "2026-10-04"]), 0)
        self.assertEqual(cli.main(["dream", "collect", "--date", "어제"]), 2)


if __name__ == "__main__":
    unittest.main()
```

Run → FAIL

- [ ] **Step 2: `lib/astack_cli/dream.py`**

```python
"""dream 재료 모으기: 오늘 생긴 이해물, 간격 복습(1·7·30일 전), 주간 모음. 상태 없이 날짜로만 고른다."""
import datetime

from . import recall

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
```

- [ ] **Step 3: CLI** — `from . import dream as _dream`, add:

```python
def _cmd_dream(args) -> int:
    try:
        day = datetime.date.fromisoformat(args.date) if args.date else datetime.date.today()
    except ValueError:
        print(f"astack dream: 날짜는 YYYY-MM-DD: {args.date}", file=sys.stderr)
        return 2
    print(json.dumps(_dream.collect(day), ensure_ascii=False))
    return 0
```

```python
    dr = sub.add_parser("dream", help="dream 재료 모으기")
    dr.add_argument("action", choices=["collect"])
    dr.add_argument("--date")
    dr.set_defaults(fn=_cmd_dream)
```

(`import datetime` at top of cli.py if absent.)

- [ ] **Step 4: Run tests** → OK

- [ ] **Step 5: Commit**

```bash
git add lib/astack_cli/dream.py lib/astack_cli/cli.py tests/test_dream.py
git commit -m "feat(cli): astack dream collect gathers today, spaced review and weekly items"
```

---

### Task 4: `astack:dream` 스킬과 Journal 템플릿

**Files:**
- Create: `skills/dream/SKILL.md`, `skills/dream/assets/template.html`
- Modify: `tests/test_templates.py` (집합에 `dream`)

**결정(사용자 확인 필요):** 승인된 Journal 템플릿이 없다(C6). 키트로 시작하고 첫 Journal로 확정한다.

- [ ] **Step 1: Failing test** — 집합에 `"dream"`, 추가:

```python
    def test_dream_template_sections(self):
        html = (ROOT / "skills/dream/assets/template.html").read_text(encoding="utf-8")
        for s in ('id="themes"', 'id="clash"', 'id="questions"', 'id="review"', 'id="mywords"', 'id="weekly"', 'class="quiz"'):
            self.assertIn(s, html)
```

- [ ] **Step 2: `skills/dream/assets/template.html`**

```html
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="description" content="[날짜] 하루 정리: [오늘의 공통 주제 한 줄]">
<meta name="rooms:created" content="[RFC3339 지금 시각]">
<meta name="rooms:machine" content="[머신 이름]">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>[날짜] Journal</title>
<!--astack:css-->
</head><body data-depth="all">
<div class="top"><div class="top-in"><span class="mark">Journal <span>dream</span></span><span class="where" id="where"></span><span class="sp"></span></div><div class="prog" id="prog"></div></div>
<div class="wrap">
<header class="cover" data-astack="30s">
  <div class="kick">Dream · [날짜] · 이해물 [N]개</div>
  <h1>[오늘을 한 문장으로]</h1>
  <div class="meta">dream · [날짜] · [읽는 시간]분</div>
  <p class="l30">[오늘 생긴 이해들이 어디로 모이나 두 줄]</p>
</header>
<section class="overview" data-astack="3m">
  <div><div class="kick">3분 · 오늘의 연결</div><p>[이해물 사이 연결 두세 줄]</p></div>
  <div>[오늘 이해물 관계 그림 SVG]</div>
</section>
<section id="themes"><div class="secHead"><div class="n">1</div><h2>공통 주제</h2></div>
  <ul><li><b>[주제]</b> — [어떤 이해물들에서, 무엇이 겹치나] <a href="[경로]">[이해물]</a></li></ul></section>
<section id="clash"><div class="secHead"><div class="n">2</div><h2>부딪히는 주장</h2></div>
  <ul><li>[A] vs [B] — [왜 다른가]</li></ul></section>
<section id="questions"><div class="secHead"><div class="n">3</div><h2>새로 생긴 질문</h2></div>
  <p class="sinlead">21:00 "오늘 밤 돌릴 질문" 후보.</p>
  <ol><li>[질문] — [어디서 나왔나]</li></ol></section>
<section id="review"><div class="secHead"><div class="n">4</div><h2>간격 복습</h2></div>
  <details class="quiz" data-kind="short"><summary>점검 · [N]일 전 · [이해물 제목]</summary><p class="q">[그 이해물의 핵심을 묻는 이해형 질문]</p><p class="ans">[답] · <a href="[경로]">다시 보기</a></p></details>
</section>
<section id="mywords"><div class="secHead"><div class="n">5</div><h2>내 말로 한 줄</h2></div>
  <p>[오늘 가장 중요한 이해물] 을(를) 한 줄로 설명한다면? 답은 Rooms Journal의 "나" 노트에 적는다.</p></section>
<section id="weekly"><div class="secHead"><div class="n">주간</div><h2>이번 주 수렴</h2></div>
  <p>[일요일에만 채운다. 아니면 이 섹션을 지운다]</p>
  <ul><li><b>이번 주 map 변화.</b> [방: 무엇이 바뀌었나]</li></ul>
  <ol><li>[이번 주 내 일에 쓸 것 1]</li><li>[2]</li><li>[3]</li></ol></section>
<footer data-astack="source">오늘 이해물 [N]개 (outputs.log) · Claude Code가 썼습니다</footer>
</div>
<!--astack:js-->
</body></html>
```

- [ ] **Step 3: `skills/dream/SKILL.md`**

````markdown
---
name: dream
description: Use when 하루를 마무리하며 오늘 생긴 이해물을 엮을 때 — 저녁 스케줄(20:00)이나 사용자가 "오늘 정리", "하루 정리", "dream"이라고 할 때. 일요일에는 주간 수렴까지.
---

# astack dream — 사람을 위한 저녁 정리

**약속:** 오늘 읽은 것들이 한 장으로 엮이고, 며칠 전 것도 한 문항씩 다시 떠올린다. 일요일에는 이번 주 내 일에 쓸 것 3가지로 좁혀진다.

먼저 `astack:design`을 읽는다. Rooms 없이 동작한다.

## 워크플로
1. `astack dream collect` → `today`, `spaced`, `weekly`, `week`.
2. 오늘 이해물이 0개면 Journal을 만들지 않고 "오늘 쌓인 이해물이 없습니다" 한 줄로 끝낸다.
3. 오늘 이해물을 읽는다(각 파일의 30초·3분 층과 "그래서 나한테는?").
4. `assets/template.html`을 채운다:
   - 공통 주제: 둘 이상 이해물에 겹치는 것만.
   - 부딪히는 주장: 왜 다른지(조건, 시점, 정의).
   - 새 질문: 오늘 이해물에서 나온 "남은 질문" → 21:00 후보.
   - 간격 복습: `spaced` 항목마다 짧은 점검 하나(이해형, 답 + 다시 보기 링크).
   - 내 말로 한 줄: 오늘 가장 중요한 이해물 하나.
   - `weekly`면 주간 수렴: 이번 주 방별 `map.html` 변화(있으면 `astack:map`으로 갱신 먼저) + `week` 이해물의 "그래서 나한테는?"을 모아 행동 3가지로 좁힌다(converge). 아니면 주간 섹션을 지운다.
5. 저장: `~/.astack/journal/<날짜>.html` → 메타 → `astack inline` → `astack check` → `astack done <f> --skill dream`. `rooms`가 있으면 `rooms link --journal <날짜> <f>`.
6. 관심 변화가 보이면 관찰만 남긴다: `astack memory add '{"type":"taste","key":"topic:<주제>","insight":"<무엇이 어떻게 바뀌었나>","confidence":0.6,"source":"observed"}'`. consolidate는 하지 않는다(그건 20:30 memory 몫).
7. 알림: 30초 층 두 줄 + 경로.

## 완료 전 체크
- [ ] 오늘 이해물 모두가 어딘가에 링크되어 있다
- [ ] 간격 복습 문항이 암기가 아니라 이해를 묻는다
- [ ] 주간 섹션은 일요일에만
- [ ] `astack check` 에러 0

## Gotchas
- dream·feed 자신의 결과는 collect가 이미 뺀다. Journal이 Journal을 엮지 않게.
- 이 머신에서 만든 이해물만 본다(v1 한계).
- **템플릿은 잠정이다.** 첫 Journal을 사용자에게 보여 확정한다(C6).
````

- [ ] **Step 4: Run tests and commit**

```bash
python3 -m unittest discover -s tests
git add skills/dream tests/test_templates.py
git commit -m "feat(skills): dream journal with spaced review, my-words line and weekly converge"
```

---

### Task 5: `astack feed seed|candidates`

**Files:**
- Create: `lib/astack_cli/feed.py`
- Modify: `lib/astack_cli/cli.py`
- Test: `tests/test_feed.py`

**Interfaces:**
- Consumes: `memory.add`, `memory.search`, `media.MediaError`, `paths.outputs_log`
- Produces:
  - `feed.YT_ID` 정규식(`(?:v=|youtu\.be/|/shorts/|/live/)([\w-]{11})`)
  - `feed.whitelist() -> list[dict]` (`{"name", "url"}`; `type=whitelist`, key `feed:youtube:<name>`, insight 안의 첫 `https://www.youtube.com/...` URL. `type=exclude`, key `channel:<name>`이 있으면 뺀다)
  - `feed.seed(name: str, url: str) -> bool` (이미 있으면 False, 없으면 told whitelist 기록을 더하고 True)
  - `feed.seen_ids() -> set[str]` (outputs.log의 파일들 본문에서 YouTube ID)
  - `feed.latest(url: str, limit: int = 5, runner=subprocess.run) -> list[dict]` (`yt-dlp --flat-playlist --playlist-end N -J <url>/videos`, `{"id","title","url","duration","upload_date"}`)
  - `feed.candidates(since: str | None = None, per_channel: int = 5, runner=subprocess.run) -> list[dict]` (채널 이름 포함, 이미 본 ID와 `since`보다 오래된 것 제외, 최신순)
  - CLI `astack feed seed "<이름>" <채널 URL>`, `astack feed candidates [--since D] [--per-channel N]` → JSON 줄.

- [ ] **Step 1: Failing tests** — `tests/test_feed.py`

```python
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli, feed, memory, paths  # noqa: E402

PLAYLIST = {"entries": [
    {"id": "AAAAAAAAAAA", "title": "new", "duration": 3600, "upload_date": "20261004"},
    {"id": "BBBBBBBBBBB", "title": "seen", "duration": 1200, "upload_date": "20261003"},
    {"id": "CCCCCCCCCCC", "title": "old", "duration": 600, "upload_date": "20260901"},
]}


class R:
    def __init__(self, out, code=0):
        self.stdout, self.returncode, self.stderr = out, code, ""


class FeedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get("ASTACK_HOME")
        os.environ["ASTACK_HOME"] = self.tmp.name

    def tearDown(self):
        if self.old is None:
            os.environ.pop("ASTACK_HOME", None)
        else:
            os.environ["ASTACK_HOME"] = self.old
        self.tmp.cleanup()

    def test_seed_is_idempotent_and_whitelist_reads_url(self):
        self.assertTrue(feed.seed("Latent Space", "https://www.youtube.com/@LatentSpacePod"))
        self.assertFalse(feed.seed("Latent Space", "https://www.youtube.com/@LatentSpacePod"))
        self.assertEqual(feed.whitelist(), [{"name": "Latent Space", "url": "https://www.youtube.com/@LatentSpacePod"}])

    def test_exclude_removes_channel(self):
        feed.seed("X", "https://www.youtube.com/@x")
        memory.add('{"type":"exclude","key":"channel:X","insight":"feed에서 제외","source":"told"}')
        self.assertEqual(feed.whitelist(), [])

    def test_seen_ids_from_short_links(self):
        doc = Path(self.tmp.name) / "a.html"
        doc.write_text('<a href="https://youtu.be/BBBBBBBBBBB?t=3">원본</a>', encoding="utf-8")
        paths.outputs_log().write_text(f"2026-10-04T10:00:00+09:00\tinterview\t{doc}\n", encoding="utf-8")
        self.assertEqual(feed.seen_ids(), {"BBBBBBBBBBB"})

    def test_candidates_skip_seen_and_old(self):
        feed.seed("C", "https://www.youtube.com/@c")
        doc = Path(self.tmp.name) / "a.html"
        doc.write_text("https://www.youtube.com/watch?v=BBBBBBBBBBB", encoding="utf-8")
        paths.outputs_log().write_text(f"2026-10-04T10:00:00+09:00\tinterview\t{doc}\n", encoding="utf-8")
        calls = []

        def runner(cmd, **kw):
            calls.append(cmd)
            return R(json.dumps(PLAYLIST))

        got = feed.candidates(since="2026-10-01", runner=runner)
        self.assertEqual([c["id"] for c in got], ["AAAAAAAAAAA"])
        self.assertEqual(got[0]["channel"], "C")
        self.assertTrue(calls[0][-1].endswith("/@c/videos"))

    def test_channel_failure_skips_that_channel(self):
        feed.seed("Bad", "https://www.youtube.com/@bad")
        self.assertEqual(feed.candidates(runner=lambda cmd, **kw: R("", 1)), [])

    def test_cli(self):
        self.assertEqual(cli.main(["feed", "seed", "Y", "https://www.youtube.com/@y"]), 0)
        self.assertEqual(cli.main(["feed", "seed", "Z", "not-a-url"]), 2)


if __name__ == "__main__":
    unittest.main()
```

Run → FAIL

- [ ] **Step 2: `lib/astack_cli/feed.py`**

```python
"""feed 재료: 화이트리스트 채널(memory의 told 기록)의 새 영상 중 아직 이해물이 없는 것."""
import json
import re
import subprocess
from pathlib import Path

from . import memory, paths
from .media import MediaError

YT_ID = re.compile(r"(?:v=|youtu\.be/|/shorts/|/live/)([\w-]{11})")
CHANNEL_URL = re.compile(r"https://www\.youtube\.com/[^\s\"']+")
PREFIX = "feed:youtube:"


def whitelist() -> list[dict]:
    excluded = {r["key"][len("channel:"):] for r in memory.search("channel:") if r.get("type") == "exclude"}
    out, names = [], set()
    for r in memory.search(PREFIX):
        if r.get("type") != "whitelist":
            continue
        name = r["key"][len(PREFIX):]
        m = CHANNEL_URL.search(str(r.get("insight", "")))
        if not m or name in excluded or name in names:
            continue
        names.add(name)
        out.append({"name": name, "url": m.group(0).rstrip("/")})
    return out


def seed(name: str, url: str) -> bool:
    if not CHANNEL_URL.fullmatch(url.rstrip("/")):
        raise ValueError(f"YouTube 채널 URL이 아닙니다: {url}")
    if any(w["name"] == name for w in whitelist()):
        return False
    memory.add(json.dumps({"type": "whitelist", "key": PREFIX + name, "insight": f"아침 feed 화이트리스트 {url.rstrip('/')}",
                           "source": "told"}, ensure_ascii=False))
    return True


def seen_ids() -> set[str]:
    log = paths.outputs_log()
    ids: set[str] = set()
    if not log.exists():
        return ids
    for line in log.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        p = Path(parts[2])
        if p.is_file():
            ids |= set(YT_ID.findall(p.read_text(encoding="utf-8", errors="ignore")))
    return ids


def latest(url: str, limit: int = 5, runner=subprocess.run) -> list[dict]:
    cmd = ["yt-dlp", "--flat-playlist", "--playlist-end", str(limit), "--extractor-args",
           "youtubetab:approximate_date", "-J", url.rstrip("/") + "/videos"]
    try:
        r = runner(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        raise MediaError("yt-dlp가 없습니다. `brew install yt-dlp`")
    if r.returncode != 0:
        raise MediaError(f"채널을 읽지 못했습니다: {url}")
    out = []
    for e in json.loads(r.stdout or "{}").get("entries", []) or []:
        if e.get("id"):
            out.append({"id": e["id"], "title": e.get("title", ""), "url": f"https://www.youtube.com/watch?v={e['id']}",
                        "duration": e.get("duration") or 0, "upload_date": e.get("upload_date") or ""})
    return out


def candidates(since: str | None = None, per_channel: int = 5, runner=subprocess.run) -> list[dict]:
    seen = seen_ids()
    cut = (since or "").replace("-", "")
    out = []
    for ch in whitelist():
        try:
            vids = latest(ch["url"], per_channel, runner)
        except MediaError:
            continue
        for v in vids:
            if v["id"] in seen or (cut and v["upload_date"] and v["upload_date"] < cut):
                continue
            out.append({**v, "channel": ch["name"]})
    out.sort(key=lambda v: v["upload_date"], reverse=True)
    return out
```

- [ ] **Step 3: CLI** — `from . import feed as _feed`, add:

```python
def _cmd_feed(args) -> int:
    try:
        if args.action == "seed":
            if len(args.rest) != 2:
                raise ValueError('사용법: astack feed seed "<이름>" <채널 URL>')
            print("추가함" if _feed.seed(*args.rest) else "이미 있음")
        else:
            for c in _feed.candidates(since=args.since, per_channel=args.per_channel):
                print(json.dumps(c, ensure_ascii=False))
    except (ValueError, _media.MediaError, memory.InvalidRecord) as e:
        print(f"astack feed: {e}", file=sys.stderr)
        return 2
    return 0
```

```python
    fe = sub.add_parser("feed", help="화이트리스트 채널(seed)과 오늘 후보(candidates)")
    fe.add_argument("action", choices=["seed", "candidates"])
    fe.add_argument("rest", nargs="*")
    fe.add_argument("--since")
    fe.add_argument("--per-channel", type=int, default=5)
    fe.set_defaults(fn=_cmd_feed)
```

- [ ] **Step 4: Run tests** → OK

- [ ] **Step 5: Commit**

```bash
git add lib/astack_cli/feed.py lib/astack_cli/cli.py tests/test_feed.py
git commit -m "feat(cli): astack feed seeds whitelist in memory and lists unseen new videos"
```

---

### Task 6: `astack:feed` 스킬과 "오늘 30분" 템플릿

**Files:**
- Create: `skills/feed/SKILL.md`, `skills/feed/assets/template.html`
- Modify: `tests/test_templates.py` (집합에 `feed`)

**결정(사용자 확인 필요):** 승인된 템플릿 없음(C6). 깊은 매거진은 interview 원자의 결과물 링크, 짧은 카드는 이 템플릿 안의 3분 층.

- [ ] **Step 1: Failing test** — 집합에 `"feed"`, 추가:

```python
    def test_feed_template_has_order_and_cards(self):
        html = (ROOT / "skills/feed/assets/template.html").read_text(encoding="utf-8")
        for s in ('id="deep"', 'id="cards"', 'class="card"', "읽는 순서"):
            self.assertIn(s, html)
```

- [ ] **Step 2: `skills/feed/assets/template.html`**

```html
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="description" content="[날짜] 오늘 30분: [가장 중요한 한 편]">
<meta name="rooms:created" content="[RFC3339 지금 시각]">
<meta name="rooms:machine" content="[머신 이름]">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>[날짜] 오늘 30분</title>
<!--astack:css-->
</head><body data-depth="all">
<div class="top"><div class="top-in"><span class="mark">오늘 30분 <span>feed</span></span><span class="where" id="where"></span><span class="sp"></span></div><div class="prog" id="prog"></div></div>
<div class="wrap">
<header class="cover" data-astack="30s">
  <div class="kick">Feed · [날짜] · [N]편 · 30분</div>
  <h1>[오늘 가장 읽을 만한 것 한 문장]</h1>
  <div class="meta">feed · [날짜] · 30분</div>
  <p class="l30">[왜 이 순서인가 두 줄]</p>
</header>
<section class="overview" data-astack="3m">
  <div><div class="kick">3분 · 읽는 순서</div>
    <ol><li><a href="#deep">[깊게 1] — [채널] · 약 [분]분</a></li><li><a href="#c1">[카드 1] — 3분</a></li></ol></div>
  <div>[오늘 편들의 주제 지도 SVG, 없으면 비운다]</div>
</section>
<section id="deep"><div class="secHead"><div class="n">깊게</div><h2>매거진</h2></div>
  <div class="card"><h3>[제목]</h3><p class="meta">[채널] · [영상 길이] · 읽는 시간 [분]분</p><p>[30초 요지 두 줄]</p><p><a href="[interview 이해물 경로]">매거진 열기</a> · <a href="[원본 URL]">원본 영상</a></p></div>
</section>
<section id="cards"><div class="secHead"><div class="n">짧게</div><h2>3분 카드</h2></div>
  <div class="card" id="c1"><h3>[제목]</h3><p class="meta">[채널] · <a href="[원본 URL]">원본 영상</a></p><ul><li>[핵심 1]</li><li>[핵심 2]</li><li>[핵심 3]</li></ul><p><b>그래서 나한테는?</b> [한 줄]</p></div>
</section>
<footer data-astack="source">화이트리스트 채널 [N]개 · 후보 [M]개 중 [K]편 · Claude Code가 썼습니다</footer>
</div>
<!--astack:js-->
</body></html>
```

Add to `alto-ext.css` (if `.card` is not already in `alto.css` — check with `grep -n '\.card{' skills/design/assets/alto.css` first):

```css
.card{border:1px solid var(--hairline);border-radius:14px;padding:14px 16px;margin:12px 0;background:var(--canvas)}
.card h3{margin:0 0 4px;font-weight:500}
.card .meta{margin:0 0 8px}
```

- [ ] **Step 3: `skills/feed/SKILL.md`**

````markdown
---
name: feed
description: Use when 아침 스케줄(05:00)에 "오늘 30분"을 만들 때, 또는 사용자가 "오늘 볼 거", "feed", "아침 30분"을 요청할 때. 화이트리스트 채널 추가·제외 요청("이 채널 feed에 넣어줘", "X는 빼줘")에도.
---

# astack feed — 아침 30분

**약속:** 아침에 30분짜리 한 장만 받는다. 밀린 목록은 없다.

먼저 `astack:design`을 읽고 `astack memory search feed:`, `astack memory search channel:`로 화이트리스트·제외·피드백을 본다.

## 화이트리스트 관리
- 추가: `astack feed seed "<채널 이름>" https://www.youtube.com/@<handle>`. 채널 URL을 모르면 `yt-dlp "ytsearch1:<채널 이름> podcast" --print channel_url`로 찾고 사용자에게 한 줄로 알린다.
- 제외: `astack memory add '{"type":"exclude","key":"channel:<이름>","insight":"feed에서 제외","source":"told"}'`.
- 화이트리스트는 기억(`~/.astack/memory.jsonl`)에만 있다. 레포에 쓰지 않는다.

## 워크플로
1. `astack feed candidates --since <지난 실행 날짜, 모르면 어제>`.
2. 고르기(30분 분량): 깊게 1~2편(합쳐 ~20분 읽기) + 3분 카드 2~3편. 기준은 취향 — 최근 이해물 주제(`astack recall --since <2주 전> --json`), 기억의 feedback("2번 별로: 너무 입문용")·taste. 나머지는 만들지 않는다.
3. 깊게: 편마다 `astack:interview`(슬라이드 발표면 `astack:seminar`)로 매거진을 만든다.
4. 카드: `astack transcript <url>`로 자막을 읽고 핵심 3줄 + "그래서 나한테는?" 한 줄.
5. `assets/template.html`을 읽는 순서대로 채운다. 모든 편에 원본 URL이 본문에 있어야 한다(다음 feed의 중복 판단에 쓰인다).
6. 저장 `~/.astack/journal/<날짜>-feed.html` → 메타 → `astack inline` → `astack check` → `astack done <f> --skill feed`.
7. 사용자가 "2번 별로" 같은 답을 주면: `astack memory add '{"type":"feedback","key":"feed:<날짜>#2","insight":"별로: <이유>","source":"told"}'`.

## 완료 전 체크
- [ ] 전체 읽는 시간 30분 이내
- [ ] 편마다 원본 URL이 본문에 있다
- [ ] 제외 채널이 없다
- [ ] `astack check` 에러 0

## Gotchas
- 채널 영상 목록의 날짜는 근사값이다(`approximate_date`). 하루 차이는 무시한다.
- 후보가 0개면 만들지 않고 "오늘 새 영상 없음" 한 줄.
- **템플릿은 잠정이다.** 첫 feed를 사용자에게 보여 확정한다(C6).
````

- [ ] **Step 4: Run tests and commit**

```bash
python3 -m unittest discover -s tests
git add skills/feed skills/design/assets/alto-ext.css tests/test_templates.py
git commit -m "feat(skills): feed builds a 30-minute morning page from the whitelist"
```

---

### Task 7: 문서와 실제 실행 (§15 P4 완료 기준)

**Files:**
- Modify: `skills/design/SKILL.md` (기억 절), `README.md`, `skills/design/references/capabilities.md`
- Create: `docs/superpowers/plans/2026-10-05-astack-p4-dogfood.md`

- [ ] **Step 1: `skills/design/SKILL.md`** — `## 시작할 때` 아래에 추가:

```markdown
## 기억 정리 (에이전트용, 저녁 20:30)
- `astack memory consolidate` — 중복 합치기, 최신 told가 오래된 observed를 대체, observed는 나이로 감쇠(30일 반감), 같은 교정 3번이면 규칙으로 승격, `skill:` 교정 반복은 레포 패치 **제안만**. 직전 상태는 `~/.astack/archive/<날짜>.jsonl`.
- 되돌리기: `astack memory restore <날짜>`. 지우기: `astack memory prune --key <접두사>`.
- 사람용 dream과 따로 돈다. 둘이 만나는 곳은 `memory add` 한 줄뿐.
```

- [ ] **Step 2: README** — English, very short. Add rows to `## Skills`:

```markdown
| `dream` | Today's pages | An evening journal with spaced review |
| `feed` | Your channel whitelist | A 30-minute morning page |
```

CLI line adds `dream | feed`. Add one line: `Scheduling (cron, Telegram) comes with host recipes.`

- [ ] **Step 3: capabilities.md** — 표 끝에:

```markdown
| dream-collect | `astack dream collect [--date D]` | 같음 | 상태 없음, 날짜로 고름 |
| feed | `astack feed seed|candidates` | YouTube 구독은 `aside` CLI로 위임 | 화이트리스트는 memory에만 |
| memory-maintain | `astack memory prune|consolidate|restore` | 같음 | `.lock`은 consolidate 중에만 |
```

- [ ] **Step 4: Commit docs**

```bash
python3 -m unittest discover -s tests
git add skills/design README.md
git commit -m "docs: memory maintenance, dream and feed for P4"
```

- [ ] **Step 5: 실제 실행** (결과물은 `~/.astack/journal/`, 레포 밖)
  1. 화이트리스트 seed: AI Engineer, Lenny's Podcast, Dialectic (Jackson Dahl), David Senra, Invest Like The Best, Y Combinator, Uncapped (Jack Altman), The Pragmatic Engineer, Latent Space. 채널 URL은 `yt-dlp "ytsearch1:<이름>" --print channel_url`로 찾고 눈으로 확인. 레포에 쓰지 않는다.
  2. `astack:feed` 한 번(깊게 1편 + 카드 2편).
  3. `astack:dream` 한 번(오늘 날짜). Rooms 없이.
  4. `astack memory consolidate --dry-run` → 보고서 확인 → 실제 실행 → `astack memory restore <오늘>`로 되돌리기가 되는지 확인 → 다시 consolidate.
  5. `docs/superpowers/plans/2026-10-05-astack-p4-dogfood.md`에 결과를 적고 커밋.

## 기본값과 열린 결정

| 항목 | 기본값 | 근거 | 확인 |
|---|---|---|---|
| dream·feed 템플릿 | Alto 키트 | 승인 템플릿 없음(C6) | 첫 결과물로 확정 |
| Journal 위치 | `~/.astack/journal/` | 프로젝트에 속하지 않음 | Rooms 연동 시 재검토 |
| observed 감쇠 | 30일 반감, 0.2 미만 삭제 | 스펙은 "감쇠"만 명시 | 2주 운영 후 조정 |
| 승격 기준 | 같은 key 교정 3번 | 스펙은 "N회" | 운영 후 조정 |
| consolidate 변경 보고 HTML | v1은 JSON 보고서만 | P5 Hermes 레시피가 알림으로 만든다 | |
| 스케줄·Telegram | P5 | 호스트 몫 | |
