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


def _read(file: Path) -> str:
    with open(file, encoding="utf-8", newline="") as f:
        return f.read()


def _write_atomic(file: Path, text: str) -> None:
    target = file.resolve() if file.is_symlink() else file
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.tmp-astack")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    if target.exists():
        shutil.copymode(target, tmp)
    os.replace(tmp, target)


def _marker_state(text: str) -> str:
    """none: 표식 없음. ok: 짝이 하나이고 순서가 맞음. broken: 그 외."""
    nb, ne = text.count(BEGIN), text.count(END)
    if nb == 0 and ne == 0:
        return "none"
    if nb == 1 and ne == 1 and text.index(END) > text.index(BEGIN):
        return "ok"
    return "broken"


def _put_snippet(file: Path, snippet: str, dry: bool, out: list[str]) -> None:
    text = _read(file) if file.exists() else ""
    state = _marker_state(text)
    if state == "broken":
        out.append(f"건너뜀: {file} (표식이 깨짐)")
        return
    inner = f"{BEGIN}\n{snippet.strip()}\n{END}"
    if state == "ok":
        a, rest = text.split(BEGIN, 1)
        _, b = rest.split(END, 1)
        new = a + inner + b
    elif not text:
        new = inner + "\n"
    elif text.endswith("\n"):
        new = text + "\n" + inner + "\n"
    else:
        new = text + "\n" + inner  # 끝 개행이 없던 파일은 끝 개행 없이 두어야 정확히 되돌아간다
    if new == text:
        out.append(f"그대로: {file}")
        return
    out.append(f"스니펫: {file}")
    if not dry:
        _write_atomic(file, new)


def _drop_snippet(file: Path, dry: bool, out: list[str]) -> None:
    if not file.exists():
        return
    text = _read(file)
    state = _marker_state(text)
    if state == "none":
        return
    if state == "broken":
        out.append(f"건너뜀: {file} (표식이 깨짐)")
        return
    a, rest = text.split(BEGIN, 1)
    _, b = rest.split(END, 1)
    if b.startswith("\n"):
        b = b[1:]
        if a.endswith("\n\n"):
            a = a[:-1]
    elif b == "" and a.endswith("\n"):
        a = a[:-1]
    out.append(f"스니펫 지움: {file}")
    if not dry:
        _write_atomic(file, a + b)


def _resolve_hosts(hosts: list[str], env: Env) -> list[str]:
    seen: list[str] = []
    for h in hosts:
        if h != "auto" and h not in HOSTS:
            raise ValueError(f"모르는 호스트: {h} (가능: {', '.join(HOSTS)}, auto)")
    for h in hosts:
        for x in (detect(env) if h == "auto" else [h]):
            if x not in seen:
                seen.append(x)
    return seen


def install(hosts: list[str], env: Env, dry_run: bool = False) -> list[str]:
    out: list[str] = []
    for h in _resolve_hosts(hosts, env):
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
                    tmp = dst.with_name(f".{dst.name}.tmp-astack")
                    if tmp.exists():
                        shutil.rmtree(tmp)
                    try:
                        shutil.copytree(s, tmp)
                        (tmp / MARK).write_text("astack setup이 만든 복사본\n", encoding="utf-8")
                    except BaseException:
                        shutil.rmtree(tmp, ignore_errors=True)
                        raise
                    if dst.exists():
                        shutil.rmtree(dst)
                    os.rename(tmp, dst)
        elif h == "hermes":
            out.append(f"직접 실행 (맥미니): {env.repo / 'recipes/hermes/README.md'}의 순서대로")
        else:
            raise ValueError(f"모르는 호스트: {h} (가능: {', '.join(HOSTS)}, auto)")
    return out


def uninstall(hosts: list[str], env: Env, dry_run: bool = False) -> list[str]:
    out: list[str] = []
    for h in _resolve_hosts(hosts, env):
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
    import sys
    p = argparse.ArgumentParser(prog="setup", description="astack 설치 (호스트별)")
    p.add_argument("--host", nargs="+", default=["auto"])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--uninstall", action="store_true")
    a = p.parse_args(argv)
    env = default_env()
    try:
        hosts = _resolve_hosts(a.host, env)
        lines = (uninstall if a.uninstall else install)(hosts, env, a.dry_run)
    except (ValueError, OSError) as e:
        print(f"setup: {e}", file=sys.stderr)
        return 2
    for l in lines:
        print(("(dry-run) " if a.dry_run else "") + l)
    return 0
