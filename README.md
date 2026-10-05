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
| `astack` | Anything: a link, a file, a question | Sends it to the right skill |
| `quest` | A question | A course: a map and chapters with quizzes |
| `study` | One page and a follow-up question | The answer, added to that page |
| `map` | A topic folder | One page that sums up the topic |
| `spec` | A spec or design doc | What it builds, flows, decisions to review |
| `change` | A task's commits or a PR | What changed and what to check |
| `recall` | A topic or "now" | One thing to read now |
| `interview` | A podcast or interview video | A magazine that keeps the full conversation |
| `seminar` | A slide talk video | A report where slides follow your scroll |
| `paper` | A paper PDF or arXiv link | A lossless reader with every figure |
| `repo` | A GitHub repo | Structure, core loop, clever parts, why, weak spots |
| `dream` | Today's pages | An evening journal with spaced review |
| `feed` | Your channel whitelist | A 30-minute morning page |

## CLI

`astack route | course | check | inline | done | memory | recall | transcript | slides | pdf | dream | feed`

Needs yt-dlp and ffmpeg (brew). PDF tools need macOS.

Scheduling (cron, Telegram) comes with host recipes.

Run `astack <command> -h` for details.

## Docs

- Spec: `docs/superpowers/specs/2026-10-05-astack-v1-handoff.md`
- Axioms: `AXIOMS.md`
