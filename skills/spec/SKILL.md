---
name: spec
description: Use when a spec, design doc or PR-sized plan has just been saved or shared and the user needs to understand it before approving work, for example right after superpowers brainstorming writes docs/superpowers/specs/*. Also when the user asks to "explain this spec", "스펙 이해시켜줘", "스펙 HTML로".
---

# astack spec — 구현 전 스펙 이해물

**약속:** 스펙 원문을 열지 않고 ① 변경을 자기 말로 설명하고 ② 가정·결정을 리뷰하고 ③ go 또는 수정을 판단할 수 있다.

먼저 `astack:design`을 읽는다. 레퍼런스: `../../docs/superpowers/specs/references/spec-reference-rooms-v1.html`(이 SKILL.md 기준. astack 플러그인 레포에 있다). 복사본(Aside 등)이라 열리지 않으면 `"$(dirname "$(readlink ~/.local/bin/astack)")/../docs/superpowers/specs/references/spec-reference-rooms-v1.html"`. 막히면 레퍼런스의 같은 장을 연다.

## 시각 설명부터 설계
`../design/references/spec-change-visuals.md`를 읽는다. 본문을 쓰기 전에 독자의 질문과 그림을 짝지어 장면을 잡는다.
- 전체 구조도: 사용자 입구 → 모듈/외부 서비스 → 저장/결과, 책임 경계를 표시한다.
- 주요 사용자 경로: 주체 레인과 실제 입출력이 있는 시퀀스. 전체 경로에서 상세 단계로 확대한다.
- 중요한 실패 경로: 어디까지 성공했는지, 무엇이 남는지, 복구/재시도 분기를 그린다.
그림 옆에는 결론·설계 이유·코드 근거를 붙인다. `assets/template.html`의 실제 SVG 배치를 출발점으로 쓰되 주체와 연결은 스펙에서 다시 정한다.

## 입력
- 스펙 파일(필수). 구현 코드가 있으면 그 레포(선택). 코드가 있으면 실제 호출부를, 없으면 "스펙 기준"이라고 적는다.

## 구성 (`assets/template.html`을 복사해 채운다)
0. Overview: 30초 두 줄, 3분 지도.
1. 관심사와 아키텍처: 관심사 카드(우리 것 / 바깥 · 꼭 있어야 하나 · 왜 · 없으면 · 바깥은 "우리가 정하는 계약"). 큰 그림 → 실제 폴더 구조 → 모듈 관계 → 코어 내부. 헷갈리는 경계 하나는 차이 표 + 실제 코드 + 잘못 놓은 예.
2. 주요 유저 스토리의 데이터 흐름: 맨 위 표(6개 안팎: 유저가 겪는 것 / 핵심 경로 / 보장 / 스펙 근거). 2.N은 "유저가 겪는 일:"로 시작. 가장 중요한 스토리 하나만 2.N.M 기술 단계와 실제 코드. 각 2.N과 2.N.M에 `p.why`(왜 이렇게 설계했나 + 근거).
3. 에러 흐름: 맨 위 표(무엇이 잘못되나 / 사용자에게 보이는 것 / 처리). 3.N마다 코드.
4. 가정·전제·결정 리뷰: 칸 = 종류, 무엇을(누가 정했나), 근거(외부 사례 / 대안 비교 / 측정 / 코드베이스 / 사용자 결정 / 근거 없음), 틀리면 깨지는 것, 확인한 곳, 흐름 링크. 스펙과 코드가 다른 곳은 반드시 여기에.
5. 비즈니스 로직: 알아야 할 규칙.
부록: Seam·Contract·AC 원문(접힘).

## 워크플로
1. 스펙을 끝까지 읽는다. 코드가 있으면 진입점과 호출부를 찾는다(`rg`).
2. 관심사를 정하고 우리 것 / 바깥을 나눈다.
3. 사용자 스토리별 질문 → 구조/시퀀스/실패 그림 → 해설과 근거 순서로 작성한다. 유저 스토리 표는 그림으로 연결하는 색인으로 둔다.
4. 코드 발췌는 실제 파일에서 잘라 `<pre data-lang data-start data-path data-who>`로 넣는다. 줄 번호는 파일에서 센다.
5. 리뷰 표: 에이전트가 정한 것과 사용자가 정한 것을 나눈다. 근거 없는 가정은 숨기지 않는다.
6. `astack inline` → `astack check`(에러 0) → `astack done <f> --skill spec --room <프로젝트>` → 채팅에 경로 + 한 줄.

## 완료 전 체크
- [ ] 각 2.N이 유저가 겪는 일로 시작하는가
- [ ] 2장·3장의 모든 장면에 `p.why`(왜 이렇게 설계했나 + 근거)가 있는가
- [ ] 코드 줄 번호가 실제 파일과 맞는가(두 군데 무작위로 연다)
- [ ] 리뷰 표에 "근거 없음"이 있으면 빨간 줄로 보이는가
- [ ] 본문에 색 글자가 없는가
- [ ] 전체 구조·주요 경로·실패 분기를 실제 그림에서 설명할 수 있는가
- [ ] 주요 scene의 데스크톱/모바일 그림이 채워졌는가
- [ ] 시각 설명 계약의 완료 판정을 수행했는가(렌더 미검증은 명시)
- [ ] `astack check` 에러 0

## Gotchas
- 본문에 `<head>` `<title>`을 그대로 쓰면 그 뒤 장면이 통째로 사라진다. 항상 이스케이프.
- 클래스 이름 `.dash`, `.code`는 키트와 충돌한 적이 있다. 새 클래스는 키트 CSS에서 먼저 검색한다.
- 시퀀스 그림 글자가 작으면 레인 간격을 줄이고 viewBox 폭을 줄인다(키우지 않는다).
- 기존 html-artifact 스킬이 같이 불리면 이 스킬의 출력만 남긴다(P1 뒤 html-artifact는 꺼진다).
