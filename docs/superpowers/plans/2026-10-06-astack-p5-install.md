# P5 install on this Mac (2026-10-06)

| Step | Result |
|---|---|
| Backup | `~/.claude/CLAUDE.md.bak-20261006-112058` |
| `./setup --dry-run` | 1 adopt (CLAUDE.md unmarked P1 block → marked), 14 codex links, AGENTS.md snippet, 14 aside copies; `~/.local/bin/astack` unchanged |
| `./setup` | exit 0 |
| CLAUDE.md / AGENTS.md | one `astack:begin` block each, one `## astack` |
| Codex | 14 `astack-*` links; 8 existing user skills kept |
| Aside | 14 `astack-*` copies with `.astack-managed` |
| Re-run | no changes (idempotent) |
| Codex smoke | `codex exec --skip-git-repo-check` listed `astack:recall`, `astack:quest` from `~/.codex/skills/astack-*` |
| Claude plugin | user runs `/plugin marketplace add ~/personal/astack`, `/plugin install astack@astack-dev` |
| Hermes | not on this Mac — `recipes/hermes/README.md` on the Mac mini |
| Night goal smoke | not run here (no scheduler); first real run on the Mac mini |
