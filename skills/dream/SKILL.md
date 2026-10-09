---
name: dream
description: Use when 하루를 마무리하며 오늘 생긴 이해물을 엮을 때 — 저녁 스케줄(20:00)이나 사용자가 "오늘 정리", "하루 정리", "dream"이라고 할 때. 일요일에는 주간 수렴까지.
---

# astack dream — 사람을 위한 저녁 정리

**약속:** 오늘 읽은 것들이 한 장으로 엮이고, 며칠 전 것도 한 문항씩 다시 떠올린다. 일요일에는 이번 주 내 일에 쓸 것 3가지로 좁혀진다.

먼저 `astack:design`을 읽는다. Rooms 없이 동작한다.

## 워크플로
1. `astack dream collect` → `today`, `spaced`, `weekly`, `week`.
   `collect`는 `astack done` 기록에 더해 Rooms 방에 오늘 들어온 문서도 읽는다(`source: rooms`). Rooms가 없으면 기록만.
2. 오늘 이해물이 0개면 Journal을 만들지 않고 "오늘 쌓인 이해물이 없습니다" 한 줄로 끝낸다.
3. 오늘 이해물을 읽는다(각 파일의 30초·3분 층과 "그래서 나한테는?").
4. `assets/template.html`을 채운다:
   - 모든 항목은 `.point` 블록: 제목 한 문장 + bullet 2~3개 + 회색 출처 한 줄(`.src`, 이해물 링크).
   - 3분 층은 그림 없이 연결 bullet 3개(`overview one`). 한 단 문서다.
   - 공통 주제: 둘 이상 이해물에 겹치는 것만.
   - 부딪히는 주장: 왜 다른지(조건, 시점, 정의).
   - 새 질문: 오늘 이해물에서 나온 "남은 질문" → 21:00 후보.
   - 간격 복습: `spaced` 항목마다 짧은 점검 하나(이해형, 답 + 다시 보기 링크).
   - 내 말로 한 줄: 오늘 가장 중요한 이해물 하나.
   - `weekly`면 주간 수렴: 이번 주 방별 `map.html` 변화(있으면 `astack:map`으로 갱신 먼저) + `week` 이해물의 "그래서 나한테는?"을 모아 행동 3가지로 좁힌다(converge). 아니면 주간 섹션을 지운다.
5. 저장 위치는 `astack dream path`가 알려준다. Rooms가 있으면 `~/rooms/journal/<날짜>/dream.html`(그날 Journal 맨 위 "Review"로 보인다. 파일 자체를 쓰고 링크하지 않는다. 이미 있으면 덮어쓰기 전에 묻는다), 없으면 `~/.astack/journal/<날짜>.html`. → 메타 → `astack inline` → `astack check` → `astack done <f> --skill dream`(Rooms 안 파일이라 링크는 건너뛰고 기록만 남는다).
6. 관심 변화가 보이면 관찰만 남긴다: `astack memory add '{"type":"taste","key":"topic:<주제>","insight":"<무엇이 어떻게 바뀌었나>","confidence":0.6,"source":"observed"}'`. consolidate는 하지 않는다(그건 20:30 memory 몫).
7. 알림: 30초 층 두 줄 + 경로.

## 길이
- 본문 600어절 이내(`<meta name="astack:words" content="600">`). 짧고 쉽게. 이해물 수만큼 쓰지 않는다. 겹치는 것만 고르고 나머지는 링크로.
- bullet 60자·2문장, 섹션당 bullet 5개(`astack:design` 길이 예산).

## 완료 전 체크
- [ ] 오늘 이해물 모두가 어딘가에 링크되어 있다
- [ ] 간격 복습 문항이 암기가 아니라 이해를 묻는다
- [ ] 주간 섹션은 일요일에만
- [ ] 본문 600어절 이내(check `length` 경고 없음)
- [ ] 키트 밖 `<style>` 블록이 없다(check `own-style`). reader가 없는 한 단 문서라 섹션은 템플릿 그대로(`.wrap.col`)
- [ ] 산문에 코드 식별자가 없다(check `term`)
- [ ] `astack check` 에러 0

## Gotchas
- dream·feed 자신의 결과는 collect가 이미 뺀다. Journal이 Journal을 엮지 않게.
- 이 머신에서 만든 이해물만 본다(v1 한계).
- **템플릿은 확정(2026-10-06)이고 쓰면서 고친다.** 사용자가 고치라고 한 점은 `astack memory add`로 교정 기록을 남기고, 같은 교정이 반복되면 템플릿을 고친다.
