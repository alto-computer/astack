---
name: design
description: Use when any astack skill is about to write an understanding HTML. It holds the output contract, writing rules, visual rules and the shared kit. Other astack skills read it first; users do not call it directly.
---

# astack design — 모든 이해물의 공통 규칙

## 출력 계약
- self-contained HTML 한 장. 키트는 `<!--astack:css-->` `<!--astack:js-->` 표식으로 넣고 `astack inline`이 내장한다.
- `<head>` 맨 앞: `description`(한두 줄), `rooms:created`(RFC3339), `rooms:machine`(`scutil --get LocalHostName`, 실패하면 `hostname -s`). 그다음 `<title>`.
- `data-astack="30s"`(무엇이고 왜 중요한지 두 줄), `data-astack="3m"`(지도 하나), `data-astack="source"`(원문, 요청 원문, "Claude Code가 썼습니다").
- 메타 줄: 회색 한 줄, 스킬 · 범위나 날짜 · 읽는 시간. 링크·배지 없음.
- 저장: `<작업 위치>/docs/astack/<스킬>/YYYY-MM-DD-<slug>.html`. 사용자 지시와 프로젝트 규칙 우선.
- 끝: `astack inline <f>` → `astack check <f>`(에러 0) → `astack done <f> --skill <s>` → 채팅에는 경로 + 한 줄.

## 글쓰기
- 두괄식. 결론 먼저.
- 개조식. 두세 줄마다 줄을 바꾼다. 단, 줄만 나열하지 않는다. 앞뒤가 왜 이어지는지 맥락을 한두 문장으로 설명한다.
- 주요 동작 흐름에는 `<p class="why"><b>왜 이렇게 설계했나.</b> …</p>`를 반드시 붙인다. 근거(스펙 절, 커밋, 대안과 기각 이유)와 근거 등급까지.
- 누구나 아는 말. 전문 용어는 처음 나올 때 한 줄로 푼다. 모호한 이름은 모호하다고 적는다.
- 짧은 문장. 한 문장에 생각 하나.
- AI 말투 금지: "핵심은", "사실상", "매우", "해당", "TL;DR", "결론적으로", 대칭 문장, 마무리 문장.
- 사실 주장에는 근거 등급(확인 / 추론 / 모름)과 원문 위치(파일:줄, 절, 타임스탬프, URL).
- 원문 인용은 그대로 두고 해설은 따로.
- 본문의 `<head>`, `<title>` 같은 글자는 반드시 `&lt;head&gt;`로 쓴다(안 쓰면 페이지가 사라진다).

## 시각화
- 2단: 본문 | 그림. 그림은 스크롤에 맞춰 장면마다 바뀐다. 문서는 한 가지 모습뿐.
- 그림에는 관심사 색. 본문 글자에는 색 없음(굵게만).
- 실선 = 우리가 만드는 것, 점선 = 바깥, 빨간 실 = 지금 단계.
- 흐름은 관심사 레인의 시퀀스 그림. 에러는 실패 지점부터 빨간 점선.
- 코드는 본문 안. 실제 파일과 실제 줄 번호만. 줄 번호를 지어내지 않는다. 코드가 없으면 "스펙 기준"이라고 적는다.
- mermaid, 인터랙션, SVG 애니메이션, 손그림 느낌을 써도 된다. 이해를 돕지 않는 장식, 의미 없는 캐릭터는 금지. 그림이 없으면 비운다.

## 원칙 색인
| 원칙 | 언제 | 요지 |
|---|---|---|
| user-first | 모든 흐름 | 유저가 겪는 일로 시작하고, 기술 단계는 그 아래 |
| wrong-example | 헷갈리는 경계 | 잘못 놓은 예 하나(가상 코드라고 표시)와 무엇이 깨지는지 |
| ours-vs-outside | 관심사 | 우리가 만드는 것인지, 계약만 정하는 바깥인지 |
| evidence-tiers | 사실 주장 | 확인 / 추론 / 모름. 코드는 의도의 증거가 아니다 |
| review-after-flow | 가정·결정 | 흐름을 보여준 뒤에 리뷰 표 |
| anchor-to-source | 모든 주장 | 원문 위치로 바로 갈 수 있게 |
| convert-not-summarize | 모든 원자 | 정보량은 그대로, 형식만 바꾼다. "요약해줘"여도 변환 |
| speaker-first | interview, seminar | 화자의 논지·순서·강조가 주인공. 내 해설은 따로 |
| lossless-gate | paper | figure·table·수치 개수를 원문과 대조해야 끝난다 |
| build-up-diagrams | 부품 3개 이상 | 한 장에 다 그리지 말고 하나씩 쌓는다 |

## 시작할 때
- `astack memory search skill:<이 스킬 이름>`으로 교정 기록을 읽는다.
- 사용자가 선호, 제외, 교정을 말하면 `astack memory add '{"type":"correction","key":"skill:<이름>","insight":"…","source":"told"}'`. 기록에서 다시 알 수 있는 사실은 쓰지 않는다.
