# astack

Skills that make your agent turn its work into HTML pages a person can read and understand.

superpowers decides what to build. astack helps you understand it.

## Install

```bash
ln -sf ~/personal/astack/bin/astack ~/.local/bin/astack
mkdir -p ~/.astack && echo "$HOME/personal" > ~/.astack/roots
```

In Claude Code:

```
/plugin marketplace add ~/personal/astack
/plugin install astack@astack-dev
```

Then add `recipes/claude/CLAUDE.md.snippet` to `~/.claude/CLAUDE.md`.

## Skills

| Skill | Input | Output |
|---|---|---|
| `spec` | A spec or design doc | What it builds, flows, decisions to review |
| `change` | A task's commits or a PR | What changed and what to check |
| `recall` | A topic or "now" | One thing to read now |

## CLI

`astack check | inline | done | memory | recall`

Run `astack <command> -h` for details.

## Docs

- Spec: `docs/superpowers/specs/2026-10-05-astack-v1-handoff.md`
- Axioms: `AXIOMS.md`
