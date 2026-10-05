---
name: study
description: Use when 사용자가 집중 공부 시간에 이미 있는 이해물(코스의 장, 매거진, 리더) 하나를 펴 놓고 후속 질문을 하거나 더 파 달라고 할 때. "이 장에서 X가 왜 그래?", "이거 더 깊게", "study".
---

# astack study — 깊게 이해하기

**약속:** 묻는 것마다 답이 그 이해물에 남는다. 다음에 열면 내가 물었던 것과 답이 같은 자리에 있다(공리 1: 모든 답은 HTML로).

먼저 `astack:design`을 읽는다. 동기 작업이다. 사용자가 요청한 시간에만.

## 입력과 출력
- 입력: 이해물 하나(경로 또는 `astack recall --query`로 찾기) + 후속 질문.
- 출력: 같은 파일에 섹션을 덧붙인다. 답이 길거나 새 개념이면 하위 교본을 같은 방(같은 폴더)에 만들고 원래 파일에서 링크한다.

## 워크플로
1. 이해물을 읽고, 질문이 어느 장면에 붙는지 정한다.
2. 답한다: 결론 먼저, 근거 등급(확인 / 추론 / 모름), 원문 위치.
3. 덧붙이기: 원래 파일의 해당 장면 아래 또는 끝의 `<section class="study">`에
   ```html
   <section class="study" id="q-[날짜]-[n]">
     <h3 class="st"><span class="no">질문</span><span>[사용자 질문 그대로]</span></h3>
     <div class="lead"><p>[답 한 줄]</p></div>
     <div class="d2"><p>[설명]</p></div>
     <details class="quiz" data-kind="short"><summary>점검 · [질문]</summary><p class="q">[질문]</p><p class="ans">[정답]</p></details>
   </section>
   ```
4. 하위 교본이 필요하면 `astack:quest`의 장 템플릿으로 한 장을 만들고 원래 파일에서 링크.
5. `astack inline <f>` → `astack check <f>` → `astack done <f> --skill study`.

## 완료 전 체크
- [ ] 원래 내용을 지우거나 바꾸지 않았다(덧붙이기만)
- [ ] 답마다 근거 등급과 원문 위치
- [ ] `astack check` 에러 0

## Gotchas
- 원본이 이미 inline된 파일이면 키트 CSS가 안에 들어 있다. 덧붙일 때 `<!--astack:css-->`를 다시 넣지 않는다.
