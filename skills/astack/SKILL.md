---
name: astack
description: Use when 사용자가 무엇을 원하는지 스킬 이름 없이 던질 때 — 링크 하나, 파일 하나, 질문 한 줄, "오늘 정리" — 그리고 어느 astack 스킬로 처리할지 정해야 할 때. "astack <무엇이든>", "이거 처리해줘"와 함께 링크·질문만 줄 때.
---

# astack — 입구

**약속:** 무엇을 던져도 알맞은 스킬이 받는다. 사용자는 스킬 이름을 몰라도 된다.

## 워크플로
1. `astack route "<입력>"` → `{"skill", "reason", "needs_judgment"}`.
2. `needs_judgment`가 false면 그 스킬을 바로 부른다(`astack:<skill>`).
3. true면 판단한다:
   - YouTube: 제목·설명·썸네일을 본다(`astack transcript <url> --json`의 title). 슬라이드 발표·강연·컨퍼런스 talk면 `seminar`, 대담·팟캐스트·인터뷰면 `interview`.
   - 일반 링크: 글 하나면 `quest`(사례 또는 개념 유형, Quick), 레포·논문이 본문이면 해당 원자.
   - 파일: 열어 보고 원자 또는 quest. 이해물 HTML에 후속 질문이 붙어 있으면 study.
4. 고른 스킬과 이유를 채팅에 한 줄로 알리고 진행한다. 확인을 기다리지 않는다.

## 라우팅 표
| 입력 | 스킬 |
|---|---|
| YouTube 대담·팟캐스트 | interview |
| YouTube 슬라이드 발표 | seminar |
| arXiv, PDF | paper |
| GitHub 레포 | repo |
| `docs/**/specs/*.md` | spec |
| "오늘 정리", "하루 정리" | dream |
| 질문, 공부하고 싶은 것 | quest |
| "지난주 거", "X 관련 뭐 쌓였지" | recall |
| 이해물 HTML 경로 + 후속 질문 | study |
