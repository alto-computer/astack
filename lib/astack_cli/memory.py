import contextlib
import datetime
import json
import os
import shutil
import time
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
    for line in f.read_text(encoding="utf-8").splitlines():
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
    parts = data.decode("utf-8", "replace").split("\n")
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


def _write_atomic(target: Path, data: bytes) -> None:
    tmp = target.with_name(target.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    os.chmod(tmp, 0o600)
    os.replace(tmp, target)


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


def replace_lines(lines: list[str], since_size: int) -> None:
    body = "".join(l + "\n" for l in lines).encode("utf-8")
    _write_atomic(paths.memory_file(), body + _tail(since_size))


def _dump(r: dict) -> str:
    return json.dumps(r, ensure_ascii=False, separators=(",", ":"))


def prune(key: str | None = None, type_: str | None = None, before: str | None = None, today=None) -> int:
    if not (key or type_ or before):
        raise ValueError("--key, --type, --before 중 하나는 있어야 합니다")
    today = today or datetime.date.today()
    with lock():
        f = paths.memory_file()
        data, lines = _snapshot()
        size = len(data)
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
    datetime.date.fromisoformat(date)  # archive 밖으로 못 나가게
    a = paths.archive_dir() / f"{date}.jsonl"
    if not a.exists():
        raise FileNotFoundError(f"archive가 없습니다: {a}")
    today = today or datetime.date.today()
    with lock():
        data, _ = _snapshot()
        if data:  # 현재 상태의 유일한 사본을 잃지 않게 늘 안전 사본을 남긴다
            stamp = datetime.datetime.now().strftime("%H%M%S")
            paths.archive_dir().mkdir(parents=True, exist_ok=True)
            _write_atomic(paths.archive_dir() / f"{today.isoformat()}.pre-restore-{stamp}.jsonl", data)
        _write_atomic(paths.memory_file(), a.read_bytes() + _tail(len(data)))
    return a
