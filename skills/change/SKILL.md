---
name: change
description: Use when an implementation step has just finished and the user should understand what changed without reading the diff — after a subagent-driven-development task passes review (Task mode, commit range), or when a plan finishes or a PR opens (Plan mode). Also on "이 변경 이해시켜줘", "PR 요약 HTML".
---

# astack change — 구현 후 변경 이해물

**약속:** diff를 열지 않고 "이 변경에서 내가 확인할 것 0~3개"와 배포 순서를 안다. Task 모드는 5분 안. 이상이 없으면 한 줄로 끝나는 것도 성공이다.

먼저 `astack:design`을 읽는다. 작업을 멈추지 않는다. Task 모드는 백그라운드 서브에이전트로 돈다.

## 입력
- Task 모드: 커밋 범위(`base..head`), Plan 파일, Task 번호, 리뷰 결과(있으면).
- Plan 모드: 브랜치 또는 PR, Plan 파일, 그 Plan의 Task 모드 이해물 경로들(`astack recall --project . --query "Task"`).

## 구성 (`assets/template.html`) — 사용자가 실제로 묻는 순서
0. 30초: 이 변경이 만든 것 한 줄 + 배지 줄("스펙과 다름 n · 에이전트가 정한 것 n · 위험 n"). 전부 0이면 "스펙대로, 볼 것 없음"으로 끝.
1. 유저 경험 before → after.
2. 안 바뀐 것: "그 외에는 그대로"를 명시.
3. 흐름·타이밍: 바뀐 경로만. 실제 코드(커밋의 파일:줄). 각 흐름에 `p.why`(왜 이렇게 바꿨나 + 근거).
4. 왜: 커밋 메시지·리뷰·Plan 근거. 근거 등급.
5. 에이전트가 정한 것과 대안: 되돌리는 비용.
6. 위험·영향 범위: 사이드이펙트, DB 부하, 하위호환, 약한 테스트(파일:줄).
7. 배포·검증: 대상, 순서와 이유, 내가 테스트할 것, 확인할 숫자의 정의(분모).
Plan 모드는 맨 위에 "PR 리뷰 때 먼저 볼 곳 3개"와 Task별 표(다름·결정·위험·링크)를 더한다.

## 워크플로
1. `git log --stat base..head`, `git diff base..head`로 바뀐 곳을 본다. Plan의 해당 Task 요구사항과 대조한다.
2. 비어 있는 장은 쓰지 않는다(빈 제목 금지).
3. `astack inline` → `astack check` → `astack done <f> --skill change --room <프로젝트>`.
4. 채팅에 `경로 — 한 줄`. 메인 작업은 멈추지 않는다.

## 완료 전 체크
- [ ] Task 모드가 5분 안에 읽히는가(본문 1,500자 안팎)
- [ ] "안 바뀐 것"이 있는가
- [ ] 바뀐 흐름마다 `p.why`가 있는가
- [ ] 배포 대상과 순서가 있는가(배포가 없으면 "배포 없음")
- [ ] 코드 줄 번호가 커밋 기준 실제 줄인가

## Gotchas
- diff를 그대로 늘어놓지 않는다. 스펙을 다시 설명하지 않는다(spec 이해물이 있다).
- 커밋 범위가 비면 아무것도 만들지 않고 채팅에 그렇게 적는다.
