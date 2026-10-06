---
name: recall
description: Use when the user is waiting on a long task and has a minute to read (at the start of any task expected to take over five minutes, "recall now", "지금 읽을 거 하나"), or asks what has piled up on a topic or in a period ("브라우저 하네스 관련 뭐 쌓였지", "지난주 거").
---

# astack recall — 쌓인 이해물 꺼내기

**약속:** now 모드는 3초 안에 열 수 있는 하나, 지금 작업과 같은 맥락. 목록 모드는 위에서 3개만 읽으면 된다는 게 분명하다.

새 이해를 만들지 않는다. 찾아서 꺼낸다.

## now 모드
1. `astack recall --now --query "<지금 작업의 핵심 단어 2~3개>" --json`
   - --json은 한 줄에 JSON 객체 하나(JSONL)다. 줄마다 파싱한다.
2. 결과가 있으면 채팅에 한 줄: `지금 읽을 것: <경로> — <description> (<읽는 시간>)`. 후보를 여러 개 늘어놓지 않는다.
3. 결과가 없으면: "같은 맥락의 읽을거리가 아직 없어 하나 만들고 있어요." 백그라운드 서브에이전트로 지금 작업과 같은 맥락의 이해물 하나를 만든다(작업당 1개, quest Quick 또는 해당 원자). 메인 작업은 멈추지 않는다.

## 목록 모드 (주제 · 기간)
1. `astack recall --query "<주제>" [--since YYYY-MM-DD] --limit 20 --json`
   - --json은 한 줄에 JSON 객체 하나(JSONL)다. 줄마다 파싱한다.
2. `assets/list-template.html`을 채운다: 30초 한 줄, 추천 순서 3개(이유 한 줄씩), 더 보려면 나머지, "아직 없는 부분"(→ quest 후보 문장). 안 읽은 개수, 밀린 표시는 쓰지 않는다.
3. `astack inline` → `astack check` → `astack done <f> --skill recall`.

## Gotchas
- 다른 프로젝트 것을 now로 주지 않는다(`--now`는 현재 git 루트로 거른다).
- `outputs.log`가 없으면 `~/.astack/roots`의 루트를 다시 훑는다. 결과가 이상하면 roots 파일을 확인한다.
