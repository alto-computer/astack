import contextlib
import fcntl
import datetime
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import cli, goal, paths  # noqa: E402

T0 = datetime.datetime(2026, 10, 6, 1, 0, 0)


class Proc:
    def __init__(self, code=0):
        self.returncode = code


def writer(payload, code=0, calls=None):
    """result.json에 payload(str이면 그대로)를 쓰는 가짜 runner. payload None이면 아무것도 안 쓴다."""
    def run(cmd, **kw):
        if calls is not None:
            calls.append((cmd, kw))
        if payload is not None:
            d = next(g for g in goal.list_goals() if g["status"] == "running")
            f = paths.goals_dir() / d["id"] / "result.json"
            f.write_text(payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8")
        return Proc(code)
    return run


OK = {"success": True, "summary": ["a", "b", "c"], "map": "/tmp/map.html"}


class GoalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.dict(os.environ, {"ASTACK_HOME": self.tmp.name})
        p.start()
        self.addCleanup(p.stop)

    def _add(self, q, i=0):
        return goal.add(q, now=T0 + datetime.timedelta(seconds=i))

    def test_add_and_list(self):
        g = self._add("RAG는 어떻게 동작해?")
        self.assertTrue(g["id"].startswith("20261006-010000-"))
        self.assertEqual(g["status"], "queued")
        self.assertEqual(g["attempts"], 0)
        self._add("두번째", 1)
        self.assertEqual([x["question"] for x in goal.list_goals()], ["RAG는 어떻게 동작해?", "두번째"])
        self.assertTrue((paths.goals_dir() / g["id"] / "goal.json").is_file())

    def test_run_marks_done_from_result(self):
        self._add("q")
        out = goal.run(runner=writer(OK), now=T0)
        self.assertEqual(out[0]["status"], "done")
        self.assertEqual(out[0]["attempts"], 1)
        saved = goal.list_goals()[0]
        self.assertEqual(saved["status"], "done")
        self.assertTrue(saved["finished"])
        self.assertEqual(goal.report(datetime.date.today())[0]["summary"], ["a", "b", "c"])

    def test_missing_result_is_failure(self):
        self._add("q")
        self.assertEqual(goal.run(runner=writer(None), now=T0)[0]["reason"], "result.json 없음")

    def test_broken_result_is_failure(self):
        self._add("q")
        g = goal.run(runner=writer("{nope"), now=T0)[0]
        self.assertEqual((g["status"], g["reason"]), ("failed", "result.json 깨짐"))

    def test_success_false_and_exit_code(self):
        self._add("q")
        g = goal.run(runner=writer({"success": False, "summary": []}), now=T0)[0]
        self.assertEqual(g["reason"], "success=false")
        self._add("q2", 5)
        g = goal.run(runner=writer(None, code=3), now=T0)[0]
        self.assertEqual(g["reason"], "종료 코드 3")

    def test_max_three_per_night(self):
        for i in range(5):
            self._add(f"q{i}", i)
        self.assertEqual(len(goal.run(runner=writer(OK), now=T0)), 3)
        self.assertEqual([g["status"] for g in goal.list_goals()], ["done"] * 3 + ["queued"] * 2)

    def test_dead_running_goal_resumes(self):
        a = self._add("old")
        b = self._add("new", 1)
        gf = paths.goals_dir() / a["id"] / "goal.json"
        d = json.loads(gf.read_text())
        d.update(status="running", pid=999999, attempts=1)
        gf.write_text(json.dumps(d))
        order = []
        goal.run(max_goals=1, runner=lambda c, **k: (order.append(c), writer(OK)(c, **k))[1], now=T0)
        self.assertEqual(len(order), 1)
        self.assertIn("old", order[0][2])
        got = {g["id"]: g for g in goal.list_goals()}
        self.assertEqual(got[a["id"]]["attempts"], 2)
        self.assertEqual(got[a["id"]]["status"], "done")
        self.assertEqual(got[b["id"]]["status"], "queued")

    def test_resume_and_queued_share_cap(self):
        a = self._add("old")
        for i in range(3):
            self._add(f"q{i}", i + 1)
        gf = paths.goals_dir() / a["id"] / "goal.json"
        d = json.loads(gf.read_text())
        d.update(status="running", pid=999999, attempts=1)
        gf.write_text(json.dumps(d))
        order = []
        goal.run(runner=lambda c, **k: (order.append(c[2]), writer(OK)(c, **k))[1], now=T0)
        self.assertEqual(len(order), 3)
        self.assertIn("old", order[0])
        self.assertEqual([g["status"] for g in goal.list_goals()], ["done"] * 3 + ["queued"])

    def test_empty_queue_runs_nothing(self):
        self.assertEqual(goal.run(runner=writer(OK), now=T0), [])

    def test_locked_run_does_nothing(self):
        self._add("q")
        with open(paths.goals_dir() / ".run.lock", "a") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            calls = []
            self.assertEqual(goal.run(runner=writer(OK, calls=calls), now=T0), [])
        self.assertEqual(calls, [])
        self.assertEqual(goal.list_goals()[0]["status"], "queued")

    def test_exception_isolated_per_goal(self):
        self._add("q1")
        self._add("q2", 1)
        n = []

        def run(cmd, **kw):
            n.append(1)
            if len(n) == 1:
                raise ValueError("boom")
            return writer(OK)(cmd, **kw)
        out = goal.run(runner=run, now=T0)
        self.assertEqual([g["status"] for g in out], ["failed", "done"])
        self.assertEqual(out[0]["reason"], "오류: ValueError: boom")

    def test_hand_edited_goal_missing_keys(self):
        d = paths.goals_dir() / "x"
        d.mkdir(parents=True)
        (d / "goal.json").write_text(json.dumps({"id": "x", "status": "queued"}))
        self.assertEqual(len(goal.list_goals()), 1)
        self.assertEqual(goal.run(runner=writer(OK), now=T0)[0]["status"], "done")

    def test_non_list_summary_wrapped(self):
        self._add("q")
        goal.run(runner=writer({"success": True, "summary": "한 줄"}), now=T0)
        self.assertEqual(goal.report(datetime.date.today())[0]["summary"], ["한 줄"])

    def test_finished_is_real_end_time(self):
        self._add("q")
        goal.run(runner=writer(OK), now=datetime.datetime(2000, 1, 1))
        g = goal.list_goals()[0]
        self.assertEqual(g["started"][:4], "2000")
        self.assertEqual(g["finished"][:10], datetime.date.today().isoformat())

    def test_live_running_goal_counts_against_cap(self):
        a = self._add("live")
        for i in range(3):
            self._add(f"q{i}", i + 1)
        gf = paths.goals_dir() / a["id"] / "goal.json"
        d = json.loads(gf.read_text())
        d.update(status="running", pid=os.getpid(), attempts=1)
        gf.write_text(json.dumps(d))
        self.assertEqual(len(goal.run(runner=writer(OK), now=T0)), 2)
        got = goal.list_goals()
        self.assertEqual(got[0]["status"], "running")
        self.assertEqual(got[0]["attempts"], 1)
        self.assertEqual(got[3]["status"], "queued")

    def test_prompt_mentions_progress_and_result(self):
        self._add("왜 하늘은 파랗지")
        calls = []
        goal.run(runner=writer(OK, calls=calls), now=T0)
        cmd = calls[0][0]
        d = str(paths.goals_dir() / goal.list_goals()[0]["id"])
        self.assertEqual(cmd, ["claude", "-p", cmd[2], "--permission-mode", "acceptEdits", "--add-dir", d,
                               "--allowedTools", "Bash(astack:*)", "WebFetch", "WebSearch"])
        for s in ("progress.md", "result.json", "왜 하늘은 파랗지", "astack:quest"):
            self.assertIn(s, cmd[2])

    def test_codex_host(self):
        self._add("q")
        calls = []
        goal.run(host="codex", runner=writer(OK, calls=calls), now=T0)
        cmd = calls[0][0]
        d = str(paths.goals_dir() / goal.list_goals()[0]["id"])
        self.assertEqual(cmd, ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "--add-dir", d,
                               cmd[-1]])
        self.assertIn("result.json", cmd[-1])

    def test_timeout_is_failure(self):
        self._add("q")

        def boom(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd, 1)
        g = goal.run(runner=boom, now=T0)[0]
        self.assertEqual((g["status"], g["reason"]), ("failed", "시간 초과"))

    def test_report_text_is_empty_when_nothing(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(cli.main(["goal", "report", "--text", "--date", "2026-10-06"]), 0)
        self.assertEqual(buf.getvalue(), "")

    def test_report_text_lists_goals(self):
        self._add("성공한 질문")
        goal.run(runner=writer(OK), now=T0)
        self._add("실패한 질문", 9)
        goal.run(runner=writer(None), now=T0)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(cli.main(["goal", "report", "--text", "--date", "today"]), 0)
        out = buf.getvalue()
        self.assertIn("✓ 성공한 질문", out)
        self.assertIn("/tmp/map.html", out)
        self.assertIn("✗ 실패한 질문", out)
        self.assertIn("result.json 없음", out)

    def test_report_bad_date(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["goal", "report", "--date", "nope"]), 2)


if __name__ == "__main__":
    unittest.main()
