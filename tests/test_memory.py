import datetime
import json
import multiprocessing
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import memory, paths  # noqa: E402


def _writer(args):
    home, n, tag = args
    os.environ["ASTACK_HOME"] = home
    for i in range(n):
        memory.add(json.dumps({"type": "feedback", "key": f"k:{tag}:{i}", "insight": "x" * 300, "source": "told"}), host=tag)


class MemoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["ASTACK_HOME"] = self.tmp.name

    def tearDown(self):
        os.environ.pop("ASTACK_HOME", None)
        self.tmp.cleanup()

    def test_add_appends_one_line_with_date_and_host(self):
        rec = memory.add('{"type":"correction","key":"skill:interview","insight":"질문자 발언도 살릴 것","source":"told"}',
                         host="claude", today=datetime.date(2026, 10, 5))
        self.assertEqual(rec["date"], "2026-10-05")
        self.assertEqual(rec["host"], "claude")
        lines = paths.memory_file().read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["insight"], "질문자 발언도 살릴 것")

    def test_rejects_unknown_type_and_missing_fields(self):
        with self.assertRaises(memory.InvalidRecord):
            memory.add('{"type":"gossip","key":"a","insight":"b","source":"told"}')
        with self.assertRaises(memory.InvalidRecord):
            memory.add('{"type":"feedback","key":"a","source":"told"}')
        with self.assertRaises(memory.InvalidRecord):
            memory.add('not json')
        with self.assertRaises(memory.InvalidRecord):
            memory.add('{"type":"taste","key":"a","insight":"b","source":"observed","confidence":3}')
        with self.assertRaises(memory.InvalidRecord):
            memory.add('{"type":["x"],"key":"a","insight":"b","source":"told"}')
        with self.assertRaises(memory.InvalidRecord):
            memory.add('{"type":"feedback","key":"a","insight":"b","source":{"a":1}}')

    def test_search_by_key_prefix_and_insight_text(self):
        memory.add('{"type":"whitelist","key":"feed:youtube:Latent Space","insight":"아침 feed","source":"told"}')
        memory.add('{"type":"correction","key":"skill:spec","insight":"결정 목록을 맨 위로","source":"told"}')
        self.assertEqual([r["key"] for r in memory.search("feed:")], ["feed:youtube:Latent Space"])
        self.assertEqual([r["key"] for r in memory.search("결정 목록")], ["skill:spec"])

    def test_search_skips_broken_lines(self):
        paths.memory_file().parent.mkdir(parents=True, exist_ok=True)
        paths.memory_file().write_text('{"type":"feedback","key":"a","insight":"ok","source":"told"}\n{broken\n', encoding="utf-8")
        self.assertEqual(len(memory.search("a")), 1)

    def test_concurrent_appends_keep_whole_lines(self):
        ctx = multiprocessing.get_context("spawn")
        with ctx.Pool(2) as pool:
            pool.map(_writer, [(self.tmp.name, 200, "a"), (self.tmp.name, 200, "b")])
        lines = paths.memory_file().read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 400)
        for line in lines:
            json.loads(line)  # 잘리거나 섞인 줄이 있으면 여기서 실패


if __name__ == "__main__":
    unittest.main()
