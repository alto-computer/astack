# astack v1 — 구현 핸드오프 문서

> 이 문서는 코딩 에이전트에게 넘기기 위한 **단일 맥락 문서**다. 설계 대화(2026-10-05)에서 정한 모든 결정, 그 이유, 기각된 대안, 참고 자료, 마이그레이션 대상 경로, 구현 순서와 완료 기준을 담았다.
> 같은 내용의 사람용 스펙(HTML)은 `2026-10-05-astack-v1-spec.html`이다. 둘이 다르면 **이 문서가 최신**이다.

---

## 0. 이 문서를 받은 에이전트에게

- **설계(brainstorming)는 끝났다.** 이 문서가 승인된 스펙이다. 다음 단계는 superpowers `writing-plans`로 구현 계획을 쓰는 것이다. 설계를 다시 열지 말고, 모호한 지점은 19장 "열린 질문"의 기본값을 따른 뒤 계획서에 표시한다.
- 사용자는 **윤준선(Junseon)**. Alto Computer 브랜드로 Alto Rooms를 만들고 있다. 한국어로 소통한다 (영어 기술 용어 혼용 OK).
- 레포 위치: `~/personal/astack` (README만 있음). GitHub: `alto-computer/astack` 예정 (공개 여부 미정, 레포에는 개인 데이터가 없도록 설계됨).
- 관련 프로젝트: `~/personal/alto-rooms` (Alto Rooms, 스펙: `docs/superpowers/specs/2026-10-05-alto-rooms-v1-spec.html`). 지금 Plan 2를 subagent-driven-development로 구현 중이다.
- **사용자의 개발 습관**: superpowers를 메인으로 쓴다. brainstorming이 스펙을 쓰면 개인 스킬 `html-artifact`(`~/.claude/skills/html-artifact/`)가 함께 불려 이해용 HTML을 만든다. 이 흐름은 이미 잘 동작한다.

---

## 1. 배경: 왜 만드는가

### 1.1 사용자가 직접 말한 문제
- "에이전트가 일하고 작업하는 걸 보고 있는 것만큼 멍청한 게 없다." 근무 중 이해하거나 검토할 시간이 빌 때 멍때리게 된다.
- Learning 모드처럼 작업을 동기식으로 막고 이해시키면 **속도가 느려진다**. 요즘은 "미리 다 구현해놓고 이해하는" 방식이 많다.
- 예: Plan 하나를 3시간 돌리면, 이해는 **전부 끝난 뒤 한꺼번에** 몰린다.
- Instinct(별도 머신의 개인 에이전트)에 카드뉴스 브리프를 받는데, 관심 항목을 발견하면 딥다이브를 요청하고 **기다려야 해서 흐름이 끊긴다.**
- 이해물을 만드는 스킬이 Aside용과 Claude Code용으로 갈라져 있고, 맥미니나 다른 에이전트에서는 쓸 수 없다.
- 토큰은 많다. "최대한 많은 공부 자료를 미리 만들어둬야 한다." 동시에 "내가 다 이해할 수 있을까, 컨텍스트 스위칭이 더 심해지지 않을까"도 걱정한다.
- 사용자가 말하는 "공부"에는 **실험**도 포함된다. 예: "Aside, browser-harness, Chrome, 새 헤드리스 브라우저 속도·성능 비교" → 벤치가 없으면 만들어서 돌린다.

### 1.2 목표 (한 줄)
**기다리는 모든 순간에, 지금 일과 같은 맥락의 이해물이 이미 준비돼 있다. 궁금한 건 던져두면 쌓이고, 쌓인 건 필요할 때 꺼내진다.**

### 1.3 astack의 정의
**astack은 사용자의 에이전트가 Alto의 경험대로 "이해물"을 만들게 하는 선택형 빌트인 스킬이다.** 설치하면 에이전트가 더 좋은 이해물을 만들고, 결국 사람이 더 잘 이해하게 된다. (gstack, pstack 같은 "~stack" 계열의 Alto Computer 버전. 이름은 Alto의 a.)

---

## 2. 사용자 환경

| 머신 | 설치된 것 | 역할 |
|---|---|---|
| 메인 맥 | Claude Code, Codex, Aside(브라우저 에이전트, `~/.aside`) | 개발 (RAM 많음). 자주 꺼져 있음 (통학이 김) |
| 맥미니 | **Hermes Agent**(Nous Research, Telegram으로 소통), Claude Code, Codex, Aside(같은 프로필) | 상시 가동. 리서치 본진, 백그라운드 작업 |
| Instinct | 별도 머신의 개인 에이전트. 사용자 Gmail 접근 | 취미용 카드뉴스 브리프 (astack 범위 밖) |

