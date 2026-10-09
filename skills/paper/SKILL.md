---
name: paper
description: Use when 사용자가 논문 PDF나 arXiv 링크를 읽기 쉬운 이해물(무손실 리더)로 만들어 달라고 요청할 때. "이 논문 리더로", "논문 html", "/paper <링크>". 링크만 붙여넣었을 때는 쓰지 않는다.
---

# astack paper — 논문 무손실 리더

**약속:** 훑으면 결론이 튀어나오고, 파고들면 원문의 모든 수치·figure가 그 자리에 있다.

먼저 `astack:design`을 읽고 `astack memory search skill:paper`로 교정 기록을 본다.

## 불변식 (다른 규칙보다 먼저)
1. 정보량은 그대로. 수치·근거·사례·수식·figure·table 하나도 빠지지 않는다. "무엇을 뺄까"가 떠오르면 틀린 방향이다.
2. 섹션 구조 그대로. 제목·순서는 원문 그대로. 재구성은 섹션 안에서만. 더하는 것은 앞의 "한눈에 보기"와 포스트잇뿐.

## 마찰 → 처방 (힘을 쏟는 순서)
1. 줄글에 묻힌 논리 구조 → **구조화**: 계층은 중첩 목록, 병렬은 나란한 목록, 단계는 번호, 비교는 표.
2. 머릿속으로 그려야 하는 관계 → **시각화**: 아키텍처·데이터 흐름·ablation·비교는 SVG로 그린다. 원문 수치·라벨은 그림 안에 그대로.
3. 흩어진 정보 → **응집**: 결과 하나를 이해하는 데 필요한 figure·수치·전제를 한 장면에 모은다. "Figure 3 참조"로 보내지 않는다.
4. 생략된 전제 → **선해소**: 용어·기호는 처음 나온 자리에서 한 줄로 푼다. 수식은 "무엇을 계산하나" 한 줄 먼저, 기호는 원문 그대로.
5. (보조) 선행연구 → **포스트잇**: 이해가 기대는 소수만 웹으로 확인해 `<details class="postit">`에. 기본은 접힘. 본문에 섞지 않는다.

## 워크플로
1. 본문: arXiv면 `https://ar5iv.org/abs/<id>`를 읽어 섹션·수식·캡션을 얻는다. 아니면 PDF를 Read 도구로 쪽마다 읽는다. ar5iv의 Figure/Table 번호와 본문 교차 참조는 틀릴 수 있다. 번호와 '(Table N)' 참조는 PDF 쪽 이미지로 확인한다.
2. 쪽 이미지: `astack pdf pages <pdf> docs/astack/paper/<날짜>-<slug>-pages/`.
3. figure 전량: 쪽 이미지를 보고 상자를 정해 `astack pdf crop <page.png> x y w h docs/astack/paper/<날짜>-<slug>-figs/fig-N.png`(표는 `tab-N.png`). 좌표는 쪽 PNG의 실제 픽셀(긴 변 2200, `pdf pages`가 stderr에 쪽 크기를 알린다). Read 도구가 줄여 보여 주면 비율을 곱한다. 애매하면 캡션 위 블록까지 넓게 자른다(누락보다 낫다). 개수를 본문의 "Figure N/Table N" 개수와 맞춘다.
4. 매핑: 어떤 figure·수치가 어떤 주장을 받치는지 표로 적고, 원문 수치 목록을 만든다(6번 검증에 쓴다).
5. `assets/template.html`을 복사해 섹션마다 `.secHead`, 하위 섹션마다 장면(`data-i`)과 그림 칸(`data-v`)을 늘린다. figure는 `<img src="<날짜>-<slug>-figs/fig-N.png">`. `{{…}}` 자리표시를 모두 채운다. 남으면 check가 막는다.
6. 무손실 검증(게이트): 4번의 수치 목록을 한 줄에 하나씩 파일로 저장하고 `astack gate paper <결과물.html> --source <원문.html|.txt> --numbers <수치파일>`을 돌린다(`inline` 전이든 후든 된다). `빠짐:` 줄이 나오면 채우고 다시. "gate: 통과"가 나와야 다음으로 간다.
7. 메타 → `astack inline` → `astack check` → `astack done <f> --skill paper`.

## 문체
- 어미 `~다`. 수치·고유명사·인용은 원문 그대로(외국어 인용은 번역 병기). 원문의 참조 번호([12])는 옮기지 않는다.
- 번역투 금지: "~를 통해"→"~로", "~에 의해 ~된"→능동, "~을 가지고 있다"→"~이 있다".
- 강조(`<mark>`, `<b>`)는 아껴 쓴다.

## 완료 전 체크
- [ ] figure·table 레이블이 결과물에 모두 있다(astack gate paper)
- [ ] 수치 목록이 모두 결과물에 있다
- [ ] 섹션 제목·순서가 원문과 같다
- [ ] 포스트잇은 접혀 있고, 원문 내용은 하나도 접혀 있지 않다
- [ ] 키트 밖 `<style>` 블록이 없다(check `own-style`), reader 밖 섹션은 `.prose`
- [ ] 변환이라 단어 상한 없음: `<meta name="astack:words" content="off">`(템플릿에 있다)
- [ ] `astack check` 에러 0

## Gotchas
- `astack gate paper`는 바닥이지 증명이 아니다. 이미지 개수에는 표 이미지와 덤 이미지도 들어가므로 figure 목록을 눈으로도 맞춰 본다.
- 그림은 오른쪽 칸(`.vis`)과 장면 안 모바일 칸(`.vis-inl`)에 둘 다 넣는다. 복사한 SVG의 id는 바꾼다(check가 dup-id로 잡는다).
- 수식이 많으면 KaTeX를 쓰고 싶어지지만 외부 스크립트는 check가 막는다. 수식은 HTML로 조판하거나 원문 쪽 이미지를 잘라 넣는다.
- `astack pdf pages`는 첫 실행에 swift 컴파일로 10초쯤 걸린다.
- 결과물에는 논문 figure가 들어간다. 공개 레포에 커밋하지 않는다.
- **템플릿은 확정(2026-10-06)이고 쓰면서 고친다.** 사용자가 고치라고 한 점은 `astack memory add`로 교정 기록을 남기고, 같은 교정이 반복되면 템플릿을 고친다.
