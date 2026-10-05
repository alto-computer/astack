import argparse
import datetime
import json
import sys
from pathlib import Path

from . import check as _check
from . import course as _course
from . import done as _done
from . import dream as _dream
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
            for rec in memory.search(args.value or ""):
                print(json.dumps(rec, ensure_ascii=False))
        elif args.action == "prune":
            print(f"지운 기록 {memory.prune(key=args.key, type_=args.type, before=args.before)}개")
        elif args.action == "restore":
            print(memory.restore(args.value or ""))
        elif args.action == "consolidate":
            return _consolidate(args)
    except (memory.InvalidRecord, ValueError, FileNotFoundError, memory.MemoryLocked) as e:
        print(f"astack memory: {e}", file=sys.stderr)
        return 2
    return 0


def _consolidate(args) -> int:
    print(json.dumps(memory.consolidate(dry_run=args.dry_run), ensure_ascii=False))
    return 0


def _cmd_check(args) -> int:
    worst = 0
    for f in args.files:
        try:
            issues = _check.check_file(f)
        except (OSError, UnicodeDecodeError) as e:
            print(f"{f}: error io: {e}")
            worst = 2
            continue
        for i in issues:
            print(f"{f}: {i.level} {i.code}: {i.message}")
            if i.level == "error":
                worst = max(worst, 1)
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
        t = _media.transcript(args.url, lang=args.lang)
    except _media.MediaError as e:
        print(f"astack transcript: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({**t, "lines": [[s, l] for s, l in t["lines"]]}, ensure_ascii=False))
        return 0
    print(f"# {t['title']}\n# {t['channel']} · {t['upload_date']} · {t['duration']}s\n# {t['url']}\n# thumbnail {t['thumbnail']}")
    for s, line in t["lines"]:
        print(f"[{_media.fmt_ts(s)}] {line}")
    return 0


def _cmd_slides(args) -> int:
    try:
        pairs = _media.slides(args.src, Path(args.outdir), threshold=args.threshold)
    except _media.MediaError as e:
        print(f"astack slides: {e}", file=sys.stderr)
        return 2
    for f, t in pairs:
        print(f"{f}\t{_media.fmt_ts(t)}")
    return 0


def _cmd_pdf(args) -> int:
    try:
        if args.action == "pages":
            for p in _pdf.pages(Path(args.a), Path(args.b), max_dim=args.max):
                print(p)
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
    worst = 0
    for name, i in _course.check_course(Path(args.folder)):
        print(f"{name}: {i.level} {i.code}: {i.message}")
        if i.level == "error":
            worst = 1
    return worst


def _cmd_dream(args) -> int:
    try:
        day = datetime.date.fromisoformat(args.date) if args.date else datetime.date.today()
    except ValueError:
        print(f"astack dream: 날짜는 YYYY-MM-DD: {args.date}", file=sys.stderr)
        return 2
    print(json.dumps(_dream.collect(day), ensure_ascii=False))
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
    t.set_defaults(fn=_cmd_transcript)
    s = sub.add_parser("slides", help="발표 영상에서 슬라이드가 바뀌는 프레임 뽑기 (ffmpeg)")
    s.add_argument("src")
    s.add_argument("outdir")
    s.add_argument("--threshold", type=float, default=0.08)
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
    co.add_argument("action", choices=["check"])
    co.add_argument("folder")
    co.set_defaults(fn=_cmd_course)
    dr = sub.add_parser("dream", help="dream 재료 모으기")
    dr.add_argument("action", choices=["collect"])
    dr.add_argument("--date")
    dr.set_defaults(fn=_cmd_dream)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)
