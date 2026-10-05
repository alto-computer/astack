import argparse
import datetime
import json
import sys
from pathlib import Path

from . import check as _check
from . import course as _course
from . import done as _done
from . import dream as _dream
from . import feed as _feed
from . import inline as _inline
from . import media as _media
from . import memory
from . import pdf as _pdf
from . import recall as _recall
from . import route as _route


def _memory(args) -> int:
    try:
        if args.action == "add":
            rec = memory.add(args.value or "")
            print(json.dumps(rec, ensure_ascii=False))
        elif args.action == "search":
            found = memory.search(args.value or "")
            for rec in found:
                print(json.dumps(rec, ensure_ascii=False))
            if not found:
                print("astack memory: 결과 없음", file=sys.stderr)
        elif args.action == "prune":
            print(f"지운 기록 {memory.prune(key=args.key, type_=args.type, before=args.before)}개")
        elif args.action == "restore":
            return _restore(args)
        elif args.action == "consolidate":
            return _consolidate(args)
    except (memory.InvalidRecord, ValueError, FileNotFoundError, memory.MemoryLocked) as e:
        print(f"astack memory: {e}", file=sys.stderr)
        return 2
    return 0


def _restore(args) -> int:
    if args.list:
        for name in memory.archives():
            print(name)
        return 0
    name = args.value or ""
    same_day = memory.archives(name) if memory.ARCHIVE_NAME.fullmatch(name) and "." not in name else []
    if len(same_day) > 1:
        print(f"astack memory: {name} 스냅샷이 {len(same_day)}개입니다. 그날 첫 상태로 되돌립니다. "
              "최근 것은 --list로 이름을 보고 지정하세요", file=sys.stderr)
    print(memory.restore(name))
    return 0


def _consolidate(args) -> int:
    print(json.dumps(memory.consolidate(dry_run=args.dry_run), ensure_ascii=False))
    return 0


def _cmd_check(args) -> int:
    worst = errors = warns = 0
    for f in args.files:
        try:
            issues = _check.check_file(f)
        except (OSError, UnicodeDecodeError) as e:
            print(f"{f}: error io: {e}")
            worst, errors = 2, errors + 1
            continue
        for i in issues:
            print(f"{f}: {i.level} {i.code}: {i.message}")
            if i.level == "error":
                worst, errors = max(worst, 1), errors + 1
            else:
                warns += 1
    print(f"check: 파일 {len(args.files)} · 에러 {errors} · 경고 {warns}", file=sys.stderr)
    return worst


def _cmd_inline(args) -> int:
    for f in args.files:
        _inline.inline_file(f)
        print(f)
    return 0


def _cmd_done(args) -> int:
    code, notes = _done.done(args.file, args.skill, room=args.room, force=args.force)
    for n in notes:
        print(n, file=sys.stderr)
    if code == 0:
        print(Path(args.file).resolve())
    return code


def _cmd_recall(args) -> int:
    project = Path(args.project) if args.project else (_recall.project_root(Path.cwd()) if args.now else None)
    items = _recall.recall(query=args.query or "", project=project, since=args.since, limit=1 if args.now else args.limit)
    for i in items:
        if args.json:
            print(json.dumps({"path": str(i.path), "skill": i.skill, "ts": i.ts, "title": i.title, "description": i.description}, ensure_ascii=False))
        else:
            print(f"{i.path}\t{i.title}\t{i.description}")
    return 0


