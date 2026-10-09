---
name: change
description: Use when an implementation step has just finished and the user should understand what changed without reading the diff — after a subagent-driven-development task passes review (Task mode, commit range), or when a plan finishes or a PR opens (Plan mode). Also on "이 변경 이해시켜줘", "PR 요약 HTML".
---

# astack change — 구현 후 변경 이해물

**약속:** diff를 열지 않고 "이 변경에서 내가 확인할 것 0~3개"와 배포 순서를 안다. 짧은 Task 보고는 5분 안. 상세 코드리뷰 요청이나 여러 경로의 변경은 Plan 모드로 다룬다. 핵심 흐름은 그림 하나와 3줄 이내.

먼저 `astack:design`을 읽는다. 작업을 멈추지 않는다. Task 모드는 백그라운드 서브에이전트로 돈다.

## 시각 설명부터 설계
`../design/references/spec-change-visuals.md`를 읽는다. 변경된 경로마다 다음 세 장면을 연결한다.
1. 사용자 경험: 실제 보이는 상태가 before → after로 어떻게 달라지는가.
2. 원인: 이전 데이터 흐름의 어느 경계에서 왜 깨졌는가. 실패 위치와 이미 완료된 작업을 표시한다.
3. 해결: 같은 주체·배치의 after에서 무엇을 바꿨는가. 데이터, 저장/응답 시점, 오류 분기를 표시한다.
비교 그림에서 바뀐 선·상태를 먼저 보고, 이어서 해설과 실제 코드로 검증할 수 있게 한다. `assets/template.html`의 SVG는 배치 예시이며 실제 변경을 근거로 다시 그린다.

## 길이
- Task 모드 600어절, Plan 모드 1,200어절 이내(`<meta name="astack:words" content="600">`, Plan이면 1200).
- bullet 60자·2문장, 문단 3문장, 섹션당 bullet 5개(`astack:design` 길이 예산).

## 입력
- Task 모드: 커밋 범위(`base..head`), Plan 파일, Task 번호, 리뷰 결과(있으면).
- Plan 모드: 브랜치 또는 PR, Plan 파일, 그 Plan의 Task 모드 이해물 경로들(`astack recall --project . --since <Plan 시작일> --limit 100 --json`을 실행하고, 줄(JSONL, 한 줄에 객체 하나) 중 `"skill"`이 `"change"`인 것만 남긴다).

## 구성 (`assets/template.html`) — 사용자가 실제로 묻는 순서
0. 30초: 이 변경이 만든 것 한 줄 + 배지 줄("스펙과 다름 n · 에이전트가 정한 것 n · 위험 n"). 관계·상태 변화가 없는 작은 Task만 한 줄로 끝낼 수 있다.
1. 유저 경험 before → after.
2. 안 바뀐 것: "그 외에는 그대로"를 명시.
3. 흐름·타이밍: 바뀐 경로만. 실제 코드(커밋의 파일:줄). `p.why`(왜 이렇게 바꿨나)는 핵심 흐름 1~3개에만, 근거는 `.src` 한 줄.
4. 왜: 커밋 메시지·리뷰·Plan 근거. 근거 등급.
5. 에이전트가 정한 것과 대안: 되돌리는 비용.
6. 위험·영향 범위: 사이드이펙트, DB 부하, 하위호환, 약한 테스트(파일:줄).
7. 배포·검증: 대상, 순서와 이유, 내가 테스트할 것, 확인할 숫자의 정의(분모).
Plan 모드는 "PR 리뷰 때 먼저 볼 곳 3개"와 Task별 목록(다름·결정·위험·링크)을 reader 밖 `<section class="prose">`(템플릿의 `#plan`)에 더한다. Task 모드면 그 섹션을 지운다.

## 워크플로
1. `git log --stat base..head`, `git diff base..head`로 바뀐 곳을 본다. Plan의 해당 Task 요구사항과 대조한다.
2. before/after 주체와 데이터를 맞춘 그림을 먼저 그린다. 원인 위치와 수정 위치를 표시한 다음 본문·실제 코드를 연결한다. 비어 있는 장은 쓰지 않는다(빈 제목 금지).
3. `astack inline` → `astack check` → `astack done <f> --skill change --room <프로젝트>`.
4. 채팅에 `경로 — 한 줄`. 메인 작업은 멈추지 않는다.

## 완료 전 체크
- [ ] Task 600어절 · Plan 1,200어절 이내인가(check `length` 경고 없음)
- [ ] "안 바뀐 것"이 있는가
- [ ] 핵심 흐름 1~3개에만 `p.why`가 있고, 각 핵심 흐름이 그림 하나와 3줄 이내인가
- [ ] 배포 대상과 순서가 있는가(배포가 없으면 "배포 없음")
- [ ] 코드 줄 번호가 커밋 기준 실제 줄인가
- [ ] 비교 그림만 보고 이전 문제와 변경 후 해결 지점을 짚을 수 있는가
- [ ] 주요 scene의 데스크톱/모바일 그림이 채워졌는가
- [ ] 시각 설명 계약의 완료 판정을 수행했는가(렌더 미검증은 명시)
- [ ] 키트 밖 `<style>` 블록이 없다(check `own-style`)
- [ ] reader 밖 섹션은 `.prose`(한 단 680px)
- [ ] 산문에 코드 식별자가 없다(check `term`). 이름은 코드 블록이나 `.src`에

## Gotchas
- diff를 그대로 늘어놓지 않는다. 스펙을 다시 설명하지 않는다(spec 이해물이 있다).
- 커밋 범위가 비면 아무것도 만들지 않고 채팅에 그렇게 적는다.
