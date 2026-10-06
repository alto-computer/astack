import contextlib
import datetime
import json
import os
import re
import shutil
import time
from html import escape as html_escape
from pathlib import Path

from . import paths

TYPES = {"whitelist", "exclude", "correction", "feedback", "taste", "preference"}
SOURCES = {"told", "observed"}
REQUIRED = ("type", "key", "insight", "source")


class InvalidRecord(ValueError):
    pass


def add(raw: str, host: str | None = None, today: datetime.date | None = None) -> dict:
    try:
        rec = json.loads(raw)
    except json.JSONDecodeError as e:
        raise InvalidRecord(f"JSON이 아닙니다: {e.msg}") from None
    if not isinstance(rec, dict):
        raise InvalidRecord("기록은 JSON 객체여야 합니다")
    missing = [k for k in REQUIRED if not str(rec.get(k, "")).strip()]
    if missing:
        raise InvalidRecord("빠진 칸: " + ", ".join(missing))
    if not isinstance(rec["type"], str):
        raise InvalidRecord("type은 텍스트여야 합니다")
    if not isinstance(rec["source"], str):
        raise InvalidRecord("source는 텍스트여야 합니다")
    if rec["type"] not in TYPES:
        raise InvalidRecord(f"모르는 type: {rec['type']} (가능: {', '.join(sorted(TYPES))})")
    if rec["source"] not in SOURCES:
        raise InvalidRecord(f"모르는 source: {rec['source']} (told | observed)")
    if "confidence" in rec:
        c = rec["confidence"]
        if not isinstance(c, (int, float)) or not 0 <= c <= 1:
            raise InvalidRecord("confidence는 0~1 숫자")
    rec["date"] = (today or datetime.date.today()).isoformat()
    rec["host"] = host or paths.host()
    line = (json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    f = paths.memory_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(100):  # consolidate 중이면 최대 5초 기다린다
        if not paths.lock_file().exists():
            break
        time.sleep(0.05)
    # O_APPEND + 한 번의 write: 짧은 한 줄은 다른 프로세스의 쓰기와 섞이지 않는다
    fd = os.open(f, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)
    return rec


def search(query: str) -> list[dict]:
    f = paths.memory_file()
    if not f.exists():
        return []
    out = []
    for line in _split(f.read_bytes()):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        if str(rec.get("key", "")).startswith(query) or query in str(rec.get("insight", "")):
            out.append(rec)
    return out


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


def _split(data: bytes) -> list[str]:
    # "\n"으로만 자른다. splitlines()는 U+2028 같은 문자에서도 잘라 기록을 깨뜨린다
    # surrogateescape: 손으로 고친 깨진 바이트도 다시 쓸 때 원래 바이트로 돌아간다
    parts = data.decode("utf-8", "surrogateescape").split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return parts


def _snapshot() -> tuple[bytes, list[str]]:
    f = paths.memory_file()
    data = f.read_bytes() if f.exists() else b""
    return data, _split(data)


def read_lines() -> list[str]:
    return _snapshot()[1]


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


def _live() -> Path:
    # 심볼릭 링크면 링크가 가리키는 실제 파일을 바꾼다. 링크 자체를 덮으면 동기화 레포와 끊긴다
    return Path(os.path.realpath(paths.memory_file()))


def _write_atomic(target: Path, data: bytes) -> None:
    tmp = target.with_name(target.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as fh:  # write()가 끝까지 쓴다. os.write 한 번은 일부만 쓸 수 있다
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.chmod(tmp, 0o600)
    os.replace(tmp, target)
    dfd = os.open(target.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def _tail(since_size: int) -> bytes:
    f = paths.memory_file()
    if not f.exists():
        return b""
    with open(f, "rb") as cur:
        cur.seek(since_size)
        return cur.read()  # 읽은 뒤에 add로 붙은 줄


def archive(today: datetime.date) -> Path:
    d = paths.archive_dir()
    d.mkdir(parents=True, exist_ok=True)
    a = d / f"{today.isoformat()}.jsonl"
    if not a.exists() and paths.memory_file().exists():
        _write_atomic(a, paths.memory_file().read_bytes())
    return a


def _stamp() -> str:
    return datetime.datetime.now().strftime("%H%M%S%f")


def snapshot_archive(today: datetime.date, data: bytes, tag: str = "") -> Path | None:
    """덮어쓰기 직전 스냅샷 바이트를 그대로 남긴다. 같은 날 두 번째부터는 시각이 붙은 새 파일.
    tag(pre-restore)가 있으면 늘 시각을 붙인다. 이미 있는 파일은 절대 덮지 않는다."""
    if not data:
        return None
    d = paths.archive_dir()
    d.mkdir(parents=True, exist_ok=True)
    a = None if tag else d / f"{today.isoformat()}.jsonl"
    while a is None or a.exists():
        a = d / f"{today.isoformat()}.{tag + '-' if tag else ''}{_stamp()}.jsonl"
    _write_atomic(a, data)
    return a


ARCHIVE_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})(\.\d+|\.pre-restore-\d+)?$")


def archives(date: str | None = None) -> list[str]:
    """archive 이름(restore에 넘기는 값), 최신 먼저."""
    d = paths.archive_dir()
    if not d.is_dir():
        return []
    found = []
    for p in d.glob("*.jsonl"):
        name = p.name[:-len(".jsonl")]
        m = ARCHIVE_NAME.fullmatch(name)
        if m and (date is None or m.group(1) == date):
            found.append((p.stat().st_mtime_ns, name))
    return [n for _, n in sorted(found, reverse=True)]


def replace_lines(lines: list[str], since_size: int) -> None:
    body = "".join(l + "\n" for l in lines).encode("utf-8", "surrogateescape")
    _write_atomic(_live(), body + _tail(since_size))


def _dump(r: dict) -> str:
    return json.dumps(r, ensure_ascii=False, separators=(",", ":"))


def prune(key: str | None = None, type_: str | None = None, before: str | None = None, today=None) -> int:
    if not (key or type_ or before):
        raise ValueError("--key, --type, --before 중 하나는 있어야 합니다")
    if type_ is not None and type_ not in TYPES:
        raise ValueError(f"모르는 type: {type_} (가능: {', '.join(sorted(TYPES))})")
    if before is not None and not _iso_date(before):
        raise ValueError(f"--before는 YYYY-MM-DD 날짜: {before}")
    today = today or datetime.date.today()
    with lock():
        data, lines = _snapshot()
        size = len(data)
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
                and (before is None or (_iso_date(r.get("date")) and r["date"] < before))
            if hit:
                removed += 1
            else:
                keep.append(line)
        if removed:
            snapshot_archive(today, data)
            replace_lines(keep, size)
        return removed


def _iso_date(v) -> bool:
    if not isinstance(v, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return False
    try:
        datetime.date.fromisoformat(v)
    except ValueError:
        return False
    return True


def restore(name: str, today=None) -> Path:
    """name: 날짜(그날 첫 상태) 또는 archives()의 이름(시각·pre-restore 스냅샷)."""
    if name.endswith(".jsonl"):
        name = name[:-len(".jsonl")]
    m = ARCHIVE_NAME.fullmatch(name)  # archive 밖으로 못 나가게
    if not m:
        raise ValueError(f"archive 이름이 아닙니다: {name} (YYYY-MM-DD 또는 --list의 이름)")
    datetime.date.fromisoformat(m.group(1))
    a = paths.archive_dir() / f"{name}.jsonl"
    if not a.exists():
        raise FileNotFoundError(f"archive가 없습니다: {a}")
    today = today or datetime.date.today()
    with lock():
        data, _ = _snapshot()
        # 현재 상태의 유일한 사본을 잃지 않게 늘 안전 사본을 남긴다
        snapshot_archive(today, data, tag="pre-restore")
        _write_atomic(_live(), a.read_bytes() + _tail(len(data)))
    return a


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _plain(r: dict) -> bool:
    return all(isinstance(r.get(k), str) and r.get(k) for k in REQUIRED)


def _decay(r: dict, today: datetime.date) -> dict:
    c0 = r.get("confidence0", r.get("confidence", 0.5))
    if not _num(c0) or ("confidence" in r and not _num(r["confidence"])):
        return r
    try:
        age = (today - datetime.date.fromisoformat(str(r.get("date", ""))[:10])).days
    except ValueError:
        age = 0
    return {**r, "confidence0": c0, "confidence": round(c0 * 0.5 ** (max(age, 0) / 30), 3)}


def _count(r: dict) -> int:
    c = r.get("count", 1)
    return c if isinstance(c, int) and not isinstance(c, bool) and c >= 1 else 1


def _unparsed(lines: list[str]) -> list[str]:
    return [l for l in lines if not parse([l])]


def consolidate(today=None, dry_run: bool = False) -> dict:
    today = today or datetime.date.today()
    with lock():
        data, lines = _snapshot()
        size = len(data)
        lines = [l for l in lines if l.strip()]
        recs = parse(lines)
        broken = _unparsed(lines)  # 읽을 수 없는 줄은 손대지 않고 그대로 남긴다
        rep = {"before": len(lines), "after": 0, "kept_unreadable": 0, "merged": 0, "superseded": [], "decayed": [], "dropped": [],
               "promoted": [], "patch_suggestions": [], "broken": len(broken)}
        odd = [r for r in recs if not _plain(r)]
        rep["kept_unreadable"] = len(odd)
        recs = [r for r in recs if _plain(r)]
        latest: dict[tuple, dict] = {}
        for r in recs:
            k = (r.get("type"), r.get("key"), r.get("insight"), r.get("source"))
            if k in latest:
                rep["merged"] += 1
                n = _count(latest[k]) + _count(r)  # 같은 교정이 몇 번 나왔는지는 합쳐도 남긴다
                if str(r.get("date", "")) < str(latest[k].get("date", "")):
                    r = latest[k]
                r = {**r, "count": n}
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
                if d is r:
                    out.append(r)
                    continue
                if d["confidence"] < 0.2:
                    rep["dropped"].append(r["key"])
                    continue
                if d["confidence"] != r.get("confidence"):
                    rep["decayed"].append([r["key"], d["confidence0"], d["confidence"]])
                r = d
            out.append(r)
        groups: dict[str, list[dict]] = {}
        for r in out:  # told만 센다. observed 교정은 사용자가 말한 게 아니라서 규칙이 되지 않는다
            if r.get("type") == "correction" and r.get("source") == "told":
                groups.setdefault(r["key"], []).append(r)
        promoted_keys = {r["key"] for r in out if r.get("type") == "preference" and "promoted_from" in r}
        for key, rs in sorted(groups.items()):
            n = sum(_count(r) for r in rs)
            if n < 3:
                continue
            rs.sort(key=lambda r: str(r.get("date", "")))
            insights = list(dict.fromkeys(r["insight"] for r in rs))
            if key.startswith("skill:"):
                rep["patch_suggestions"].append({"key": key, "count": n, "insights": insights})
            if key in promoted_keys:
                continue
            out.append({"type": "preference", "key": key, "insight": "규칙: " + " / ".join(insights[-3:]),
                        "source": "told", "date": today.isoformat(), "host": paths.host(), "promoted_from": n})
            rep["promoted"].append(key)
        out += odd
        rep["after"] = len(out) + len(broken)
        if not dry_run:
            snapshot_archive(today, data)
            replace_lines([_dump(r) for r in out] + broken, size)
        return rep


def changed(rep: dict) -> bool:
    return bool(rep["merged"] or rep["superseded"] or rep["decayed"] or rep["dropped"] or rep["promoted"]
                or rep["before"] != rep["after"])


def _li(items) -> str:
    return "<ul>" + "".join(f"<li>{html_escape(str(i))}</li>" for i in items) + "</ul>" if items else "<p>없음</p>"


def render_report(rep: dict, day: datetime.date, dry_run: bool = False) -> str:
    esc = html_escape
    if changed(rep):
        line = (f"기록 {rep['before']}→{rep['after']}, 합침 {rep['merged']}, 대체 {len(rep['superseded'])}, "
                f"감쇠 {len(rep['decayed'])}, 지움 {len(rep['dropped'])}, 승격 {len(rep['promoted'])}")
    else:
        line = "바뀐 것 없음"
    if dry_run:
        line = "미리보기 (적용 안 됨) · " + line
    patches = "".join(
        f"<li><b>{esc(p['key'])}</b> (교정 {p['count']}번): " + " / ".join(esc(i) for i in p["insights"]) + "</li>"
        for p in rep["patch_suggestions"])
    patch_html = f"<ul>{patches}</ul>" if patches else "<p>제안 없음</p>"
    decayed = [f"{k}: {a} → {b}" for k, a, b in rep["decayed"]]
    created = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="description" content="{esc(day.isoformat())} 기억 정리: {esc(line)}">
<meta name="rooms:created" content="{created}">
<meta name="rooms:machine" content="{esc(paths.host())}">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{day.isoformat()} 기억 정리</title>
<!--astack:css-->
</head><body>
<div class="wrap">
<header class="cover" data-astack="30s">
  <div class="kick">memory · {day.isoformat()}</div>
  <h1>기억 정리 보고</h1>
  <p class="l30">{esc(line)}</p>
</header>
<section data-astack="3m">
  <h2>승격</h2>
  {_li(rep['promoted'])}
  <h2>패치 제안</h2>
  <p>제안만 합니다. 스킬 파일은 자동 적용하지 않습니다. 직접 보고 고치세요.</p>
  {patch_html}
</section>
<section>
  <h2>대체된 기록</h2>
  {_li(rep['superseded'])}
  <h2>감쇠된 기록</h2>
  {_li(decayed)}
  <h2>지운 기록</h2>
  {_li(rep['dropped'])}
</section>
<footer data-astack="source">출처: memory.jsonl · 정리일 {day.isoformat()} · Claude Code가 썼습니다</footer>
</div>
</body></html>
"""
