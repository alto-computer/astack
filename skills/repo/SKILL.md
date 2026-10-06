---
name: repo
description: Use when 사용자가 외부 GitHub 레포를 학습 자료로 읽어 이해물로 만들어 달라고 요청할 때. "이 레포 분석해줘", "어떻게 만들었는지 HTML로", "/repo <링크>". 내 코드베이스 동작 설명이나 링크만 붙여넣었을 때는 쓰지 않는다.
---

# astack repo — 남의 레포를 학습 자료로

**약속:** 레포를 직접 클론해 읽지 않고도 구조, 핵심 루프, 영리한 부분(파일:줄), 그렇게 만든 이유와 근거 등급, 약점을 안다.

먼저 `astack:design`을 읽고 `astack memory search skill:repo`로 교정 기록을 본다.

## 원칙
- **evidence-tiers**: 이유에는 등급을 단다. 확인(커밋·PR·이슈·문서에 적힘) / 추론(정황) / 모름. 코드는 동작의 증거이지 의도의 증거가 아니다.
- **anchor-to-source**: 모든 코드는 실제 파일과 실제 줄 번호. `data-path`에 파일 경로, `data-start`에 시작 줄(inline이 `파일:줄`로 보여 준다). `data-lang`은 `auto`(경로 확장자로 정함) 또는 rs/ts/py…. 커밋 고정 링크(`https://github.com/<owner>/<repo>/blob/<커밋>/<파일>#L<줄>`)는 `p.why`의 근거 자리에.
- **definition-then-case**: 낯선 개념은 통용 이름과 일반 정의 → 이 레포의 사례.
- **build-up-diagrams**: 부품이 셋 이상이면 하나씩 쌓아 그린다.

## 워크플로
1. 클론: `git clone --depth 200 <url> ~/.cache/astack/repos/<owner>__<repo>` (있으면 `git -C … pull`). 커밋 해시를 적는다. 작업 폴더에 클론하지 않는다(레포 안 HTML이 이해물로 잡히는 오염).
2. 지도: README, 진입점, 폴더 구조. 부품 3~7개를 정한다.
3. 핵심 루프: 진입점부터 한 바퀴를 따라간다(`rg`). 실제 호출부를 발췌.
4. 데이터 흐름: 유저가 하는 대표 동작 2~3개.
5. 영리한 부분: 보통 방식과 다른 곳. `git log -S`, `git blame`, PR·이슈(`gh` 있으면)로 이유를 찾고 등급을 단다. 얕은 클론이라 `git log -S`/`blame`이 시작 커밋에 닿지 않으면: `git -C <dir> fetch --deepen=2000`(필요한 만큼), 또는 `gh api "repos/<o>/<r>/commits?path=<파일>&per_page=100" --paginate`의 마지막 항목이 그 파일의 첫 커밋 → `gh pr list --search <sha> --state merged`로 PR.
6. 약점: 열린 이슈, TODO, 테스트가 약한 곳, 확장이 막히는 곳. 근거 링크.
7. `assets/template.html`을 채운다. `{{…}}` 자리표시를 모두 채운다. 남으면 check가 막는다 → 메타 → `astack inline` → `astack check` → `astack done <f> --skill repo`.

## 완료 전 체크
- [ ] 코드 발췌의 줄 번호가 실제 파일과 맞다(두 군데 연다)
- [ ] 모든 "왜"에 등급이 있다. 근거 없는 의도를 단정하지 않았다
- [ ] 약점에 근거 링크가 있다
- [ ] `astack check` 에러 0

## Gotchas
- 큰 레포는 `--depth 200`으로도 무겁다. 루프와 흐름에 필요한 경로만 읽는다.
- `--depth 200`은 활발한 레포에서 며칠치뿐이다. 이유를 찾을 때는 5번의 deepen/`gh api`를 쓴다.
- 스타 수는 참고만. 실사용·최근 활동·신뢰하는 사람의 언급이 더 낫다.
- **템플릿은 확정(2026-10-06)이고 쓰면서 고친다.** 사용자가 고치라고 한 점은 `astack memory add`로 교정 기록을 남기고, 같은 교정이 반복되면 템플릿을 고친다.
