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


def _put_snippet(file: Path, snippet: str, dry: bool, out: list[str]) -> None:
    text = file.read_text(encoding="utf-8") if file.exists() else ""
    block = f"{BEGIN}\n{snippet.strip()}\n{END}\n"
    if BEGIN in text and END in text:
        a, rest = text.split(BEGIN, 1)
        _, b = rest.split(END, 1)
        new = a + block + b.lstrip("\n")
    else:
        new = text + ("\n" if text and not text.endswith("\n") else "") + ("\n" if text else "") + block
    if new == text:
        out.append(f"그대로: {file}")
        return
    out.append(f"스니펫: {file}")
    if not dry:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(new, encoding="utf-8")


def _drop_snippet(file: Path, dry: bool, out: list[str]) -> None:
    if not file.exists():
        return
    text = file.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        return
    a, rest = text.split(BEGIN, 1)
    _, b = rest.split(END, 1)
    new = (a.rstrip("\n") + "\n" if a.strip() else "") + b.lstrip("\n")
    out.append(f"스니펫 지움: {file}")
    if not dry:
        file.write_text(new, encoding="utf-8")


def install(hosts: list[str], env: Env, dry_run: bool = False) -> list[str]:
    out: list[str] = []
    for h in hosts:
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
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(s, dst)
                    (dst / MARK).write_text("astack setup이 만든 복사본\n", encoding="utf-8")
        elif h == "hermes":
            out.append(f"직접 실행 (맥미니): {env.repo / 'recipes/hermes/README.md'}의 순서대로")
        else:
            raise ValueError(f"모르는 호스트: {h} (가능: {', '.join(HOSTS)}, auto)")
    return out


def uninstall(hosts: list[str], env: Env, dry_run: bool = False) -> list[str]:
    out: list[str] = []
    for h in hosts:
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
    hosts = detect(env) if a.host == ["auto"] else a.host
    try:
        lines = (uninstall if a.uninstall else install)(hosts, env, a.dry_run)
    except (ValueError, OSError) as e:
        print(f"setup: {e}", file=sys.stderr)
        return 2
    for l in lines:
        print(("(dry-run) " if a.dry_run else "") + l)
    return 0
