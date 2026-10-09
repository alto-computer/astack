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
- 단어 상한: `<head>`에 `<meta name="astack:words" content="N">`(스킬별 상한, 아래 길이 예산). 없으면 1,500. 변환 스킬(interview, seminar, paper)은 `content="off"`.
- 스타일은 키트뿐. 자기 `<style>` 블록을 더하지 않는다. 필요한 모양은 키트 클래스(`.prose`, `.point`, `.src`, `.card`)로.
- 끝: `astack inline <f>` → `astack check <f>`(에러 0) → `astack done <f> --skill <s>` → 채팅에는 경로 + 한 줄.

## 글쓰기
- 두괄식. 결론 먼저.
- 개조식. 두세 줄마다 줄을 바꾼다. 단, 줄만 나열하지 않는다. 앞뒤가 왜 이어지는지 맥락을 한두 문장으로 설명한다.
- `<p class="why"><b>왜 이렇게 설계했나.</b> …</p>`는 핵심 흐름 1~3개에만 붙인다. 이유는 두 문장 안, 근거는 아래 `.src` 줄로. 나머지 흐름은 `.src` 줄만.
- 누구나 아는 말. 전문 용어는 처음 나올 때 한 줄로 푼다. 모호한 이름은 모호하다고 적는다.
- 산문에 코드 식별자(camelCase, snake_case, `a.b`, `run()`)를 쓰지 않는다. 쉬운 말로 쓰고, 이름은 코드 블록이나 `.src` 줄에. check가 `term`으로 경고한다.
- 짧은 문장. 한 문장에 생각 하나.
- AI 말투 금지: "핵심은", "사실상", "매우", "해당", "TL;DR", "결론적으로", 대칭 문장, 마무리 문장.
- 사실 주장에는 근거 등급(확인 / 추론 / 모름)과 원문 위치(파일:줄, 절, 타임스탬프, URL). 둘 다 블록 끝 회색 한 줄 `<p class="src">`에 모은다. 문장 안에 넣지 않는다. 등급 표시(`.ev`)는 회색 글자이고 "근거 없음"(`ev-bad`)만 빨강.
- 원문 인용은 그대로 두고 해설은 따로.
- 본문의 `<head>`, `<title>` 같은 글자는 반드시 `&lt;head&gt;`로 쓴다(안 쓰면 페이지가 사라진다).

## 길이 예산
- bullet 하나에 생각 하나. 60자 이내, 2문장 이내.
- 문단은 3문장 이내. 섹션 하나에 bullet 5개까지.
- 블록 모양: 제목 + bullet 2~3개 + `.src` 한 줄.
- 스킬별 본문 상한(어절, `astack:words`): dream 600 · quest 장 900 · quest 지도 500 · spec 1,500 · change Task 600 / Plan 1,200. 넘으면 check가 `length`로 경고한다.
- 원문 전문이 필요하면 접힌 부록(`details.apx`)에만. 부록은 상한에 세지 않는다.

## 읽는 폭
- reader(2단) 밖 읽기 블록은 한 단 680px(한 줄 40~46자). 키트가 `.wrap>section`, `footer`, `.prose`에 건다.
- reader 밖에 새 섹션을 두면 `<section class="prose">`로 감싼다. 한 단 문서(dream, quest 지도)는 `<div class="wrap col">`.
- 3분 층(`overview`)은 진한 글자. 그림이 없는 문서는 `overview one`에 요약 bullet.

## 시각화
- 2단: 본문 | 그림. 그림은 스크롤에 맞춰 장면마다 바뀐다. 문서는 한 가지 모습뿐.
- 좁은 화면은 `.stage`를 숨긴다. 장면마다 `.inl.vis-inl` 사본을 두고, 사본의 SVG id에 접두사를 붙인다.
- 그림에는 관심사 색. 본문 글자에는 색 없음(굵게만).
- 실선 = 우리가 만드는 것, 점선 = 바깥, 빨간 실 = 지금 단계.
- 흐름은 관심사 레인의 시퀀스 그림. 에러는 실패 지점부터 빨간 점선.
- 코드는 본문 안. 실제 파일과 실제 줄 번호만. 줄 번호를 지어내지 않는다. 코드가 없으면 "스펙 기준"이라고 적는다.
- SVG 글자는 보이는 크기로 12px 이상. 좁은 화면 사본은 viewBox 폭을 칸 폭 이하로, font-size 13 이상. check가 `svg-text`로 경고한다(viewBox 폭 600 초과 + font-size 11 미만).
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
| convert-not-summarize | interview, seminar, paper만 | 정보량은 그대로, 형식만 바꾼다. "요약해줘"여도 변환. 다른 스킬은 길이 예산이 우선 |
| speaker-first | interview, seminar | 화자의 논지·순서·강조가 주인공. 내 해설은 따로 |
| lossless-gate | paper | figure·table·수치 개수를 원문과 대조해야 끝난다 |
| build-up-diagrams | 부품 3개 이상 | 한 장에 다 그리지 말고 하나씩 쌓는다 |
| definition-then-case | 개념 설명 | 일반 정의(통용 이름) → 지금 사례 → 깊이 |
| retrieval-check | 장 끝 | 이해를 묻는 질문. 암기 금지. 오답 = 오해 진단 |
| converge | map, dream | 쌓여도 두꺼워지지 않고 정확해진다 |
| explain-the-number | 실험 | 숫자를 제한하는 요인, 엉뚱한 걸 잰 건 아닌지 |
| build-the-lever | 실험 | 손으로 재지 말고 다시 돌릴 벤치를 만든다 |

## 시작할 때
- `astack memory search skill:<이 스킬 이름>`으로 교정 기록을 읽는다.
- 사용자가 선호, 제외, 교정을 말하면 `astack memory add '{"type":"correction","key":"skill:<이름>","insight":"…","source":"told"}'`. 기록에서 다시 알 수 있는 사실은 쓰지 않는다.

## 기억 정리 (에이전트용, 저녁 20:30)
- `astack memory consolidate` — 중복 합치기, 최신 told가 오래된 observed를 대체, observed는 나이로 감쇠(30일 반감), 같은 told 교정 3번이면(같은 말 반복도 센다) 규칙으로 승격, `skill:` 교정 반복은 레포 패치 **제안만**. 직전 상태는 `~/.astack/archive/<날짜>.jsonl`에 저장되며, 읽을 수 없는 레코드는 그대로 두고 모든 변경 전 스냅샷이 보관된다.
- 되돌리기: `astack memory restore --list`로 스냅샷 이름을 본다(최신 먼저). `astack memory restore <날짜>`는 그날 첫 상태, 그 뒤 스냅샷·pre-restore 사본은 `astack memory restore <이름>`.
- 지우기: `astack memory prune --key <접두사>`(접두사 일치라 `feed:youtube:A`는 `feed:youtube:AI…`도 지운다) · `--type <type>` · `--before YYYY-MM-DD`(날짜 없는 기록은 남는다).
- 사람용 dream과 따로 돈다. 둘이 만나는 곳은 `memory add` 한 줄뿐.