def _cmd_transcript(args) -> int:
    try:
        t = _media.transcript(args.url, lang=args.lang, cookies=args.cookies_from_browser)
    except _media.MediaError as e:
        print(f"astack transcript: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({**t, "lines": [[s, l] for s, l in t["lines"]]}, ensure_ascii=False))
        return 0
    print(f"# {t['title']}\n# {t['channel']} · {t['upload_date']} · {t['duration']}s\n# {t['url']}\n# thumbnail {t['thumbnail']}\n# lang {t['lang']}")
    for s, line in t["lines"]:
        print(f"[{_media.fmt_ts(s)}] {line}")
    return 0


def _cmd_slides(args) -> int:
    try:
        pairs, gaps = _media.slides(args.src, Path(args.outdir), threshold=args.threshold, crop=args.crop,
                                    cookies=args.cookies_from_browser)
    except _media.MediaError as e:
        print(f"astack slides: {e}", file=sys.stderr)
        return 2
    for f, t in pairs:
        print(f"{f}\t{_media.fmt_ts(t)}")
    for a, b in gaps:
        print(f"astack slides: 슬라이드 없는 구간 {_mmss(a)}–{_mmss(b)} ({round((b - a) / 60)}분). "
              "--threshold를 낮추거나(0.05/0.03) 그 구간을 직접 확인하세요", file=sys.stderr)
    return 0


def _mmss(sec: float) -> str:
    s = int(sec)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60:02d}:{s % 60:02d}"


def _cmd_pdf(args) -> int:
    try:
        if args.action == "pages":
            ps = _pdf.pages(Path(args.a), Path(args.b), max_dim=args.max)
            for p in ps:
                print(p)
            if ps:
                w, h = _pdf._image_size(ps[0])
                print(f"astack pdf: {len(ps)}쪽, 쪽 크기 {w}x{h}px (crop 좌표 기준)", file=sys.stderr)
        else:
            x, y, w, h = (int(v) for v in args.box)
            print(_pdf.crop(Path(args.a), x, y, w, h, Path(args.b)))
    except (_pdf.PdfError, ValueError) as e:
        print(f"astack pdf: {e}", file=sys.stderr)
        return 2
    return 0


def _cmd_route(args) -> int:
    r = _route.route(args.text, Path.cwd())
    print(json.dumps({"skill": r.skill, "reason": r.reason, "needs_judgment": r.needs_judgment}, ensure_ascii=False))
    return 0


def _cmd_course(args) -> int:
    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"astack course: 폴더가 없습니다: {folder}", file=sys.stderr)
        return 2
    issues = _course.check_course(folder)
    for name, i in issues:
        print(f"{name}: {i.level} {i.code}: {i.message}")
    e = sum(i.level == "error" for _, i in issues)
    has_map = int((folder / _course.MAP).is_file())
    print(f"course: 지도 {has_map} · 장 {len(_course.chapters(folder))} · 에러 {e} · 경고 {len(issues) - e}")
    return 1 if e else 0


def _cmd_dream(args) -> int:
    try:
        day = datetime.date.fromisoformat(args.date) if args.date else datetime.date.today()
    except ValueError:
        print(f"astack dream: 날짜는 YYYY-MM-DD: {args.date}", file=sys.stderr)
        return 2
    print(json.dumps(_dream.collect(day), ensure_ascii=False))
    return 0


