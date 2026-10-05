---
name: interview
description: Use when 사용자가 팟캐스트, 인터뷰, 대담 영상이나 자막을 이해물(매거진)로 만들어 달라고 요청할 때. "이 팟캐스트 정리해줘", "인터뷰 아티팩트로", "/interview <링크>". 링크만 붙여넣었을 때는 쓰지 않는다.
---

# astack interview — 대화를 보존한 매거진

**약속:** 영상을 다 보지 않고도 대화 전체를 읽은 것처럼 안다. 맨 위 30초·3분만 읽어도 무엇을 얻을지 판단할 수 있다.

먼저 `astack:design`을 읽고 `astack memory search skill:interview`로 교정 기록을 본다.

## 입력과 출력
- 입력: 유튜브 링크, 자막 파일, 또는 녹취 텍스트. 진행자·게스트 이름.
- 출력: `docs/astack/interview/<날짜>-<slug>.html` 한 장 (현재 레포, 없으면 `~/personal/astack-out/`). 3시간이 넘으면 파트별 장 + 지도로 나눈다.

## 원칙 (design 색인에서)
- **convert-not-summarize**: 요약이 아니라 변환. 게스트의 주장·순서·예시·뉘앙스를 그대로. 빼는 건 군말, 반복, 광고, 겹친 말뿐. "요약해줘"라고 해도 매거진을 만든다.
- **anchor-to-source**: 타임스탬프가 있으면 챕터와 풀쿼트를 `원본URL&t=초s`로 잇는다.
- **one-name-per-concept**, 20.2 글쓰기 지침.

## 워크플로
1. 자막: `astack transcript <url> --lang <언어>`. 원 자막(`-orig`)을 먼저 고른다. 출력 머리의 `# lang`과 첫 줄을 확인한다(자동 자막은 언어가 틀리기 쉽다). 자막이 없으면 `--lang ko` 등 다른 언어를 시도한다.
2. 파트(3~6)와 챕터(질문 하나 = 챕터 하나)로 나눈다. 파트마다 짧은 제목 + 게스트의 대표 한 문장.
3. 챕터마다: 앞 챕터와 잇는 리드(`.ch-deck`) 2~3문장, "구조 한눈에"(3~5 노드), 대화 턴(`turn q` 진행자 질문, `turn a` 게스트 답, `turn n` 내레이션), 풀쿼트 하나.
4. `assets/template.html`을 복사해 채운다. `<style>`과 `<script>`는 고치지 않는다. 블록 패턴은 복제한다(`data-pnav` id = `.partdiv id`). 원본 링크는 `{{SRC_URL}}`, 출처 줄(`foot`)의 요청은 `{{요청 원문}}`. 남으면 check가 막는다.
5. 그림: 마스트헤드는 영상 썸네일(`transcript` 출력의 thumbnail)을 내려받아 문서 옆 폴더에 둔다. 게스트 사진은 깨끗한 출처가 있을 때만. 없으면 그림 자리를 비운다(C8): 주석 그대로 두거나 `src=""`. 템플릿이 빈 자리를 밝게 접는다. 의미 없는 그림·캐릭터 금지.
6. `<head>` 메타 세 개를 채운다(`rooms:created`는 `date -Iseconds`, `rooms:machine`은 `scutil --get LocalHostName`, 실패하면 `hostname -s`).
7. `astack inline <f>` → `astack check <f>`(에러 0) → `astack done <f> --skill interview` → 채팅에 경로 한 줄.

## 완료 전 체크
- [ ] 게스트 답변이 원문 순서·내용을 지키는가(무작위 챕터 두 개를 자막과 대조)
- [ ] 30초(`cover`)와 3분(`standfirst`)만 읽고 무엇을 얻을지 알 수 있는가
- [ ] 그림 자리가 비었으면 빈 채로, 넣었으면 내장되었는가
- [ ] 출처 줄(`foot`)에 원본 링크, 요청 원문, "Claude Code가 썼습니다"
- [ ] `astack check` 에러 0
- [ ] 사용자가 선호·제외·교정을 말했으면 `astack memory add`

## Gotchas
- 유튜브 자동 자막만 있으면 언어 코드를 명시해야 한다. 첫 줄이 엉뚱한 언어면 다시 받는다.
- 화자 표시가 없으면 맥락으로 정한다(묻는 쪽이 진행자). 애매한 턴은 내레이션으로 두지 말고 화자를 정한다.
- `>>`는 자동 자막의 화자 바뀜 표시다. 화자를 정하는 단서로 쓴다.
- 이미지 검색이 막히면 Openverse(`https://api.openverse.org/v1/images/?q=<검색어>&page_size=6&aspect_ratio=wide`)를 쓴다. 그래도 없으면 비운다.
- 결과물에는 제3자 발언과 사진이 들어간다. 공개 레포에 커밋하지 않는다.
