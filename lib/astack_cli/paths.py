import os
import socket
from pathlib import Path


def home() -> Path:
    return Path(os.environ.get("ASTACK_HOME") or (Path.home() / ".astack"))


def rooms_home() -> Path | None:
    env = os.environ.get("ASTACK_ROOMS_HOME")
    if env:
        h = Path(env)
        return h if h.is_dir() else None
    h = Path.home() / "rooms"
    return h if (h / ".rooms").is_dir() else None


def memory_file() -> Path:
    return home() / "memory.jsonl"


def outputs_log() -> Path:
    return home() / "outputs.log"


def roots_file() -> Path:
    return home() / "roots"


def host() -> str:
    return os.environ.get("ASTACK_HOST") or socket.gethostname().split(".")[0]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def archive_dir() -> Path:
    return home() / "archive"


def lock_file() -> Path:
    return home() / ".lock"


def journal_dir() -> Path:
    return home() / "journal"


def goals_dir() -> Path:
    return home() / "goals"
