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
from . import gate as _gate
from . import goal as _goal
from . import inline as _inline
from . import media as _media
from . import memory
from . import pdf as _pdf
from . import recall as _recall
from . import route as _route
from . import setup as _setup


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
    rep = memory.consolidate(dry_run=args.dry_run)
    if not args.html:
        print(json.dumps(rep, ensure_ascii=False))
        return 0
    if args.quiet_if_unchanged and not memory.changed(rep):
        return 0
    out = Path(args.html)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(memory.render_report(rep, datetime.date.today(), dry_run=args.dry_run), encoding="utf-8")
    _inline.inline_file(out)
    print(out)
    return 0


def _cmd_gate(args) -> int:
    nums = []
    cur = args.numbers or args.out
    try:
        if args.numbers:
            nums = [l.strip() for l in Path(args.numbers).read_text(encoding="utf-8").splitlines() if l.strip()]
        cur = args.out
        out_text = Path(args.out).read_text(encoding="utf-8")
        cur = args.source
        src_text = _gate.source_text(args.source)
    except (OSError, UnicodeDecodeError) as e:
        print(f"astack gate: {cur}: {e}", file=sys.stderr)
        return 2
    miss = _gate.paper(out_text, src_text, nums)
    for m in miss:
        print(f"빠짐: {m}")
    if not miss:
        print("gate: 통과")
    return 1 if miss else 0


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


def _expand(items) -> list:
    """폴더면 그 안의 *.html(정렬), 아니면 그대로."""
    out: list = []
    for it in items:
        p = Path(it)
        out.extend(sorted(p.glob("*.html")) if p.is_dir() else [it])
    return out


def _cmd_inline(args) -> int:
    for f in _expand(args.files):
        _inline.inline_file(f)
        print(f)
    return 0


def _cmd_done(args) -> int:
    worst = 0
    for it in args.files:
        if Path(it).is_dir() and not any(Path(it).glob("*.html")):
            print(f"astack done: {it}: html 없음", file=sys.stderr)
            worst = 1
    for f in _expand(args.files):
        code, notes = _done.done(f, args.skill, room=args.room, force=args.force)
        for n in notes:
            named = str(f) in n or str(Path(f).resolve()) in n
            print(f"{f}: {n}" if code and not named else n, file=sys.stderr)
        if code == 0:
            print(Path(f).resolve())
        worst = max(worst, code)
    return worst


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
            if args.since and not memory._iso_date(args.since):
                raise ValueError(f"--since는 YYYY-MM-DD 날짜: {args.since}")
            for c in _feed.candidates(since=args.since, per_channel=args.per_channel, cookies=args.cookies_from_browser):
                print(json.dumps(c, ensure_ascii=False))
    except (ValueError, _media.MediaError, memory.InvalidRecord) as e:
        print(f"astack feed: {e}", file=sys.stderr)
        return 2
    return 0


def _goal_day(text: str) -> datetime.date:
    today = datetime.date.today()
    if text == "today":
        return today
    if text == "yesterday":
        return today - datetime.timedelta(days=1)
    return datetime.date.fromisoformat(text)


def _goal_add(args) -> int:
    print(json.dumps(_goal.add(args.question), ensure_ascii=False))
    return 0


def _goal_list(args) -> int:
    for g in _goal.list_goals():
        print(json.dumps(g, ensure_ascii=False) if args.json else f"{g['id']}\t{g['status']}\t{g['question']}")
    return 0


def _goal_run(args) -> int:
    try:
        until = None if args.until == "none" else datetime.datetime.strptime(args.until, "%H:%M").time()
    except ValueError:
        print(f"astack goal: --until은 HH:MM 또는 none: {args.until}", file=sys.stderr)
        return 2
    for g in _goal.run(max_goals=args.max, host=args.host, until=until):
        print(f"{g['id']}\t{g['status']}\t{g['reason'] or ''}")
    return 0


