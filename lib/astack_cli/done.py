import datetime
import shutil
import subprocess
from pathlib import Path

from . import check, paths


def done(path, skill: str, room: str | None = None, force: bool = False,
         now: datetime.datetime | None = None) -> tuple[int, list[str]]:
    p = Path(path).resolve()
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
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if r.returncode != 0:
                notes.append(f"rooms link 실패({r.returncode}): {r.stderr.strip()[:200]}")
        except (OSError, subprocess.TimeoutExpired) as e:
            notes.append(f"rooms link 실패: {e}")
    return 0, notes
