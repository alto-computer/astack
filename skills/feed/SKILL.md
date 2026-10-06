---
name: feed
description: Use when 아침 스케줄(05:00)에 "오늘 30분"을 만들 때, 또는 사용자가 "오늘 볼 거", "feed", "아침 30분"을 요청할 때. 화이트리스트 채널 추가·제외 요청("이 채널 feed에 넣어줘", "X는 빼줘")에도.
---

# astack feed — 아침 30분

**약속:** 아침에 30분짜리 한 장만 받는다. 밀린 목록은 없다.

먼저 `astack:design`을 읽고 `astack memory search feed:`, `astack memory search channel:`로 화이트리스트·제외·피드백을 본다.

## 화이트리스트 관리
- 추가: `astack feed seed "<채널 이름>" https://www.youtube.com/@<handle>`. 채널 URL을 모르면 `yt-dlp "ytsearch1:<채널 이름> podcast" --print channel_url`로 찾고 사용자에게 한 줄로 알린다.
- 제외: `astack memory add '{"type":"exclude","key":"channel:<이름>","insight":"feed에서 제외","source":"told"}'`.
- 다시 넣기: 같은 `astack feed seed`. 채널마다 가장 최근 기록(seed 또는 제외)이 이긴다.
- 화이트리스트는 기억(`~/.astack/memory.jsonl`)에만 있다. 레포에 쓰지 않는다.

## 워크플로
1. `astack feed candidates --since <YYYY-MM-DD>`. 지난 실행 날짜는 `astack recall --json`에서 `skill == "feed"`인 가장 최근 항목의 날짜, 없으면 어제.
2. 고르기(30분 분량): 깊게 1~2편(합쳐 ~20분 읽기) + 3분 카드 2~3편. 기준은 취향 — 최근 이해물 주제(`astack recall --since <2주 전> --json`), 기억의 feedback("2번 별로: 너무 입문용")·taste. 나머지는 만들지 않는다.
3. 깊게: 편마다 `astack:interview`(슬라이드 발표면 `astack:seminar`)로 매거진을 만든다. 출력 폴더는 `~/.astack/journal/feed/<날짜>/`로 정해 준다. 지금 레포의 `docs/astack/`에 쓰지 않는다(남의 자막이 아무 레포에 들어간다).
4. 카드: `astack transcript <url> --lang <언어>`(영어가 아닌 채널은 `--lang`이 꼭 필요하다)로 자막을 읽고 핵심 3줄 + "그래서 나한테는?" 한 줄.
5. `assets/template.html`을 읽는 순서대로 채운다. 모든 편에 원본 URL이 본문에 있어야 한다(다음 feed의 중복 판단에 쓰인다).
6. 저장 `~/.astack/journal/<날짜>-feed.html` → 메타 → `astack inline` → `astack check` → `astack done <f> --skill feed`.
7. 사용자가 "2번 별로" 같은 답을 주면: `astack memory add '{"type":"feedback","key":"feed:<날짜>#2","insight":"별로: <이유>","source":"told"}'`.

## 완료 전 체크
- [ ] 전체 읽는 시간 30분 이내
- [ ] 편마다 원본 URL이 본문에 있다
- [ ] 제외 채널이 없다
- [ ] `astack check` 에러 0

## Gotchas
- 채널 영상 목록의 날짜는 근사값이다(`approximate_date`). 하루 차이는 무시한다.
- 채널 목록에 날짜가 없으면 두 번째 조회(채널당 yt-dlp 한 번)로 날짜를 채운다. 그래도 못 채운 후보는 맨 뒤에 나오고 stderr에 경고가 찍힌다(since로 거르지 못했다는 뜻).
- `--since`를 주면 그보다 오래된 날짜의 후보는 빠지고, 날짜 없는 후보는 남아 맨 뒤에 경고와 함께 나온다.
- 고르기 전에 `astack transcript`가 찍는 `# … · YYYYMMDD`의 날짜를 확인한다. 너무 오래된 영상은 고르지 않는다.
- 후보가 0개면 만들지 않고 "오늘 새 영상 없음" 한 줄.
- **템플릿은 확정(2026-10-06)이고 쓰면서 고친다.** 사용자가 고치라고 한 점은 `astack memory add`로 교정 기록을 남기고, 같은 교정이 반복되면 템플릿을 고친다.
