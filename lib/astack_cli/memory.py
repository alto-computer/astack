import datetime
import json
import os

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
