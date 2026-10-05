import datetime
import shutil
import subprocess
from pathlib import Path

from . import check, paths


def done(path, skill: str, room: str | None = None, force: bool = False,
         now: datetime.datetime | None = None) -> tuple[int, list[str]]:
    p = Path(path).resolve()
    # Validate skill and path don't contain tab/newline
    if any(c in skill for c in "\t\n\r"):
        return 1, ["error: skill/path must not contain tab or newline"]
    if any(c in str(p) for c in "\t\n\r"):
        return 1, ["error: skill/path must not contain tab or newline"]
    # Check if file exists
    if not p.is_file():
        return 1, [f"error: not a file: {p}"]
    errors = [i for i in check.check_file(p) if i.level == "error"]
    if errors and not force:
        return 1, [f"error {i.code}: {i.message}" for i in errors]
    log = paths.outputs_log()
    log.parent.mkdir(parents=True, exist_ok=True)
    ts = (now or datetime.datetime.now().astimezone()).isoformat(timespec="seconds")
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"{ts}\t{skill}\t{p}\n")
    notes: list[str] = []
    rooms = shutil.which("rooms")
    if rooms:
        cmd = [rooms, "link", str(p)] + (["--room", room] if room else [])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20,
                               stdin=subprocess.DEVNULL)
            if r.returncode != 0:
                notes.append(f"rooms link 실패({r.returncode}): {r.stderr.strip()[:200]}")
        except (OSError, subprocess.TimeoutExpired) as e:
            notes.append(f"rooms link 실패: {e}")
    return 0, notes
