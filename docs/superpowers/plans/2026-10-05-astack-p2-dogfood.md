# P2 dogfood

| 원자 | 소스 | 걸린 시간 | check | 사용자 판정 | 고칠 것 |
|---|---|---|---|---|---|
| interview | Lenny's Podcast, Adam Mosseri (youtube.com/watch?v=yQ_EWmtfWvQ, 68:29) | 약 14분 | 에러 0, 경고 9 (모두 long) | 대기 | 고침: C2·I1·I2(자막), I7(long 오탐), I9(빈 그림 칸), I10(머신 이름), M1·M2. 남음: M8(계약과 템플릿 불일치), M9(썸네일 캡션 겹침), M10, M19 |
| seminar | Geoffrey Litt, "Understanding is the new bottleneck" (youtube.com/watch?v=WkBPX-oDMnA) | 약 15분 | 에러 0, 경고 18 (모두 long) | 대기 | 고침: C1(data-img 이중 내장), C2(en 재번역 자막), I1, I2, I3(slides 재실행), I4(빠진 슬라이드 경고, --crop), I5(slides 폴더 경로), I7. 남음: M3, M6(720p 프레임), M8 |
| paper | ReAct, arXiv 2210.03629 (PDF v3, 33쪽) | 약 14.5분 | 에러 0, 경고 8 | 대기 | 고침: I6(`[…]` 자리표시), I7, I11(그림 폴더, ar5iv 참조 번호, crop 좌표), I12(그림 크기), M1, M2. 남음: I15(좁은 화면 그림), I16(무손실 게이트 수동), M5(PNG 크기), M12(inline 덮어쓰기), M14(부록 긴 프롬프트) |
| repo | openai/codex @ 823ea83 | 약 11.5분 | 에러 0, 경고 0 | 대기 | 고침: I7, I13(얕은 클론의 why 검색), I14(data-lang ts 고정), M2. 남음: I15, M11(장면·그림 짝, 읽는 시간) |

항목 ID는 `.superpowers/sdd/2026-10-05-astack-p2-atoms/final-review.md`, 고친 커밋은 같은 폴더 `fix-wave-report.md`(0389c13, abf7cbd, 0f65fa4, 7a08128).
I15의 일부(quest 장 템플릿의 `.inl.vis-inl` 칸, `dup-id` 경고)는 P3 fix wave에서 들어갔다. paper·repo 템플릿에는 아직 칸이 없다.

paper·repo 템플릿 확정 여부: (사용자 결정)
