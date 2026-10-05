import argparse
import json
import sys
from pathlib import Path

from . import check as _check
from . import done as _done
from . import inline as _inline
from . import memory


def _memory(args) -> int:
    if args.action == "add":
        try:
            rec = memory.add(args.value)
        except memory.InvalidRecord as e:
            print(f"astack memory: {e}", file=sys.stderr)
            return 2
        print(json.dumps(rec, ensure_ascii=False))
        return 0
    for rec in memory.search(args.value):
        print(json.dumps(rec, ensure_ascii=False))
    return 0


def _cmd_check(args) -> int:
    worst = 0
    for f in args.files:
        for i in _check.check_file(f):
            print(f"{f}: {i.level} {i.code}: {i.message}")
            if i.level == "error":
                worst = 1
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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="astack")
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("memory", help="기억 쓰기·찾기")
    m.add_argument("action", choices=["add", "search"])
    m.add_argument("value")
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
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)