def _cmd_feed(args) -> int:
    try:
        if args.action == "seed":
            if len(args.rest) != 2:
                raise ValueError('사용법: astack feed seed "<이름>" <채널 URL>')
            print("추가함" if _feed.seed(*args.rest) else "이미 있음")
        else:
            for c in _feed.candidates(since=args.since, per_channel=args.per_channel, cookies=args.cookies_from_browser):
                print(json.dumps(c, ensure_ascii=False))
    except (ValueError, _media.MediaError, memory.InvalidRecord) as e:
        print(f"astack feed: {e}", file=sys.stderr)
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="astack")
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("memory", help="기억 쓰기·찾기·정리")
    m.add_argument("action", choices=["add", "search", "prune", "restore", "consolidate"])
    m.add_argument("value", nargs="?")
    m.add_argument("--key")
    m.add_argument("--type")
    m.add_argument("--before")
    m.add_argument("--dry-run", action="store_true")
    m.add_argument("--list", action="store_true", help="restore: archive 이름, 최신 먼저")
    m.set_defaults(fn=_memory)
    c = sub.add_parser("check", help="이해물 HTML이 출력 계약을 지키는지 검사")
    c.add_argument("files", nargs="+")
    c.set_defaults(fn=_cmd_check)
    i = sub.add_parser("inline", help="키트 CSS/JS, 이미지, 코드 강조를 HTML 안에 넣는다")
    i.add_argument("files", nargs="+")
    i.set_defaults(fn=_cmd_inline)
    d = sub.add_parser("done", help="검사 후 outputs.log에 기록하고 rooms link를 부른다")
    d.add_argument("file")
    d.add_argument("--skill", required=True)
    d.add_argument("--room")
    d.add_argument("--force", action="store_true")
    d.set_defaults(fn=_cmd_done)
    r = sub.add_parser("recall", help="쌓인 이해물에서 찾기")
    r.add_argument("--query")
    r.add_argument("--project")
    r.add_argument("--since")
    r.add_argument("--limit", type=int, default=10)
    r.add_argument("--now", action="store_true")
    r.add_argument("--json", action="store_true")
    r.set_defaults(fn=_cmd_recall)
    t = sub.add_parser("transcript", help="영상 자막과 메타데이터 (yt-dlp)")
    t.add_argument("url")
    t.add_argument("--lang", default="en")
    t.add_argument("--json", action="store_true")
    t.add_argument("--cookies-from-browser", metavar="BROWSER", help="429·403이면 chrome 등 브라우저 쿠키로")
    t.set_defaults(fn=_cmd_transcript)
    s = sub.add_parser("slides", help="발표 영상에서 슬라이드가 바뀌는 프레임 뽑기 (ffmpeg)")
    s.add_argument("src")
    s.add_argument("outdir")
    s.add_argument("--threshold", type=float, default=0.08)
    s.add_argument("--crop", metavar="W:H:X:Y", help="슬라이드 영역만 보고 잘라 낸다 (픽셀)")
    s.add_argument("--cookies-from-browser", metavar="BROWSER", help="429·403이면 chrome 등 브라우저 쿠키로")
    s.set_defaults(fn=_cmd_slides)
    pd = sub.add_parser("pdf", help="PDF 쪽을 PNG로 렌더(pages), 그림 영역 자르기(crop)")
    pd.add_argument("action", choices=["pages", "crop"])
    pd.add_argument("a", help="pages: PDF 경로 / crop: PNG 경로")
    pd.add_argument("box", nargs="*", help="crop: x y w h (픽셀)")
    pd.add_argument("b", help="pages: 출력 폴더 / crop: 출력 PNG")
    pd.add_argument("--max", type=int, default=2200)
    pd.set_defaults(fn=_cmd_pdf)
    ro = sub.add_parser("route", help="입력(링크, 파일, 질문)을 어느 스킬로 보낼지")
    ro.add_argument("text")
    ro.set_defaults(fn=_cmd_route)
    co = sub.add_parser("course", help="quest 코스 폴더 검사")
    cs = co.add_subparsers(dest="action", required=True)
    ck = cs.add_parser("check", help="지도·장·퀴즈·링크 검사", description="지도·장·퀴즈·링크 검사")
    ck.add_argument("folder")
    ck.set_defaults(fn=_cmd_course)
    dr = sub.add_parser("dream", help="dream 재료 모으기")
    dr.add_argument("action", choices=["collect"])
    dr.add_argument("--date")
    dr.set_defaults(fn=_cmd_dream)
    fe = sub.add_parser("feed", help="화이트리스트 채널(seed)과 오늘 후보(candidates)")
    fe.add_argument("action", choices=["seed", "candidates"])
    fe.add_argument("rest", nargs="*")
    fe.add_argument("--since")
    fe.add_argument("--per-channel", type=int, default=5)
    fe.add_argument("--cookies-from-browser", metavar="BROWSER", help="429·403이면 chrome 등 브라우저 쿠키로")
    fe.set_defaults(fn=_cmd_feed)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)
