import argparse
import json
import sys

from . import check as _check
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
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)
