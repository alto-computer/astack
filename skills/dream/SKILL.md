---
name: dream
description: Use when 하루를 마무리하며 오늘 생긴 이해물을 엮을 때 — 저녁 스케줄(20:00)이나 사용자가 "오늘 정리", "하루 정리", "dream"이라고 할 때. 일요일에는 주간 수렴까지.
---

# astack dream — 사람을 위한 저녁 정리

**약속:** 오늘 읽은 것들이 한 장으로 엮이고, 며칠 전 것도 한 문항씩 다시 떠올린다. 일요일에는 이번 주 내 일에 쓸 것 3가지로 좁혀진다.

먼저 `astack:design`을 읽는다. Rooms 없이 동작한다.

## 워크플로
1. `astack dream collect` → `today`, `spaced`, `weekly`, `week`.
2. 오늘 이해물이 0개면 Journal을 만들지 않고 "오늘 쌓인 이해물이 없습니다" 한 줄로 끝낸다.
3. 오늘 이해물을 읽는다(각 파일의 30초·3분 층과 "그래서 나한테는?").
4. `assets/template.html`을 채운다:
   - 공통 주제: 둘 이상 이해물에 겹치는 것만.
   - 부딪히는 주장: 왜 다른지(조건, 시점, 정의).
   - 새 질문: 오늘 이해물에서 나온 "남은 질문" → 21:00 후보.
   - 간격 복습: `spaced` 항목마다 짧은 점검 하나(이해형, 답 + 다시 보기 링크).
   - 내 말로 한 줄: 오늘 가장 중요한 이해물 하나.
   - `weekly`면 주간 수렴: 이번 주 방별 `map.html` 변화(있으면 `astack:map`으로 갱신 먼저) + `week` 이해물의 "그래서 나한테는?"을 모아 행동 3가지로 좁힌다(converge). 아니면 주간 섹션을 지운다.
5. 저장: `~/.astack/journal/<날짜>.html` → 메타 → `astack inline` → `astack check` → `astack done <f> --skill dream`. `rooms`가 있으면 `rooms link --journal <날짜> <f>`.
6. 관심 변화가 보이면 관찰만 남긴다: `astack memory add '{"type":"taste","key":"topic:<주제>","insight":"<무엇이 어떻게 바뀌었나>","confidence":0.6,"source":"observed"}'`. consolidate는 하지 않는다(그건 20:30 memory 몫).
7. 알림: 30초 층 두 줄 + 경로.

## 완료 전 체크
- [ ] 오늘 이해물 모두가 어딘가에 링크되어 있다
- [ ] 간격 복습 문항이 암기가 아니라 이해를 묻는다
- [ ] 주간 섹션은 일요일에만
- [ ] `astack check` 에러 0

## Gotchas
- dream·feed 자신의 결과는 collect가 이미 뺀다. Journal이 Journal을 엮지 않게.
- 이 머신에서 만든 이해물만 본다(v1 한계).
- **템플릿은 확정(2026-10-06)이고 쓰면서 고친다.** 사용자가 고치라고 한 점은 `astack memory add`로 교정 기록을 남기고, 같은 교정이 반복되면 템플릿을 고친다.