- 모바일: 맥미니 Hermes를 Telegram으로 조작, 메인 맥이 켜져 있으면 Orca/Codex remote control.
- Aside CLI: `aside "<task>"`, `aside mcp`, `aside repl` (docs: https://docs.aside.com/help/developers).
- Aside 샌드박스 참고: Aside의 Bash는 `/Library/Developer` 읽기 허용을 추가해 git이 동작한다. `~/personal` 등은 기본적으로 쓰기 불가 → Aside에 astack 결과물을 쓰게 하려면 `permission.files.writableRoots`에 경로 추가 필요.
- YouTube 구독: **업무 계정(authuser=0)**이 진짜 구독 계정 (54채널). 개인 gmail 계정 구독은 노이즈가 많다.

---

## 3. 경계: 누가 무엇을 하나

| 주체 | 하는 일 | 하지 않는 일 |
|---|---|---|
| 사용자의 에이전트 (Claude Code, Codex, Hermes, Aside) | 실제로 일한다. 사용자 설정을 따른다 | |
| **astack** | 에이전트에게 **잘 이해시키는 방법**을 준다 | 프로세스, 개발, 스케줄, 저장소 운영 |
| Alto Rooms | 결과물(HTML)을 모아서 보여준다 (폴더 규칙, 방, Journal) | AI 일 (원칙: 1000% 사용자 에이전트에 위임) |
| superpowers | 무엇을 어떻게 만들지 (brainstorming, plans, SDD, 설계 관문 HARD-GATE) | |

- **경계 문장**: superpowers/pstack가 "무엇을 할지"를 만들면, astack은 "사람이 그걸 이해하게" 만든다. 그래서 개발 문서(스펙, 변경)도 다루지만 개발 프로세스는 다루지 않는다.
- astack과 Rooms는 서로 몰라도 각각 동작해야 한다. **하나만 설치한 사람도 잘 쓸 수 있어야 한다.**
- superpowers 확장 방식(공식 안내): 본체를 포크하지 않고 **개인 스킬**(`~/.claude/skills/`, Codex 등은 `~/.agents/skills/`)로 얹고, 동작 조정은 **CLAUDE.md**(사용자 지침이 스킬보다 우선)로 한다. 프로젝트 고유 규칙은 스킬이 아니라 지침 파일에 둔다.

### 기각된 대안 (다시 꺼내지 말 것)
- **pstack으로 메인 교체**: 기각. pstack은 설계까지 에이전트가 자율로 정하는데, 사용자 코드베이스가 지저분해서 "기존 패턴을 보고 설계"하면 틀릴 수 있다. superpowers 메인 + 필요한 것만 개인 스킬로 얹는 방식으로 결정.
- **astack에 개발 프로세스 스킬 포함**: 기각. 공리 2.
- **Aside Slack/Telegram 채널 연결**: Pro 플랜 전용이라 불가. Telegram은 맥미니 Hermes가 맡는다.
- **Tailscale/Vercel 배포 필수화**: 기각. Telegram 파일 첨부나 Rooms 원격 보기, 정적 서버 중 아무거나. 호스트 몫.
- **astack이 Rooms API(`/v1/search` 등) 사용**: 기각. 결합도 0을 위해 astack은 파일만 쓴다.
- **구독 목록/취향을 레포에 파일로(sources.yaml, taste.md)**: 기각. 개인 데이터는 `~/.astack/` 로컬 기억에, 취향은 기록에서 재구성.
- **대화형 check(점검)**: 기각. 공리 1 → 점검도 HTML 인터랙티브 퀴즈.
- **feed를 대량 카드뉴스로**: 기각. 취미 목록(HF 논문 등)은 Instinct. astack feed는 화이트리스트 YouTube 채널, 아침 30분 분량만.
- **sync 기반 멀티디바이스 Rooms**: 보류. 머신별 독립 Rooms, 통합은 v2 클라이언트 페더레이션.

---

## 4. 공리 (모든 결정의 기준. 충돌하면 공리가 이긴다)

1. **모든 산출물은 HTML이다.** 퀴즈, 질의응답, 종합, 개념 설명 모두 HTML. 채팅·알림에는 경로 + 한 줄 요약만. 진행 상황·실패 이유 같은 운영 메시지는 예외. HTML은 self-contained이고 격리 환경(저장소·API 키·필수 외부 호출 없음)에서 동작해야 한다.
2. **이해만 한다.** 프로세스와 개발은 superpowers의 몫.
3. **저장 위치는 환경을 따르고, Rooms가 있으면 링크한다.** 기본 `<작업 위치>/docs/astack/<스킬>/YYYY-MM-DD-<slug>.html`. 사용자 지시·프로젝트 규칙 우선. `rooms link`가 있으면 호출, 없으면 건너뜀. (superpowers가 `<프로젝트>/docs/superpowers/specs/`에 쓰는 관례를 따른 것. 전역 폴더를 만들지 않는다.)
4. **런타임이 없다.** 언제·어디서 실행할지는 호스트(Hermes cron, 세션 훅)가 정한다. 대신 호스트용 레시피를 함께 배포한다.
5. **상태는 파일에 있다.** `~/.astack/`의 텍스트 파일뿐. 레포에는 틀만. 색인은 파일에서 다시 만들 수 있는 파생물로만.
6. **이해는 비동기, 재고는 넉넉히.** astack은 작업 흐름을 절대 멈추지 않는다. 기다리는 순간에 읽을 게 없으면 실패. 설계 확정의 동기 관문은 superpowers brainstorming의 HARD-GATE가 맡는다 (astack에 예외 없음).
7. **만드는 건 많이, 보여주는 건 적게.** 희소한 건 주의력. 재고는 할 일 목록이 아니라 서랍(안 읽은 개수·밀린 표시 없음). 업무 중 대기에는 같은 맥락만. 모든 이해물은 30초/3분/30분 세 층. "다음 하나"만 준다. 코스가 여러 장이어도 입구는 지도 한 장, 알림은 한 줄. 발산(quest, feed)만큼 수렴(dream, map)을 정해진 리듬으로.

### 주의력 등급
| 등급 | 무엇 | 다루는 방식 |
|---|---|---|
| 업무 | spec, change, recall now | 최우선. 대기 시간에만, 같은 맥락만 |
| 핵심 공부 | quest (실험 포함) | 적중률이 생명. 저녁에 사용자가 고른 것만 밤에 돌림. map으로 수렴 |
| 아침 읽기 | feed | 아침 30분 분량만 |
| 취미 | HF 논문 목록 등 | astack 밖 (Instinct) |

---

## 5. 사용자 시나리오 (완료 기준의 원천)

| # | 상황 | 일어나야 하는 일 |
|---|---|---|
| 1 | Plan을 3시간 돌리는 중 (superpowers SDD) | Task가 리뷰를 통과할 때마다 그 Task의 `change`가 **백그라운드**로 생긴다. 에이전트가 Task N+1을 만드는 동안 사용자는 Task N을 이해한다. 끝나면 Plan 전체 요약 한 장 |
| 2 | 개발 설계 중 | brainstorming이 스펙을 저장하면 `spec`이 이해용 HTML을 만든다 (지금도 동작). 확정할 결정 목록, 레거시 충돌 표시, go 전 점검 퀴즈 |
| 3 | 대기 중 멍한 순간 | `recall now` → 지금 작업과 같은 맥락의 3분짜리 **하나** |
| 4 | 지하철에서 궁금한 게 생기면 | Telegram Quest 토픽에 한 줄 → 확인 없이 바로 진행 → 완료 즉시 무음 알림. 재고에 쌓인다 |
| 5 | 아침 | feed "오늘 30분" 한 장 + 밤 goal 결과 (07:00 1통) |
| 6 | 저녁 | dream이 하루를 엮고 간격 복습과 "내 말로 한 줄"을 묻는다. 21:00에 "오늘 밤 돌릴 질문"을 받는다 → 고른 것만 밤에 goal로 |
| 7 | 집중 공부 시간 | `study`로 교본 하나를 깊게. 후속 질문과 더 파기가 같은 교본에 덧붙는다 |
| 8 | 팟캐스트 보다가 직접 | `/interview <링크>` 또는 "이 인터뷰 정리해줘" |
| 9 | 실험이 궁금할 때 | "브라우저별 속도 비교" → 벤치를 찾거나 만들어 밤에 돌림 → 실험 보고서 + 재현 가능한 벤치 코드 |
| 10 | 무언가를 공부하고 싶을 때 | "Codex CLI 공부" → 지도 + 10~12장 코스. 입구는 지도 한 장 |

---

## 6. 스킬 카탈로그

### 6.0 노출 구조
```
사용자 동사   quest (만들어두기) · study (깊게 이해하기) · recall (꺼내기)
원자(단축키)  interview · seminar · paper · repo · spec · change
자동 실행    feed (아침 30분) · dream (저녁) · map (수렴) · memory (기억)
공통        astack (입구/라우터) · design (공통 문서, 직접 부르지 않음)
스크립트     setup (스킬 아님)
v1.1        check (별도 점검 덱) · article (긴 글, X 스레드) · 월간 수렴
```
- 원자는 quest의 부품이면서 직접 부를 수 있는 단축키다. `/interview <링크>`와 Telegram에 링크만 던지는 건 결과가 같다.
- 원자 이름은 **소스 종류**, 조합 이름은 **시작 계기**. 출력 형식 이름(매거진, teardown 등)은 스킬 내부에만.

### 6.1 description 규칙 (모든 스킬)
superpowers `writing-skills` 지침: description에는 **언제 쓰는지만**, `Use when`으로 시작, 워크플로를 요약하지 않는다 (요약하면 에이전트가 본문을 안 읽고 행동함). 500자 이내.
```yaml
---
name: interview
description: Use when 사용자가 팟캐스트, 인터뷰, 대담 영상이나 자막을 정리하거나 아티팩트로 만들어달라고 요청할 때. "이 팟캐스트 정리해줘", "인터뷰 아티팩트로" 같은 요청.
---
```
- **자동 선택 허용**: `spec`, `change`, `recall`(긴 작업 처방). 나머지 무거운 원자는 **요청할 때만** 반응하도록 description을 "요청할 때"로 좁힌다 (링크를 붙여넣기만 했을 땐 반응하지 않음).

### 6.2 스킬 본문 뼈대 (모든 SKILL.md 공통)
1. 약속: 이 스킬을 쓰면 사용자가 얻는 것 한 줄
2. 입력과 출력
3. 원칙: `design` 원칙 색인 중 특히 중요한 것을 **이름으로** 부른다 (pstack 방식)
4. 워크플로: 번호 단계. 호스트별 동작은 "능력" 이름으로 쓰고 `design/references/capabilities.md` 참조
5. 완료 전 체크: 출력 계약 체크리스트 + "사용자가 선호, 제외, 피드백, 교정을 말했으면 `astack-memory add`. 기록에서 다시 알 수 있는 사실은 기록하지 않음"
6. Gotchas: 실제로 겪은 함정 (마이그레이션에서 옮겨옴)
- 시작 시: `design`을 먼저 읽고, `astack-memory search <관련 키>`로 관련 기억(교정 등)을 읽는다.

### 6.3 사용자 동사

#### quest — 만들어두기
- **입력**: 한 줄 질문 또는 소스(링크, 파일). **출력**: 코스(지도 + 장).
- **방식**: 비동기. 확인을 기다리지 않는다. 낮에 던진 건 완료 즉시 **무음** 알림, 밤 goal은 아침에 묶어서. 기본 깊이 **Standard**.
- **유형** (질문을 보고 판별):
  | 유형 | 예시 | 결과 |
  |---|---|---|
  | 만들기 | "jev dream 만들고 싶다" | 레포 분해, 하위 질문 × 소스 비교, 스타터 플랜 |
  | 개념 | "타입 좁히기가 뭐지" | 교본 (일반 정의 → 사례 → 깊이) |
  | 사례 | "Harvey는 리서치 랩을 어떻게 굴렸나" | 케이스 스터디 |
  | 실험 | "브라우저별 벤치 속도 비교" | 실험 보고서 + 재현 가능한 벤치 코드 |
- **워크플로**:
  1. 판별: 소스 하나면 해당 원자로 바로. 질문이면 유형 판별.
  2. 분해: 하위 질문 3~6개. 첫 응답("받았어요, 이렇게 쪼개서 볼게요: ①②③, 방향 바꾸려면 답장")으로 보여주고 **기다리지 않는다**. 이 첫 응답은 사용자 머릿속 "열린 고리"를 닫는 신호다.
  3. 수집·선별: GitHub, 엔지니어링 블로그, 발표, 논문, X. 상위 3~5개 (실사용, 최근 활동, 신뢰하는 사람의 언급. 스타 수는 참고만).
  4. 원자 호출: 병렬 서브에이전트로 repo/seminar/interview/paper.
  5. 종합: 코스로 엮기 (아래).
  6. 적재·알림: `docs/astack/quest/<날짜>-<slug>/`, `rooms link`, 시작한 곳으로 알림.
- **코스 구조**:
  ```
  docs/astack/quest/<날짜>-<slug>/
    00-지도.html     입구. 전체 구조, 장별 30초 요약, 읽는 순서 (= 이 방의 map 첫 판)
    01-….html ~ NN   장마다 질문 하나
  ```
  | 규칙 | 내용 |
  |---|---|
  | 한 장 = 한 질문 | 장 제목이 질문 하나로 말해져야 함 |
  | 한 장 = 10~15분 | 넘으면 쪼개고, 너무 짧으면 합친다 |
  | 세 층 + 퀴즈 | 장마다 30초/3분/본문 + 끝에 점검 |
  | 연결 | 이전/다음/지도 링크. 같은 개념은 장이 달라도 같은 이름 |
  | 깊이 | Quick: 지도+5장 / **Standard(기본): 지도+10~12장 (why 장, 실험 또는 실습 장 포함)** / Deep: 지도+20장 이상, 장마다 하위 문서와 실습 ("깊게"라고 할 때) |
  - 만드는 순서: 장 설계(지도 초안) → 장마다 서브에이전트 병렬 집필(클론은 한 번 공유) → 용어 통일·겹침 제거 → 지도 확정.
  - 예시 (Codex CLI, Standard, 실제 구조는 레포 분해 후 확정): 00 지도 / 01 코어와 UI 분리(프로토콜) / 02 에이전트 루프 / 03 도구 실행과 샌드박스 / 04 승인 정책 / 05 세션 저장(jsonl + sqlite 색인) / 06 MCP / 07 멀티 에이전트(spawn_agent) / 08 설정·프로필·모델 / 09 왜 이렇게 만들었나(PR·이슈) / 10 실험(속도·토큰) / 11 실습 / 12 내 일에 쓰면(Alto Rooms 설계와 비교).
- **실험 유형 워크플로**:
  1. 가설과 지표 (페이지 로드, 스냅샷 시간, 액션 지연, 메모리 등)
  2. 기존 벤치 탐색 → 쓸 만하면 재사용
  3. 없으면 제작: 재현 가능한 스크립트 (build-the-lever). 벤치 자체가 남는 자산
  4. 환경 고정: 머신, 버전, 워밍업, 교차 실행, 반복 횟수 기록
  5. 실행: 맥미니에서 밤에 (자원 경쟁 방지)
  6. 분석: 숫자를 제한하는 요인과 엉뚱한 걸 잰 건 아닌지 확인 (explain-the-number)
  7. 보고서: 방법, 차트, 원자료, 재현 명령, 한계. 벤치 코드는 quest 폴더에 보존
- **브라우저 프로필 (실험)**: 기본은 **Aside 실제 프로필** (로그인·권한, 실사용 조건). 사용자가 명시적으로 원함. 가드레일:
  | 가드레일 | 내용 |
  |---|---|
  | 읽기 전용 | 로그인된 사이트에서는 읽고 이동만. 글쓰기, 구매, 삭제, 설정 변경 금지 |
  | 세션 보존 | 실제 프로필의 캐시·쿠키를 지우지 않음. 콜드 스타트 측정만 깨끗한 프로필 |
  | 한 번에 하나 | Aside 프로필 쓰는 goal은 순차. 병렬은 다른 브라우저끼리만 |
  | 부하는 내 쪽에 | 반복 측정은 로컬 테스트 페이지나 자기 서버. 외부 사이트 반복 호출로 계정 제한 금지 |
  - 비교 실험은 "실사용 조건(Aside 프로필)"과 "깨끗한 조건(새 프로필)"을 함께 잰다. 차이가 곧 프로필 상태의 영향.
- **클론 캐시**: `~/.cache/astack/repos/` (Rooms Home·작업 위치 밖. 레포 안 docs HTML이 아티팩트로 잡히는 오염 방지, 재사용).
- **밤 goal**: 9장 참고.

#### study — 깊게 이해하기
- **입력**: 교본(이해물) 하나 + 후속 질문. **출력**: 같은 교본에 덧붙이거나(섹션 추가) 하위 교본 생성. 모든 답은 HTML로 남긴다 (공리 1).
- **방식**: 동기. 사용자가 요청한 집중 공부 시간에만.
- 할 일: 후속 질문 답변(근거 등급 포함), 하위 개념 더 파기, why 조사, 추가 퀴즈. 결과는 원래 방에.

#### recall — 꺼내기
- 새 이해를 만들지 않는다. 재고에서 찾아 꺼낸다.
- **모드**: 주제("브라우저 하네스 관련 뭐 쌓였지?") / 지금 작업(자동, 긴 작업 시작 시) / 기간("지난주") / **`recall now`(딱 하나)**.
- **출력**: 읽을 목록 HTML (각 항목: description 한 줄, 추천 순서, 빈 부분). `now`는 하나만 + 채팅에 경로 한 줄.
- **검색 방법 (Rooms 없이 동작)**: `~/.astack/outputs.log`의 경로들 → 각 파일 `<meta name="description">` + 본문 grep. 로그가 깨지면 설정된 루트(예: `~/personal`, `~/dev`)에서 `docs/astack/**/*.html`을 다시 훑는다. 수천 개가 되면 파생 SQLite 색인을 고려 (v1 없음).
- **선택 기준**: 관련성 + 최신순. 읽음 상태는 알 수 없음 (Rooms 클라이언트 상태). 지금 작업 맥락 우선.

### 6.4 원자 (소스 하나 → 이해물 하나)
| 스킬 | 소스 | 출력 형식 | 자동 선택 | 마이그레이션 원본 |
|---|---|---|---|---|
| `interview` | 팟캐스트, 인터뷰, 대담 영상 | 대화(Q&A)를 보존한 매거진 에디션 | 요청 시만 | Aside `podcast-magazine` |
| `seminar` | 슬라이드 발표 영상 | 스크롤하면 슬라이드가 바뀌는 리포트 | 요청 시만 | Aside `seminar-report` |
| `paper` | 논문 PDF, arXiv | 구조화·시각화한 무손실 리더 (모든 figure 임베드, 선행연구 포스트잇) | 요청 시만 | Aside `paper-lossless-reader` |
| `repo` | 외부 GitHub 레포 | 아키텍처, 핵심 루프, 데이터 흐름, 영리한 부분(파일:줄), why(커밋·PR·이슈 근거, 확신도 등급), 약점 | 요청 시만 | 신규 (pstack how/why 방식 참고) |
| `spec` | 스펙·설계 문서 (구현 전) | 목적 → 구조 → 흐름(인터랙티브) → 결정과 트레이드오프 → 근거. + 확정할 결정 목록(에이전트 제안 vs 사용자 결정 구분), 레거시 충돌 표시, go 전 점검 퀴즈 | **허용** (스펙 저장 시) | Claude Code `html-artifact` |
| `change` | Task 커밋 범위, 브랜치, PR (구현 후) | 만들어진 것(흐름 시각화), 스펙 대비 차이, 에이전트의 임의 결정, 위험한 곳(레거시 접촉, 약한 테스트), 리뷰에서 나온 것, 점검 퀴즈. **Task 단위**와 **Plan 전체 요약** 두 모드 | **허용** (Task 리뷰 통과 시, Plan 완료/PR 시) | 신규 (html-artifact 기반) |

- 원자는 **요약이 아니라 무손실 변환**. "요약해줘"라고 해도 매거진을 만들고, 맨 위 30초/3분 층이 요약 역할.
- 소스가 길면 quest처럼 장으로 나눈다 (예: 3시간 팟캐스트 → 파트별 장 + 지도).
- `spec` 범위: 스펙, PR, 설계 문서만. 기존 html-artifact의 "일반 리포트, 시각 설명"은 `design`의 기본 동작으로 이동. **e2e 문서는 만들지 않는다** (사용자가 안 읽음. e2e 증거는 PR 리뷰 게이트에서 봄).
- `spec`은 astack에서 품질 기준이 가장 높은 원자 (사용자 업무, 설계 권한은 사용자에게 있음).
- `change`는 가볍고 빠르게: 스펙은 이미 이해했으므로 **차이만**.
- `repo`: "남의 레포를 학습 자료로". 내 코드베이스의 동작 설명은 범위 밖 (그건 대화형 how의 몫).

### 6.5 자동 실행
#### feed — 아침 30분
| 단계 | 내용 |
|---|---|
| 소스 | **화이트리스트 YouTube 채널만** (업무 계정에서 실시간으로 읽음). 화이트리스트는 레포가 아니라 `~/.astack/memory.jsonl`의 `told` 기록 |
| 신작 | 지난 실행 이후. 이미 이해물이 있는 소스는 건너뜀 (outputs.log + 본문 원문 링크) |
| 양 | **30분 분량만 만든다.** 많으면 취향 순으로 자르고 나머지는 만들지 않음 (밀린 목록 없음) |
| 구성 | "오늘 30분" HTML 한 장: 깊은 매거진 1~2개(~20분) + 짧은 카드 2~3개(각 3분 층), 읽는 순서대로 |
| 취향 | 기록에서 재구성(만든 이해물, 좋아요) + memory(피드백, 교정) |
| 피드백 | Telegram 답장 "2번 별로"는 memory 기록 → 다음 선택 반영 |
| 시간 | 05:00 생성, 07:00 아침 1통에 포함 |

**초기 화이트리스트 (memory 초기값으로 seed. 레포에 커밋 금지)**: AI Engineer, Lenny's Podcast, Dialectic (Jackson Dahl), David Senra, Invest Like The Best, Y Combinator, Uncapped (Jack Altman), The Pragmatic Engineer, Latent Space.

#### dream — 사람을 위한 저녁 정리 (20:00)
- 입력: 오늘 생긴 이해물 (`outputs.log` + `rooms:created`로 수집. **Rooms 없이 동작**).
- 출력 Journal HTML: 공통 주제, 부딪히는 주장, 새로 생긴 질문(→ 21:00 질문 후보), **간격 복습**(1일·7일·30일 전 이해물에서 1문항씩, 날짜로 선택하므로 상태 불필요), **"내 말로 한 줄"** 질문(답은 Rooms Journal의 "나" 노트로).
- 주 1회 **주간 수렴 모드**: 이번 주 map 변화 + "이번 주 내 일에 쓸 것 3가지" (각 이해물 끝 "그래서 나한테는?"을 모아 좁힘).
- 관심 변화를 발견하면 `astack-memory add`로 **관찰만** 남긴다. 정리(consolidate)는 하지 않는다.
- Rooms가 있으면 `rooms link --journal <날짜>`.
- 한계(v1 허용): 맥미니에서 돌므로 맥미니에서 만든 이해물만 본다.

#### map — 주제 지도 (수렴)
- 방(주제)마다 계속 갱신되는 `map.html` 한 장: 지금까지 알게 된 것, 합의, 부딪히는 주장, 남은 질문, 사용자가 내린 결정.
- 새 이해물이 그 방에 들어올 때 갱신 (비싸면 dream 때 하루 한 번). quest 코스의 `00-지도`가 첫 판.
- 원칙: 문서가 쌓여도 두꺼워지지 않고 더 정확해진다 (converge). 사용자는 20개 대신 지도 한 장을 읽는다.
- v1.1로 미뤘던 `connect`(방 하나 일회성 엮기)를 대체한다.

#### memory — 에이전트를 위한 기억
- 명령: `add`, `search`, `prune`, `consolidate`. 7장.

### 6.6 공통
- **`astack` (입구/라우터)**: 링크면 소스 종류로 원자(YouTube 대담→interview, 슬라이드 발표→seminar, arXiv/PDF→paper, GitHub→repo, 스펙 md→spec), 질문이면 quest, "오늘 정리"면 dream. Telegram에 무엇이든 던질 수 있게 하는 게 목적. (pstack의 poteto-mode, gstack 루트 SKILL.md에 해당)
- **`design`**: 직접 부르지 않는 공통 문서. 다른 모든 스킬이 시작할 때 읽는다. 출력 계약(8장), 이해 원칙 색인(10장), Alto 토큰, 능력 지도, 내장 퀴즈 컴포넌트.
- **`setup`**: 스킬이 아니라 설치 스크립트 (gstack `./setup`처럼). `./setup --host claude|codex|hermes|aside|auto`.

---

## 7. 상태와 기억 (`~/.astack/`)

| 파일 | 역할 |
|---|---|
| `memory.jsonl` | **기억의 진실(SSOT).** 한 줄에 기록 하나 |
| `archive/YYYY-MM-DD.jsonl` | consolidate 직전 상태 (되돌리기, 감사) |
| `outputs.log` | astack이 쓴 이해물 경로 목록 (한 줄 = 경로 하나 + 시각 + 스킬). 지워져도 루트 재스캔으로 복구 |
| `.lock` | consolidate 중에만 잡는 잠금 |
| SQLite | v1 없음. 필요해지면 jsonl에서 만드는 파생 색인 |

- **왜 jsonl인가**: 규모가 작음(수천 줄), 사람이 열어 고침, git으로 두 맥 동기화 시 diff/병합 가능. 짧은 한 줄 append는 동시 쓰기에 안전. (Rooms의 "파일이 진실, SQLite는 파생 색인" 패턴과 동일)
- **gstack 참고**: gstack은 스킬 끝마다 `gstack-learnings-log`로 JSON 한 줄을 `~/.gstack/`에 남기고 `/learn`으로 관리한다. 레포에는 틀만 있고 데이터는 각자 로컬. astack도 같은 구조.
- **pstack 참고**: pstack은 자체 저장소 없이 대화 기록(`~/.claude/projects/*/*.jsonl`)과 git·이슈에서 매번 재구성(recall)하고, 교훈은 스킬 자체를 고쳐서 남긴다. astack은 둘을 섞는다: **취향은 재구성, 재구성 불가능한 것만 기억**.

### 기록 형식
```json
{"type":"exclude","key":"channel:<이름>","insight":"feed에서 제외","source":"told","date":"2026-10-05","host":"hermes"}
{"type":"whitelist","key":"feed:youtube:<채널>","insight":"아침 feed 화이트리스트","source":"told","date":"2026-10-05","host":"aside"}
{"type":"correction","key":"skill:interview","insight":"질문자 발언도 전부 살릴 것","source":"told","date":"2026-10-05","host":"claude"}
{"type":"feedback","key":"feed:2026-10-06#2","insight":"별로: 너무 입문용","source":"told","date":"2026-10-06","host":"hermes"}
{"type":"taste","key":"topic:personal-agent","insight":"최근 2주 quest가 개인 에이전트 메모리로 몰림","confidence":0.7,"source":"observed","date":"2026-10-05","host":"hermes"}
```
- `type`: whitelist | exclude | correction | feedback | taste | preference (확장 가능)
- `source`: told(사용자가 말함) | observed(에이전트가 관찰)

### 누가, 언제 쓰나
- **판단은 에이전트, 형식은 스크립트.** 에이전트가 `astack-memory add '{…}'` 호출 → 스크립트가 스키마 검사, `date`/`host` 자동 부착, append.
- **기록에서 다시 알 수 없는 것만**: 사용자가 말한 선호·제외·피드백·교정, dream이 발견한 관심 변화. 만든/읽은 것, 구독, 좋아요는 쓰지 않는다(재구성).
- **읽기**: 스킬 시작 시 `astack-memory search <키 또는 접두사>`.

### consolidate (에이전트를 위한 dream, 20:30)
1. `.lock` 획득, 현재 파일을 `archive/오늘.jsonl`로 복사.
2. 중복 합치기. 모순: 최신 told > 오래된 observed. 오래된 observed는 confidence 감쇠. told는 취소 전까지 유지.
3. 반복 교정 승격 (encode-lessons): **내 취향**(같은 스킬 교정 N회)은 기억 안의 강한 규칙으로. **스킬 결함**(같은 실패 반복)은 astack 레포 패치를 **제안만** (자동 적용 금지).
4. 임시 파일에 쓰고 rename으로 원자적 교체. 잠금 해제.
5. 바뀐 게 있으면 변경 보고 HTML (전후 차이, 승격, 패치 제안).
- **사람용 dream과 분리하는 이유**: 진실이 다르다 (HTML 산출물 vs jsonl 상태). 둘이 만나는 곳은 `memory add` 한 줄뿐.

---

## 8. 출력 계약 (`design/references/output.md`)

| 항목 | 규칙 |
|---|---|
| 형식 | self-contained HTML 한 장. 이미지는 base64 등으로 내장 (`scripts/inline-assets`). 상대경로 자산 금지 — Rooms는 **링크가 있는 위치 기준**으로 파일을 제공하므로 옆 폴더 이미지가 깨진다 |
| 격리 환경 | Rooms는 아티팩트를 별도 origin(포트 4318)의 `CSP: sandbox allow-scripts allow-popups` (allow-same-origin 없음)로 연다 → localStorage 불가, API 키 금지, 필수 외부 호출 금지. 인터랙션은 미리 계산해 페이지 안 JS로 |
| 경로 | `<작업 위치>/docs/astack/<스킬>/YYYY-MM-DD-<slug>.html`, 여러 파일이면 같은 이름 폴더. 프로젝트 규칙 우선 |
| 메타 | `<meta name="description">`(한두 줄 요약, HTML 표준, 필수), `rooms:created`(ISO, 필수 — 파일이 이동·클론돼도 날짜 유지), `rooms:machine`(필수 — v2 묻기에서 세션이 어느 머신인지), 선택 `rooms:agent`, `rooms:session`, `<title>` |
| 세 층 | 맨 위 30초 층(무엇이고 왜 중요한지 2줄) + 3분 층(핵심 구조 하나 + 그림 하나 + 퀴즈 하나), 그 아래 30분 본문 |
| 내장 점검 | 챕터 끝 접힌 블록. **객관식**: 즉시 채점, 오답마다 "흔한 오해" 해설 + 원문 링크. **주관식(단답)**: 정답 공개. **서술형**: 모범답안 + 핵심 포인트 공개. 질문은 이해형(왜, 만약, 비교, 적용). 상태는 페이지 안에서만 (닫으면 초기화) |
| 출처 | 모든 주장에 원문 위치 (타임스탬프, 페이지, 파일:줄, URL). 원문 URL은 본문에 반드시 등장 (feed 중복 판단에 사용) |
| 근거 등급 | 사실 주장은 확인 / 추론 / 모름. 코드를 그 코드의 의도에 대한 증거로 쓰지 않음 |
| 끝 섹션 | "그래서 나한테는?" (지금 하는 일에 어떻게 연결되는지). 주간 수렴의 입력 |
| 언어 | 한국어. 코드 식별자·원문 인용은 그대로, 설명은 한국어 |
| 디자인 | 바탕·글자·간격은 **Alto 토큰 고정**(alto-rooms 레포의 토큰 파일과 맞출 것). 의미 색(상태, 흐름 강조)만 내용에 맞게. 금지: 그라데이션, 네온, 이모지 불릿, 가운데 정렬 남발, 마케팅 말투. 다크 모드 지원. 모바일 세로 화면에서 읽힐 것 |
| 채팅 응답 | 경로 + 한 줄. 내용은 HTML에만 |
| 완료 후 | `outputs.log`에 기록, `rooms link`가 있으면 호출 |

현재 사용자 디자인 기본값(Aside 메모리 기준, 토큰 확정 전 임시값): bg `#f7f6f3`, surface `#fff`, border `#eae7e0`, ink `#1f2328`, muted `#73757b`, accent `#3a5a7c`, dark bg `#14140f`. 참고: Rooms 스펙 문서 자체는 파란 강조색과 이모지 배지를 쓰고 있다 (Claude Code html-artifact의 "내용에 맞게 색 선택" 규칙 때문). astack에서는 위 규칙으로 통일.

---

## 9. 호출, 스케줄, 예산

### 9.1 세 가지 호출 모드
| 모드 | 언제 | 어떻게 |
|---|---|---|
| 요청 | 사용자가 부탁 | 직접 지정 `/interview <링크>`, 자연어, 던지기(Telegram에 링크·한 줄 → 입구가 판단) |
| 흐름 속 자동 | 다른 작업 중 | 좁은 조건 목록 (pstack 라우터처럼 "이럴 때만", 모든 걸 가로채지 않음) |
| 백그라운드 | 사용자 없이 | 맥미니 Hermes cron, Telegram 토픽 |

입구 계약: `astack quest "…"` 명령 하나. 어느 호스트에서 불러도 같다. Telegram은 그중 하나의 입구 (사용자 기본값).

### 9.2 흐름 속 자동 조건
| 조건 | 발동 | 연결 |
|---|---|---|
| 스펙·설계 문서 저장 | `spec` | **이미 brainstorming과 함께 동작 중. 추가 설정 없음.** 건너뛰는 일이 생기면 CLAUDE.md로 보강 |
| SDD에서 Task 리뷰 통과 | `change` (Task 단위, 백그라운드 서브에이전트) | 전역 CLAUDE.md |
| Plan 완료 / PR 열림 | `change` (Plan 요약) | 전역 CLAUDE.md |
| 5분 넘는 작업 시작 | `recall now` → 하나 처방. 재고 없으면 같은 맥락 이해물 1개 백그라운드 생성 | 전역 CLAUDE.md |

전역 CLAUDE.md 스니펫 (`recipes/claude/CLAUDE.md.snippet`):
```markdown
## astack
- subagent-driven-development에서 Task가 리뷰를 통과할 때마다, 그 Task 커밋 범위로
  astack:change를 백그라운드 서브에이전트로 실행하고 경로를 한 줄로 알려줘. 작업은 멈추지 마.
- Plan이 끝나거나 PR을 열면 astack:change로 Plan 전체 요약을 만들어줘.
- 5분 넘게 걸릴 작업을 시작할 때 astack:recall now로 지금 읽을 것 하나를 알려줘.
```
- 지시가 무시되면 Claude Code 훅(서브에이전트 종료, PR 생성 시점)으로 전환. 첫 구현 때 실제 SDD 실행에서 발동을 검증할 것.
- superpowers 근거: `using-superpowers`의 "User Instructions (CLAUDE.md, AGENTS.md…) take precedence over skills". brainstorming의 "Architectural 경로 후 부르는 스킬은 오직 writing-plans" 문구는 승인 이후 얘기라 spec과 충돌하지 않음.
- **참고: 레거시 지도**: brainstorming은 "Follow existing patterns"라고 지시한다. 지저분한 코드베이스에서는 레포 AGENTS.md에 "따라 하지 말 패턴 / 목표 패턴"을 두는 것을 권장 (astack 범위 밖, setup 안내만).

### 9.3 알림
- 시작한 곳으로 답한다. 보내는 쪽은 항상 호스트(Hermes 등), astack은 일만 한다.
- 사용자 기본값: Telegram. 낮 quest = 완료 즉시 **무음 메시지**(도착하되 집중을 깨지 않음). 밤 goal + feed = 07:00 1통. dream = 20:00 1통. 질문 받기 = 21:00 1통.
- 메시지 = 30초 층(2~3줄) + 링크(또는 Hermes가 HTML 파일 첨부). 본체는 HTML.

### 9.4 스케줄 (맥미니 Hermes)
| 시간 | 작업 |
|---|---|
| 05:00 | `feed` → "오늘 30분" |
| 07:00 | 아침 1통: feed + 밤 goal 결과 |
| 20:00 | `dream` (주 1회 주간 수렴 모드) → Journal → Telegram |
| 20:30 | `memory consolidate` |
| 21:00 | "오늘 밤 돌릴 질문" 받기: 후보(오늘 작업에서 나온 질문, dream의 새 질문, 요즘 관심사) + 자유 입력. 답 없으면 후보 1번만 |
| 01:00~ | 밤 goal 실행 (**최대 3개**) |
| 상시 | Telegram Quest 토픽 → `quest` 자동 로드 |

### 9.5 밤 goal
| 항목 | 설계 |
|---|---|
| 성공 조건 | 유형별 판정. 실험: 반복 3회 + 편차 기준 + 보고서·재현 명령. 코스: 모든 장에 세 층·퀴즈, 지도에서 모든 장 도달, 원문 근거 |
| 반복 | 조건 만족 또는 시간·예산 소진까지 (pstack Autonomous run 방식) |
| 결정 기록 | 무엇을 왜 정했는지 남김 (pstack show-me-your-work 방식). 아침에 결과를 믿을 수 있게 |
| 실패 대비 | 체크포인트에서 재개 (pstack pause/resume 방식) |
| 개수 | 최대 3개. Aside 프로필 쓰는 goal은 순차 |
| 아침 | goal별 성공 여부, 핵심 3줄, 지도 링크 |

### 9.6 예산 상한
자동 작업엔 스스로 멈출 지점이 없다. 실제 위험은 비용보다 **구독 사용량 한도**(밤사이 소진 → 낮 업무 에이전트 정지). 토큰 대신 개수로.
| 자동 작업 | 상한 |
|---|---|
| feed | 아침 30분 분량 |
| 긴 작업 시작 시 선생성 | 작업당 1개 |
| 밤 goal | 최대 3개 |
| change (Task 단위) | 상한 없음 (업무 이해 최우선) |
| 사용자가 시작한 quest, spec | 상한 없음 |
- 무거운 자동 작업은 밤에만. 2주 운영 후 조정. 우선순위: 지금 작업(spec, change, recall) > 사용자 quest와 밤 goal > feed.

---

## 10. 이해 원칙 (`design/principles/*.md`, pstack 원칙 부품 방식)

pstack은 원칙마다 짧은 스킬(`principle-*`, 1~2.5천 자, `disable-model-invocation: true`, description "Apply when [상황]. [요지]")을 두고, 라우터(poteto-mode)에 "언제 적용하는지 + 요지" 색인만 둔다. 응답에서 적용한 원칙의 이름을 대게 하고 "이번 세션에 전문을 읽은 원칙만 인용"하게 한다. 같은 교정이 두 번 나오면 원칙이나 lint/스크립트로 올린다 (encode-lessons-in-structure: 일회성 → 메모, 반복 → 스킬/lint, 시스템적 → 원칙).

| 원칙 | 언제 | 요지 | 출처 |
|---|---|---|---|
| convert-not-summarize | 모든 원자 | 정보량은 그대로, 형식만 바꾼다 | podcast-magazine, paper reader |
| three-layers | 모든 이해물 | 30초 / 3분 / 30분 | 공리 7 |
| definition-then-case | 개념 설명 | 일반 정의(통용 이름과 함께) → 지금 사례 → 깊이 | pstack teach |
| build-up-diagrams | 부품 3개 이상 | 한 장에 다 그리지 말고 A→B, +C, +돌아오는 화살표처럼 하나씩 쌓아 그린다 | pstack teach |
| visual-per-paragraph | 설명 문단 | 문단마다 옆에 그 내용을 설명하는 시각화 (장식 아이콘·반복 다이어그램은 불인정) | html-artifact |
| evidence-tiers | 사실 주장 | 확인 / 추론 / 모름. 모르는 건 모른다고. 코드는 메커니즘이지 동기가 아님 | pstack why, html-artifact |
| anchor-to-source | 모든 주장 | 원문 위치로 바로 갈 수 있게 | seminar, paper |
| one-name-per-concept | 글쓰기 | 개념 하나에 이름 하나 | pstack unslop |
| retrieval-check | 챕터 끝 | 이해를 묻는 질문. 암기 금지. 오답 = 오해 진단 | 학습 과학 |
| no-slop-ko | 모든 글 | 한국어 AI 말투 금지. 가능하면 `scripts/slop-scan`으로 | pstack unslop, gstack slop-scan |
| explain-the-number | 실험 | 숫자를 제한하는 요인과 엉뚱한 걸 잰 게 아닌지 확인 | pstack |
| build-the-lever | 실험 | 손으로 재지 말고 다시 돌릴 수 있는 벤치를 만든다 | pstack |
| converge | dream, map | 새 이해물이 들어와도 문서가 두꺼워지지 않고 정확해지게. "그래서 나한테는?"을 행동 3가지로 좁힌다 | 수렴층 |

pstack teach에서 가져올 문체 규칙 (한국어로 옮겨 적용): 비유·예고 말고 구체적 메커니즘, 틀 짓는 말("핵심은", "TL;DR") 금지, 대칭 문장·깔끔한 마무리 문장 금지, 가장 작은 완결 답부터.

---

## 11. 능력과 호스트

### 11.1 능력 지도 (`design/references/capabilities.md`)
스킬 본문에는 능력 이름만. 호스트 차이는 이 문서 한 곳에 (pstack이 `codex-tools.md`, `pi-tools.md`로 하는 방식. gstack식 템플릿 생성은 쓰지 않음).
| 능력 | Aside | 터미널 호스트 (Claude Code, Codex, Hermes) | 주의 |
|---|---|---|---|
| transcript | `youtube.getTranscript(id,{lang,includeTimestamp:true})` | `scripts/transcript <url> --lang en` (yt-dlp) | 자동 자막만 있으면 lang 명시, 첫 줄 확인. 긴 자막은 타임스탬프 버전으로 받아 분할 읽기 |
| pdf-figures | REPL 크롭 | `scripts/pdf-figures` | 모든 figure 추출 |
| clone | Bash git | `git clone --depth 1` → `~/.cache/astack/repos/` | |
| subscriptions | 로그인 YouTube 구독(업무 계정), X | `aside` CLI로 위임 | 실시간으로만, 저장 금지 |
| subagent | subagent 도구 | Claude Code: Agent(`general-purpose`). Codex: `spawn_agent`/`wait_agent` (`~/.codex/config.toml`에 `multi_agent = true`). Hermes: delegate | 미지원 시 순차, 결과 형식 동일 |
| inline-assets | REPL | `scripts/inline-assets` | self-contained 보장 |
| rooms-link | Bash | `rooms link` 있으면 호출 | 없으면 건너뜀 |
| memory | Bash | `bin/astack-memory` | |
| browser-drive (실험) | Aside REPL | `aside repl`, computer use, browser-harness | 9장/6.3 가드레일 |

### 11.2 호스트
| 호스트 | 머신 | 설치 | 맡는 일 |
|---|---|---|---|
| Claude Code | 메인 맥(+맥미니) | 플러그인 `.claude-plugin/` + 전역 CLAUDE.md 블록 | spec, change, recall now, 직접 요청 |
| Codex | 메인 맥(+맥미니) | 플러그인 `.codex-plugin/`, multi_agent | 직접 요청 |
| Hermes | 맥미니 | `.hermes-plugin/` (superpowers는 `hermes plugins install obra/superpowers --enable` 방식), cron, Telegram DM 토픽(`platforms.telegram.extra.dm_topics`에 `skill:` 바인딩), 작업 위치 `~/personal/notes` | feed, dream, memory consolidate, 21:00 질문 받기, 밤 goal, Telegram 입구와 알림 |
| Aside | 메인 맥, 맥미니 | `~/.aside/u/0/skills/user/astack-*`로 복사 (Aside는 평평한 스킬 폴더라 `astack-` 접두어). `writableRoots`에 `~/rooms`(Rooms 링크용)와 작업 위치 추가. 계정 스킬은 머신 간 동기화되지 않음 (setup이 매번 복사) | 로그인이 필요한 소스, 실험(Aside 프로필), 직접 요청 |

참고 자료 (호스트):
- Hermes: https://github.com/NousResearch/hermes-agent , cron https://hermes-agent.nousresearch.com/docs/user-guide/features/cron (no-agent 스크립트 잡은 stdout이 비면 전송 안 함), Telegram 토픽 https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram
- superpowers 포팅 가이드: `docs/porting-to-a-new-harness.md`
- pstack 포팅판 매니페스트·훅: https://github.com/michael-denyer/pstack-claude (`plugins/pstack/hooks/`, `.claude-plugin/`, `.agents/plugins/`)

---

## 12. Rooms 접점

astack과 Rooms의 접점은 **두 개뿐**. astack은 Rooms API(`/v1/*`)를 쓰지 않는다. dream, recall, 알림, 원격 보기 모두 Rooms 없이 동작.
| 접점 | 성격 | Rooms가 없으면 |
|---|---|---|
| HTML 메타: `description` + `rooms:created`, `rooms:machine` | 데이터 | 무시되는 태그 |
| `rooms link <파일> [--room <이름>] [--journal <날짜>]` | 명령 호출 | 명령 없음 → 건너뜀 |

방 배정(Rooms 쪽 정책이지만 astack이 힌트로 `--room` 전달): quest는 `<slug>` 방, feed·원자는 주제 방(모르면 inbox), dream은 Journal, spec·change는 프로젝트 방.

### Alto Rooms 스펙에 추가할 것 (별도 작업, alto-rooms 레포)
- `<meta name="description">` 색인 + 카드에 한 줄 설명 표시 (Rooms 스펙의 "한 줄 설명" 후속 이슈 해결).
- `/v1/search`: FTS5로 제목·description·본문 검색 (사람용. astack은 사용 안 함). Rooms는 이미 SQLite(`index.sqlite`)를 도입했고 스펙에 "본문 검색(FTS5) 추가 가능"이 있음.
- `rooms link` CLI: 방 선택, 확신 없으면 inbox, `--journal`. 링크 정책(원본이 있으면 링크, 원본 위치 유지)은 Rooms 소유.
- 멀티디바이스: 머신별 독립 Home (추상화 변경 없음). 통합은 v2 클라이언트 페더레이션(클라이언트가 여러 roomsd에 동시 접속, 다른 머신 방은 읽기 전용).
- roomsd: launchd 상주, 데스크탑 앱 없이 단독 실행 (스펙 Open Question 2 → 상주로 확정). 원격 리스너는 실행 플래그(예: `roomsd --remote`)로.
- 모르는 메타는 무시한다는 규칙 명시.
- 참고: Rooms 원격은 읽기 전용, 아티팩트는 별도 origin sandbox → astack 출력 계약의 격리 제약 근거.

---

## 13. 레포 구조

```
astack/
  README.md            무엇, 왜, 설치. 경계 문장
  AXIOMS.md            공리 7개 (gstack ETHOS.md 역할)
  .claude-plugin/  plugin.json, marketplace.json
  .codex-plugin/   plugin.json
  .hermes-plugin/  plugin.yaml, __init__.py
  setup                --host claude|codex|hermes|aside|auto
  recipes/
    claude/CLAUDE.md.snippet       9.2 블록
    hermes/cron.yaml               9.4 스케줄
    hermes/telegram-topics.yaml    Quest 토픽 + skill 바인딩
    aside/permissions.md           writableRoots, 작업 위치
    static-server.md               선택: 맥미니 정적 서버 + Tailscale (Funnel 금지)
  bin/
    astack-memory      add | search | prune | consolidate
  skills/
    astack/            입구
    quest/  study/  recall/
    interview/  seminar/  paper/  repo/  spec/  change/
    feed/  dream/  map/  memory/
    design/
      SKILL.md                    색인 (원칙, 참조 문서)
      assets/alto.css             토큰
      assets/quiz.js              내장 점검 컴포넌트 (객관식 채점, 모범답안 토글)
      references/output.md        출력 계약
      references/capabilities.md  능력 지도
      references/layers.md        세 층 작성법
      principles/*.md             이해 원칙
  scripts/             transcript · pdf-figures · inline-assets · slop-scan · check-output
  tests/               스킬별 기준 시나리오 + 샘플 소스
  docs/superpowers/specs/2026-10-05-astack-v1-spec.html
```
- 원자별 템플릿은 각 스킬 `assets/template.html` (마이그레이션 원본의 템플릿에서 시작).
- 레포에 개인 데이터(화이트리스트, 기억) 없음.

---

## 14. 마이그레이션 (기존 스킬 → astack)

### 14.1 원본 경로 (읽고 학습을 추출할 것)
| 원본 | 경로 | 가져갈 것 |
|---|---|---|
| Aside podcast-magazine | `~/.aside/u/0/skills/user/podcast-magazine/SKILL.md`, `assets/template.html` | 대화 보존 매거진 형식, 3-beat 섹션 인트로, AI-slop 카드 패턴 목록, 이미지 대체(Openverse), 섬네일 대체 프레임(i.ytimg.com) 기법 |
| Aside seminar-report | `~/.aside/u/0/skills/user/seminar-report/SKILL.md`, `assets/report-template.html` | 스크롤 연동 메커닉(템플릿 JS), 문장·내용·구조 원칙, gotchas |
| Aside paper-lossless-reader | `~/.aside/u/0/skills/user/paper-lossless-reader/SKILL.md` | 마찰 4종 → 메커니즘 4종, figure 전량 임베드와 크롭, 포스트잇 선행연구, 시각화·구조화·강조·문체 규칙 |
| Aside html-산출물-만들기 | `~/.aside/u/0/skills/user/html-산출물-만들기/SKILL.md` | 디자인 언어(차분/깨끗, AI slop 회피), 완료 전 점검 (저장 위치·대시보드 규칙은 폐기) |
| Claude Code html-artifact | `~/.claude/skills/html-artifact/SKILL.md` (+ `references/dynamic-flow.md`, `references/runtime.md`) | **spec의 원본.** 설명 순서(목적→구조→흐름→결정→근거), 필수 인터랙티브 흐름(Previous/Next/Restart, 시나리오 선택, 단계별 컴포넌트·연결·데이터·상태 동시 갱신), 근거 3단 구분, 가독성 규칙(서술형 제목, 한국어), 문단마다 시각화, 완료 점검(데스크톱/좁은 화면/키보드/모션 감소) |
| 사용자 메모리 (참고) | `~/.aside/u/0/memory/concepts/interview-magazine-html-design.md`, `~/.aside/u/0/memory/MEMORY.md` | 매거진 디자인 결정 이력, 유튜브 자막 언어 함정 등 |

### 14.2 순서
1. **학습 추출**: 위 원본 → `design/principles`, `design/references`, 각 스킬 Gotchas.
2. **구현** (15장 순서).
3. **검증**: 메인 맥 Claude Code와 Aside에 설치, 실제 소스로 한 번씩.
4. **삭제** (검증 후, 사용자 확인 받고): Aside 스킬 4개(podcast-magazine, seminar-report, paper-lossless-reader, html-산출물-만들기), Claude `html-artifact`(→ astack spec으로 대체), `~/.aside/u/0/agents/main/artifacts/results-dashboard.html`, `build-dashboard.js`, `build-dashboard.mjs`. Aside 프로젝트의 "결과물 대시보드 자동 갱신" 에이전트 정리.
   - **유지**: Aside 회사 CS 조회 스킬, `memory-wiki`(Aside 메모리 전용).
   - **기존 HTML 결과물(약 54개, `~/.aside/u/0/agents/main/artifacts/*.html`)은 지우지 않는다.** Rooms 온보딩으로 방에 링크.
5. **Aside 메모리 정리**: 옛 스킬·대시보드를 가리키는 내용 수정 (Aside 쪽 작업).
6. **맥미니**: `./setup --host auto`, Hermes 레시피, memory 초기값(화이트리스트) seed.

---

## 15. 구현 순서와 완료 기준

| 단계 | 내용 | 완료 기준 |
|---|---|---|
| P0 기반 | 레포 스캐폴드, AXIOMS, README, `design`(출력 계약, 토큰, 세 층, quiz.js, 원칙 색인 + 원칙 파일), scripts(inline-assets, check-output, slop-scan), `.claude-plugin` | `check-output`이 self-contained·description·세 층·외부 의존·slop을 검사. Claude Code에 플러그인 설치됨 |
| P1 업무 이해 (최우선) | `spec`(html-artifact 마이그레이션), `change`(Task/Plan), `recall`(now/주제/기간), CLAUDE.md 스니펫, `bin/astack-memory`(add/search만) , outputs.log | **alto-rooms Plan 2 실행에서 dogfood**: Task 리뷰 통과마다 change가 생기고, 긴 작업 시작 시 recall now가 하나를 준다. spec이 brainstorming과 계속 같이 불린다 |
| P2 원자 | interview, seminar, paper, repo (원본 학습 반영) | 각 원자를 실제 소스 1개로 실행, 출력 계약 통과. 긴 소스는 장 분할 |
| P3 탐구와 수렴 | quest(코스, 4유형, 실험 포함), study, astack(입구), map | "Codex CLI 공부"로 Standard 코스(지도+10~12장) 생성. 실험 1건(브라우저 비교 축소판) 보고서+벤치 코드 |
| P4 리듬과 기억 | memory(prune, consolidate), dream(간격 복습, 내 말로 한 줄, 주간 모드), feed(화이트리스트, 30분) | Rooms 없이 dream·recall 동작. consolidate 되돌리기 테스트 |
| P5 호스트 | codex, hermes(cron, Telegram 토픽, 21:00 질문 받기, 밤 goal 3개), aside(복사·권한), setup --host auto | 맥미니에서 하루 사이클(05:00→07:00→20:00→20:30→21:00→01:00) 1회 완주 |
| P6 정리 | 마이그레이션 삭제, Aside 메모리 정리, Rooms 스펙 추가분 반영(별도) | 옛 스킬 없이 모든 시나리오 동작 |

---

## 16. 테스트

| 대상 | 방법 |
|---|---|
| 각 스킬 | superpowers `writing-skills` 방식 (문서용 TDD): 스킬 없이 돌린 결과(기준 실패)를 먼저 보고, 스킬이 있을 때 출력 계약·원칙을 지키는지. "실패를 보지 않았다면 스킬이 맞는 걸 가르치는지 모른다" |
| 출력 계약 | `scripts/check-output`: self-contained, description, rooms 메타, 세 층, 외부 의존, slop 패턴, 퀴즈 존재 |
| 흐름 속 자동 | 실제 SDD 실행에서 change·recall now 발동 여부 |
| memory | 동시 add, consolidate 되돌리기, 모순 해결 규칙, 승격 제안 |
| Rooms 없이 | Rooms 미설치 상태에서 dream, recall |
| 모바일 | 좁은 화면에서 세 층·퀴즈 사용 가능 |

---

## 17. 참고 자료 (조사 결과 요약)

- **superpowers** (https://github.com/obra/superpowers, ~29.5만 스타): 스킬 15개. 기본 흐름 brainstorming → using-git-worktrees → writing-plans → subagent-driven-development → TDD → requesting-code-review → finishing-a-development-branch. 세션 시작 부트스트랩(using-superpowers, "1%라도 해당하면 반드시"). 새 스킬 기여는 받지 않음. brainstorming: Spike/Bounded/Architectural 3경로, HARD-GATE(대화 설계 승인 → 스펙 작성만 허용 → 스펙 승인 → writing-plans만 허용), 스펙은 `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`, 8단계 "User reviews written spec"에서 대기, Visual Companion(대화 중 브라우저 목업, 일회성).
- **gstack** (https://github.com/garrytan/gstack, ~13.5만 스타): 스킬 55개(office-hours, plan-ceo-review, review, qa, ship, browse 등). `SKILL.md.tmpl` + `hosts/*.ts`로 호스트별 생성. `ETHOS.md`(Boil the Ocean, Search Before Building, User Sovereignty). learnings 로그(`~/.gstack/`, `/learn`) + gbrain(로컬 PGLite/Supabase 지식 베이스, MCP). `browse`는 Aside 엔진을 쓸 수 있음.
- **pstack** (원본 https://github.com/cursor/plugins/tree/main/pstack, Lauren Tan, MIT / Claude·Codex 포팅 https://github.com/michael-denyer/pstack-claude): 스킬 57개 중 `principle-*` 24~27개. `poteto-mode` 라우터 + 플레이북(Investigation, Bug fix, Feature, Prototype, Multi-phase plan, Autonomous run, Orchestrate, Babysit, Shipping 등, 프로젝트 플레이북 `.agents/playbooks/` 확장). SessionStart 훅이 좁은 조건 지시문 주입("여러 파일·설계 선택·원인 모를 버그면 poteto-mode"), superpowers와 공존 명시, `session hook: off`로 끔. `teach`(how+why를 엮어 대화로 가르침, 다이어그램 쌓아 그리기, 퀴즈 금지), `how`(탐색 에이전트 2~4 → 설명 에이전트, 섹션 Overview/Key Concepts/How It Works/Where Things Live/Gotchas, 느슨한 틀), `why`(코드 닻 → git blame/log/gh pr → 7개 증거 범주 병렬 조사 → 확신도 등급 [Direct]/[Supported]/[Inferred]/Speculative/Unknown, 정확한 구조 강제, "What We Don't Know" 필수), `recall`(대화 기록 재구성), `create-verification-skill`(프로젝트 `.claude/skills/verify/` 생성: Launch/Doctor/Drive/Evidence/Cleanup/features 지도).
- **Hermes Agent** (Nous Research): Telegram·Discord·Slack·WhatsApp·Signal·Email·CLI 게이트웨이, 자체 메모리와 사용자 모델(Honcho), 스킬 자동 생성·개선, agentskills.io 호환, cron(플랫폼 전달), 격리 서브에이전트, MCP.
- **Aside CLI/MCP**: https://docs.aside.com/help/developers

---

## 18. 결정 로그 (왜 이렇게 됐나)

1. 이름 `astack` (Alto Computer, gstack/pstack 계열). 레포 `alto-computer/astack`.
2. astack = 이해만. 개발 프로세스는 superpowers. pstack 메인 교체는 기각(지저분한 코드베이스에서 자율 설계 위험).
3. 원자 이름 = 소스 종류 (`/repo <url>`처럼 "뭘 넣을지"만 알면 명령이 정해짐).
4. 모든 산출물 HTML (Rooms가 모든 에이전트 산출물을 HTML로 가정) → 퀴즈·질의응답도 HTML.
5. 저장은 환경을 따름 (superpowers의 `<프로젝트>/docs/superpowers/` 관례). 전역 폴더 `~/alto` 안은 기각.
6. Rooms 링크는 Rooms의 정책·명령(`rooms link`). astack은 호출만.
7. Rooms 멀티디바이스: 머신별 독립 Home으로 결합도·추상화 변경 0.
8. 메타는 HTML 표준 `description` + 기존 `rooms:*`만. `astack:topics/source`는 전문 검색·본문 링크로 대체. 이유: Rooms는 AI를 안 하므로 요약만은 producer가 파일에 넣어야 함.
9. 개인 데이터는 레포에 없음. `~/.astack/` 로컬 기억(gstack 방식) + 취향 재구성(pstack 방식).
10. 사람용 dream(HTML)과 에이전트용 consolidate(jsonl)는 진실이 달라 분리.
11. 공리 6(비동기, 넉넉히)에 예외 없음: 설계 관문은 superpowers HARD-GATE가 이미 담당.
12. 공리 7(보여주는 건 적게): 사용자가 "다 이해할 수 있을까, 컨텍스트 스위칭" 우려 → 서랍, 같은 맥락, 세 층, 하나만.
13. 업무 대기 시간 이해(change 파이프라이닝)가 최우선 가치 (3시간 SDD 사례).
14. 점검은 HTML: 객관식 즉시 채점, 주관식·서술형 모범답안. AI 채점 없음.
15. quest 결과 = 코스(지도 + 장). 토큰은 많으므로 기본 Standard. 입구는 지도 한 장.
16. quest에 실험 유형. 실험은 Aside 실제 프로필 기본 + 가드레일 (사용자: "그래야 권한이 좋지").
17. feed는 화이트리스트 YouTube 9개, 아침 30분만. 취미 브리프는 Instinct.
18. 예측 quest는 에이전트 단독 선택 대신 21:00 질문 받기(적중률) + 답 없으면 1개.
19. 밤 goal 최대 3개, 성공 조건 기반 반복.
20. 수렴층: map(주제 지도), dream 간격 복습·내 말로 한 줄·주간 수렴. 낮 quest 알림은 무음.
21. 자동 발동은 좁은 조건 목록(pstack 라우터 방식). spec 자동은 이미 동작하므로 추가 설정 없음.

---

## 19. 열린 질문 (기본값으로 진행하고 계획서에 표시)

| 질문 | 기본값 |
|---|---|
| 동사 이름 | `quest` / `study` / `recall` |
| interview와 seminar를 `video`로 합칠지 | 분리 유지 |
| Aside 스킬 이름 충돌 | Aside에만 `astack-` 접두어 |
| Task 단위 change 비용 | 상한 없이 시작, 2주 뒤 확인 |
| map 갱신 시점 | 새 이해물 유입 시. 비싸면 dream 때 하루 한 번 |
| 밤 goal 성공 조건 수치 | 유형별 기본값으로 시작, 2주 후 조정 |
| 실험용 깨끗한 프로필 | Aside 별도 프로필 또는 헤드리스 새 프로필, 구현 시 결정 |
| feed 30분 계산 | 본문 길이로 읽기 시간 추정, 2주 체감으로 조정 |
| 흐름 속 자동 신뢰성 | CLAUDE.md 지시로 시작, 실패하면 훅 |
| 레포 공개 여부 | 개인 데이터 없음 → public 가능. 사용자 결정 |
| Alto 토큰 실제 값 | alto-rooms 레포 토큰 파일과 맞춤 |
| dream이 맥미니 결과물만 봄 | v1 허용, Rooms 페더레이션 때 해결 |

---

## 20. 2026-10-05 명료화 (이 장이 위 내용보다 우선한다)

설계 대화 이후 사용자와 함께 정한 것. 위 장과 다르면 이 장이 이긴다.

### 20.1 결정 목록

| # | 결정 | 근거 |
|---|---|---|
| C1 | 레포는 `~/personal/astack`. 커밋은 개인 이메일 | 사용자 결정 |
| C2 | 스크립트는 Python 3 표준 라이브러리, 테스트는 unittest. 문법 강조만 빌드 도구에서 Pygments 허용 | 사용자 결정 |
| C3 | Alto 토큰은 `~/personal/alto-site/design/tokens.css` v3 그대로. 이해물의 강조색은 실(`#e31c5f`), 진행 막대는 항상 실(`#ff385c`) | 사용자 결정. Rooms 화면의 "빨강은 세 곳만" 규칙과 별개 |
| C4 | 기존 `~/.claude/skills/html-artifact`는 P1 검증 뒤 `~/.claude/skills-disabled/`로 옮긴다. 삭제는 P6 | 사용자 결정 |
| C5 | 얇은 하네스. 스크립트는 `bin/astack` 하나(`check`, `done`, `memory`, `recall`). 원칙은 `design/SKILL.md` 한 장에 색인 | 사용자 결정 |
| C6 | 템플릿은 실험으로 정한다. 사용자가 "정답"이라고 고른 결과물의 배치를 그대로 두고 디자인 디테일(색, 글꼴, 라벨, 반경)만 Alto로 바꾼다 | 사용자 결정 |
| C7 | 확정된 템플릿: interview = podcast-magazine, seminar = seminar-report, spec = 아래 20.3 | 사용자 결정 |
| C8 | 캐릭터(Clew)는 의미 없이 넣지 않는다. 그림이 없으면 비워 둔다 | 사용자 피드백 |
| C9 | 메타 줄은 회색 한 줄, 세 항목까지(스킬 · 범위나 날짜 · 읽는 시간). 링크·배지 없음 | 사용자 결정 |
| C10 | `rooms:created`, `rooms:machine`, `description`은 `<head>` 맨 앞, 앞 64KB 안. `rooms:created`는 RFC3339 | Rooms `meta.rs` (HEAD_LIMIT 64KB, RFC3339만 인정) |
| C11 | 완료 처리는 `astack done <file> --skill <s>`: check → `~/.astack/outputs.log`(TSV: 시각, 스킬, 절대경로) → `rooms link` 있으면 호출 | 에이전트 제안, 사용자 승인 |
| C12 | spec의 "확정할 결정"은 페이지에서 고르고 요약 문장을 복사해 채팅에 붙인다 | Rooms 샌드박스에서 저장 불가 |

### 20.2 글쓰기 지침 (모든 이해물)

- 두괄식. 결론 먼저, 근거는 뒤에.
- 개조식. 긴 문단 대신 짧은 줄. 단, 줄만 나열하지 않고 맥락이 이해되게 설명적으로 쓴다(앞뒤가 왜 이어지는지).
- 주요 동작 흐름에는 "왜 이렇게 동작하도록 설계했나"를 반드시 붙인다. 근거(스펙 절, 커밋, 대안과 기각 이유)와 근거 등급까지.
- 누가 봐도 아는 말. 전문 용어는 처음 나올 때 한 줄로 풀어 쓴다.
- 문장은 짧게. 한 문장에 생각 하나. 두세 줄마다 줄을 바꾼다.
- AI 말투 금지. "핵심은", "사실상", "매우", "해당", 대칭 문장, 깔끔한 마무리 문장을 쓰지 않는다.
- AI가 쓴 글은 출처 줄에 "Claude Code가 썼습니다"와 요청 원문을 남긴다.
- 원문 인용은 원문 그대로 두고 해설은 옆에 따로 둔다.

### 20.3 spec 이해물의 구성 (확정)

레퍼런스: `references/spec-reference-rooms-v1.html` (Alto Rooms v1 스펙을 이 구성으로 만든 것).

화면: 본문 | 시각화 2단. 문서는 한 가지 모습뿐(요지·세부 전환 없음). 코드는 본문 안.

| 장 | 내용 |
|---|---|
| 0 Overview | 30초 두 줄, 3분 지도 |
| 1 관심사와 아키텍처 | 관심사 카드(우리 것 / 바깥, 왜 있어야 하나, 없으면, 꼭 있어야 하나). 바깥은 "우리가 정하는 계약"을 적는다. 큰 그림 → 실제 폴더 구조 → 모듈 관계 → 코어 내부. 헷갈릴 만한 경계(예: core vs daemon)는 차이 표 + 실제 코드 + "잘못 놓은 예" 하나 |
| 2 주요 유저 스토리의 데이터 흐름 | 맨 위에 유저 스토리 표(6개 안팎). 2.N은 유저가 겪는 일로 시작. 핵심 스토리만 2.N.M 기술 단계로 내려가 실제 호출부 코드를 보여준다. 각 흐름과 단계에 "왜 이렇게 설계했나" 줄 |
| 3 에러 흐름 | 맨 위 표(무엇이 잘못되나 / 사용자에게 보이는 것 / 처리). 3.N마다 실제 코드 |
| 4 가정·전제·결정 리뷰 | 흐름 뒤에 둔다. 칸: 종류, 무엇을(누가 정했나), 근거(외부 사례 / 대안 비교 / 측정 / 코드베이스 / 사용자 결정 / 근거 없음), 틀리면 깨지는 것, 확인한 곳, 흐름 링크. 근거 없음은 빨간 줄 |
| 5 비즈니스 로직 | 알아야 할 규칙과 동작 방식 |
| 부록 | Seam, Contract, AC 등 원문 전문(접힘) |

시각화 규칙:
- 그림에는 관심사 색을 쓴다. 본문 글자에는 색을 쓰지 않는다(굵게만).
- 실선 = 우리가 만드는 것, 점선 = 바깥, 빨간 실 = 지금 보는 단계(흐르는 애니메이션, 모션 줄이기면 정지).
- 흐름은 관심사별 세로 레인의 시퀀스 그림. 에러는 실패 지점부터 빨간 점선.
- 코드는 문법 강조 + 원본 파일 줄 번호. 주석은 연한 노란 배경.
- 목차는 화면 가장자리 짧은 선(—). 가리키면 제목이 펼쳐진다.
- 다양한 시각화(mermaid, 인터랙티브, SVG 애니메이션, 손그림 느낌)를 써도 된다. 단, 이해를 돕지 않는 장식은 금지.

### 20.4 사용자가 실제로 묻는 질문 (최근 30일, 544개)

이해물이 먼저 답해야 하는 질문. 많은 순: 왜·근본 원인(커밋·의도) / 유저 경험 / 데이터 흐름·타이밍 / 용어 뜻·모호한 이름 / 배포 대상·순서 / 사이드이펙트·영향 범위 / 전후 차이·안 바뀐 것 / 테스트·내가 할 일 / 대안·다른 제품 사례 / 코드 품질 / 숫자의 분모 / 큰 그림부터.

change 이해물은 이 순서를 따른다: 유저 경험 before→after → 안 바뀐 것 → 흐름·타이밍 → 왜 → 결정과 대안 → 위험·영향 범위 → 배포·검증(대상, 순서, 내가 할 일).

### 20.5 레퍼런스 파일

- `references/spec-reference-rooms-v1.html`: spec 구성 레퍼런스(위 20.3)
- `references/interview-reference-magazine.html`, `references/seminar-reference-report.html`: 확정 템플릿에 Alto 디테일을 덮은 결과. 제3자 사진·발언이 들어 있어 git에 올리지 않는다(.gitignore)
- `references/alto-override.css`: 두 템플릿에 덮은 Alto 디테일
- `references/build_rooms_*.py`: 레퍼런스를 만든 스크립트(참고용, 경로가 이 머신에 묶여 있음)