def _goal_report(args) -> int:
    try:
        day = _goal_day(args.date)
    except ValueError:
        print(f"astack goal: 날짜는 YYYY-MM-DD, yesterday, today: {args.date}", file=sys.stderr)
        return 2
    items = _goal.report(None if args.new else day, new=args.new)
    if not items:
        return 0
    print(_goal.report_text(items) if args.text else json.dumps(items, ensure_ascii=False))
    if args.new:
        sys.stdout.flush()
        _goal.mark_reported(items)
    return 0


def _cmd_setup(args) -> int:
    return _setup.main(args.rest)


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
    m.add_argument("--html", help="consolidate: 변화 보고서를 이 경로에 쓴다")
    m.add_argument("--quiet-if-unchanged", action="store_true", help="consolidate --html: 변화가 없으면 아무것도 쓰지 않는다")
    m.add_argument("--list", action="store_true", help="restore: archive 이름, 최신 먼저")
    m.set_defaults(fn=_memory)
    c = sub.add_parser("check", help="이해물 HTML이 출력 계약을 지키는지 검사")
    c.add_argument("files", nargs="+")
    c.set_defaults(fn=_cmd_check)
    i = sub.add_parser("inline", help="키트 CSS/JS, 이미지, 코드 강조를 HTML 안에 넣는다")
    i.add_argument("files", nargs="+", metavar="file_or_dir")
    i.set_defaults(fn=_cmd_inline)
    d = sub.add_parser("done", help="검사 후 outputs.log에 기록하고 rooms link를 부른다")
    d.add_argument("files", nargs="+", metavar="file_or_dir")
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
    go = sub.add_parser("goal", help="밤 goal 큐: add, list, run(하룻밤 3개까지, 이어서), report")
    gs = go.add_subparsers(dest="action", required=True)
    ga = gs.add_parser("add", help="질문을 큐에 넣는다")
    ga.add_argument("question")
    ga.set_defaults(fn=_goal_add)
    gl = gs.add_parser("list", help="큐 보기")
    gl.add_argument("--json", action="store_true")
    gl.set_defaults(fn=_goal_list)
    gr = gs.add_parser("run", help="이어서 할 것과 큐의 것을 실행")
    gr.add_argument("--max", type=int, default=3)
    gr.add_argument("--host", choices=["claude", "codex"], default="claude")
    gr.add_argument("--until", default="06:30", help="이 시각 뒤로는 새 goal을 시작하지 않음(HH:MM, none)")
    gr.set_defaults(fn=_goal_run)
    gp = gs.add_parser("report", help="그날 끝난 goal 보고")
    gp.add_argument("--date", default="today", help="YYYY-MM-DD, yesterday, today")
    gp.add_argument("--text", action="store_true", help="Telegram용 짧은 글")
    gp.add_argument("--new", action="store_true", help="아직 보고하지 않은 끝난 goal 전부, 출력 후 보고됨 표시(--date 무시)")
    gp.set_defaults(fn=_goal_report)
    ga = sub.add_parser("gate", help="무손실 검사")
    gas = ga.add_subparsers(dest="gate_cmd", required=True)
    gp2 = gas.add_parser("paper", help="논문 리더가 원문의 figure·table·수치를 다 담았는지")
    gp2.add_argument("out")
    gp2.add_argument("--source", required=True)
    gp2.add_argument("--numbers", help="한 줄에 수치 하나인 파일")
    gp2.set_defaults(fn=_cmd_gate)
    se = sub.add_parser("setup", help="호스트별 설치 (./setup과 같다)")
    se.add_argument("rest", nargs=argparse.REMAINDER)
    se.set_defaults(fn=_cmd_setup)
    return p


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["setup"]:  # REMAINDER는 맨 앞 --옵션을 못 받아서 직접 넘긴다
        return _setup.main(argv[1:])
    args = build_parser().parse_args(argv)
    return args.fn(args)
