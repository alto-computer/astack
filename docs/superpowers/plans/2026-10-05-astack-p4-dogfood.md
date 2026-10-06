# P4 dogfood

| Run | Source | Time | Check result | Problems | User verdict |
|---|---|---|---|---|---|
| Feed | 45 candidates (9 channels × 5); selected: Lenny's Podcast (37 min) + AI Engineer (21 min, 60 min); real dates from yt-dlp | 7.2 s `feed candidates`; ~12 s each for 3 `transcript` calls (one at a time) | Deep-read (415 KB) + Feed page (33 KB). `astack check` 파일 2 · 에러 0 · 경고 0. Feed page warning fixed. `astack inline`, `astack done` both 0. | 1, 2, 3 | 대기 |
| Dream | Dream collect: 1 today + 1 spaced; memory 10 records | Part of ~11.5 min total (09:28:56 output) | Dream Journal (31 KB). `astack check` 파일 1 · 에러 0 · 경고 0. `astack inline`, `astack done` 0. | 4 | 대기 |
| Memory | Consolidate/restore: 10 records (memory.jsonl) | ~15 s (dry-run, consolidate, restore, re-consolidate) | Dry-run: no changes. Consolidate: archive created, `confidence0` added to file. Restore: byte-identical to pre-consolidate. Re-consolidate: byte-identical to first. No locks. | 5, 6, 7 | 대기 |

Item IDs are from the 7 problems found during steps 2–5.

## Runs

**Feed (step 2):** `astack feed candidates --since 2026-10-03` returned 45 candidates (9 channels × 5). Every `upload_date` was empty; real dates confirmed per video with yt-dlp. Only 4 from 2026-10-03 or later; one from 2026-09-07 was dropped. Deep-read: Lenny's Podcast "Why most actions on the internet will soon be taken by AI" (37 min, 2026-10-04) → interview magazine, 5 parts, 22 chapters. Cards: AI Engineer (21 min, 2026-10-05) and (60 min, 2026-10-06). Deep-read magazine and images in `~/.astack/journal/feed/2026-10-06/`. Feed page in `~/.astack/journal/2026-10-06-feed.html`. No subagents.

**Dream (step 3):** `astack dream collect` returned 1 today (magazine; feed excluded), 1 spaced (quest, 1 day ago). Weekly section removed (Tuesday). Added 1 observed taste record (topic:agents, confidence 0.6). Memory grew from 9 to 10 records. Dream Journal in `~/.astack/journal/2026-10-06.html`. With 1 today item, cross-item themes empty; used themes repeated within the magazine.

**Memory maintenance (steps 4–5):** Consolidate operations: dry-run reported no changes (before 10, after 10); real consolidate created archive in `~/.astack/archive/2026-10-06.jsonl` and updated memory.jsonl with `confidence0` field. Restore operations: `restore --list` printed archive names (plain text); `restore 2026-10-06` returned archive path and pre-restore snapshot, file byte-identical to pre-consolidate state. Re-consolidate gave same no-change report and added new snapshot. Archive cleanup not implemented; no lock files left.

## Problems and status

- Open: 1–7 (no fixes in this run; all problems found and documented).

## Problems

1. `feed candidates --since` does not filter; all 45 candidates have `upload_date: ""`.
2. Parallel `transcript` calls hit 429 (rate limit) immediately.
3. Feed SKILL lacks step to verify upload dates in transcript headers against `--since`.
4. `dream collect` excludes feed skill; 3-minute cards never reach Journal output.
5. `consolidate` dry-run reports "no change" but real run rewrites file with `confidence0`.
6. `memory restore` and `restore --list` print plain text, not JSON (inconsistent with `consolidate`).
7. Every `consolidate` adds archive snapshot, even when nothing changed.

## Network resilience note

The 9-channel whitelist was seeded in the earlier run (step 1). During feed step 4, the first parallel `transcript` calls hit 429 (rate limit). Running one at a time with `--cookies-from-browser chrome` worked (~12 s per call). No further stalls.

All output files in `~/.astack/journal/` and subdirectories (outside repo).
