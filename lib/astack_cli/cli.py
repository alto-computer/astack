import argparse
import json
import sys

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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="astack")
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("memory", help="기억 쓰기·찾기")
    m.add_argument("action", choices=["add", "search"])
    m.add_argument("value")
    m.set_defaults(fn=_memory)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)
