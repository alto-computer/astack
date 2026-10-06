import datetime
import os
import shutil
import subprocess
from pathlib import Path

from . import check, paths


def _free_name(room_dir: Path, name: str) -> Path:
    link = room_dir / name
    if not os.path.lexists(link):
        return link
    stem, ext = os.path.splitext(name)
    n = 2
    while True:
        link = room_dir / f"{stem} ({n}){ext}"
        if not os.path.lexists(link):
            return link
        n += 1


def link_into_rooms(p: Path, room: str | None, home: Path) -> str:
    slug = room or "inbox"
    if (not slug or "/" in slug or "\\" in slug or ".." in slug
            or slug.startswith(".") or "\0" in slug):
        return f"rooms 링크 건너뜀: 방 이름이 올바르지 않음: {slug}"
    try:
        rhome = Path(os.path.realpath(home))
        rp = Path(os.path.realpath(p))
        if rp == rhome or rhome in rp.parents:
            return "rooms 링크 건너뜀: Home 안의 파일"
        if home.is_dir():
            for room_dir in sorted(home.iterdir()):
                if not room_dir.is_dir() or room_dir.is_symlink():
                    continue
                for f in sorted(room_dir.iterdir()):
                    if f.is_symlink() and Path(os.path.realpath(f)) == rp:
                        return f"rooms: 이미 연결됨 {f}"
        room_dir = home / slug
        room_dir.mkdir(parents=True, exist_ok=True)
        link = _free_name(room_dir, p.name)
        os.symlink(str(p), link)
        return f"rooms: {link}"
    except OSError as e:
        return f"rooms 링크 실패: {e}"


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
    elif (home := paths.rooms_home()) is not None:
        notes.append(link_into_rooms(p, room, home))
    else:
        notes.append("rooms 없음: 방 링크 건너뜀")
    return 0, notes
