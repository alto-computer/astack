# astack

사용자의 에이전트가 Alto의 방식대로 사람이 읽는 이해물(HTML)을 만들게 하는 스킬 묶음.

- 경계: superpowers가 무엇을 만들지 정하면, astack은 사람이 그걸 이해하게 만든다.
- 스펙: `docs/superpowers/specs/2026-10-05-astack-v1-handoff.md` (20장이 최신)
- 공리: `AXIOMS.md`

## 설치 (Claude Code)

터미널에서:

```bash
mkdir -p ~/.local/bin && ln -sf ~/personal/astack/bin/astack ~/.local/bin/astack
mkdir -p ~/.astack
printf '%s\n' "$HOME/personal" > ~/.astack/roots
astack recall --limit 1; echo $?    # 기대: 0
```

Claude Code 프롬프트에서:
```
/plugin marketplace add ~/personal/astack
/plugin install astack@astack-dev
```

그 후 `recipes/claude/CLAUDE.md.snippet`의 내용을 `~/.claude/CLAUDE.md` 끝에 추가하세요. (추가 전에 diff를 확인하세요.)

## 지금 있는 것 (P0~P1)

- `astack:spec` 스펙·설계 문서의 이해물
- `astack:change` Task 단위, Plan 요약 이해물
- `astack:recall` 쌓인 이해물에서 지금 읽을 것 찾기
- `bin/astack` check · inline · done · memory · recall
