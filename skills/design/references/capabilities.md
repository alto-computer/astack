# 능력 지도

스킬 본문에는 능력 이름만 쓴다. 호스트 차이는 여기 한 곳에.

| 능력 | Claude Code · Codex (터미널) | Aside | 주의 |
|---|---|---|---|
| transcript | `astack transcript <url> --lang en` | `youtube.getTranscript(id,{lang,includeTimestamp:true})` | 기본은 원 자막(`-orig`) 우선. 출력 머리의 `# lang`과 첫 줄 확인. 429·403이면 `--cookies-from-browser chrome`, 그래도 403이면 yt-dlp 업그레이드 |
| slides | `astack slides <url> <dir> [--crop W:H:X:Y]` | 브라우저 프레임 스캔 | 비슷한 슬라이드 합쳐짐 → `--threshold 0.05`(같은 폴더에 다시 돌려도 됨). stderr의 '슬라이드 없는 구간' 확인. 방송 테두리는 `--crop`. 429·403이면 `--cookies-from-browser chrome`, 그래도 403이면 yt-dlp 업그레이드 |
| pdf-pages | `astack pdf pages <pdf> <dir>` | `aside.pdf.read` | macOS(PDFKit). 첫 실행 10초 |
| pdf-crop | `astack pdf crop <png> x y w h <out>` | canvas 크롭 | 좌표는 쪽 이미지 픽셀 |
| clone | `git clone --depth 200 <url> ~/.cache/astack/repos/<owner>__<repo>` | Bash git | 작업 폴더에 클론하지 않는다 |
| subagent | Agent(`general-purpose`) / Codex `spawn_agent` | subagent 도구 | 없으면 순차 |
| inline-assets | `astack inline <f>` | 같음 | `img src`, `data-img` |
| rooms-link | `astack done`이 `rooms link` 호출 | 같음 | 없으면 건너뜀 |
| memory | `astack memory add|search` | 같음 | |
| route | `astack route "<입력>"` | 같음 | YouTube는 needs_judgment |
| course-check | `astack course check <폴더>` | 같음 | 지도·장·퀴즈·링크 |
