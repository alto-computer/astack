# P3 dogfood

| Run | Source | Time | course check | Problems | User verdict |
|---|---|---|---|---|---|
| quest Standard | "Codex CLI 공부" | about 16 min (21:59:04–22:14:59 KST) | rc 0, no output (before I5). Map + 12 chapters; per-file `astack check` 0 errors, 0 warnings | I2, I5, M4, M6, M7, M8, M9, M10, M11 | 대기 |
| experiment | browser automation page-load (small) | about 18 min (21:59:11–22:17 KST) | rc 0, no output (before I5). Map + 5 chapters; per-file `astack check` rc 0 | I5, I7, M2, M5, M11, M12, M13 | 대기 |

Item IDs are from `.superpowers/sdd/2026-10-05-astack-p3-quest/final-review.md`.

## Runs
- quest Standard: `docs/astack/quest/2026-10-05-codex-cli/`. Type 개념, depth Standard. why chapter 02, experiment chapter 08, practice chapter 12. `bench/` holds `sandbox-probe.sh` and three runs. Written in order, with no subagents.
- experiment (Quick): `docs/astack/quest/2026-10-05-browser-load-bench/`. The report is chapter 03. `bench/` holds the generator, the runner, the chart script and two result sets (7 reps and 5 reps). Re-run takes about 2 minutes. Load average was 36–85 during measurement. Only the clean-profile condition was measured.
- After the fix wave, `astack course check` prints `course: 지도 1 · 장 12 · 에러 0 · 경고 0` and `course: 지도 1 · 장 5 · 에러 0 · 경고 0` for these two folders.

## Problems and status
- Fixed in the P3 fix wave: I1–I7, M5, M9, M11.
- M7 is a measurement artifact: headless Chrome `--window-size` does not go below 500px. No change.
- Open: M1–M4, M6, M8, M10, M12–M15.
- Not verified: the parallel chapter path with subagents (SKILL §4.2–4.3). Both runs wrote chapters in order.
- Outside astack: Codex docs redirects and 404s, Codex CLI flag quirks, zsh `=cmd` expansion.
