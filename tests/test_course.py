import contextlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from astack_cli import cli, course  # noqa: E402

GOOD = (ROOT / "tests/fixtures/good.html").read_text(encoding="utf-8")
QUIZ = '<details class="quiz" data-kind="short"><summary>점검</summary><p class="q">왜?</p><p class="ans">그래서.</p></details>'


def page(body: str) -> str:
    return GOOD.replace("</body>", body + "</body>")


class CourseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / "00-지도.html").write_text(page('<a href="01-a.html">1</a><a href="02-b.html">2</a>'), encoding="utf-8")
        (self.d / "01-a.html").write_text(page(QUIZ + '<a href="00-지도.html">지도</a><a href="02-b.html">다음</a>'), encoding="utf-8")
        (self.d / "02-b.html").write_text(page(QUIZ + '<a href="00-지도.html">지도</a><a href="01-a.html">이전</a>'), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def codes(self):
        return [i.code for _, i in course.check_course(self.d) if i.level == "error"]

    def test_good_course_has_no_errors(self):
        self.assertEqual(self.codes(), [])

    def test_missing_map_is_error(self):
        (self.d / "00-지도.html").unlink()
        self.assertIn("map", self.codes())

    def test_unlinked_chapter_is_error(self):
        (self.d / "03-c.html").write_text(page(QUIZ + '<a href="00-지도.html">지도</a>'), encoding="utf-8")
        self.assertIn("unlinked", self.codes())

    def test_chapter_without_quiz_is_error(self):
        (self.d / "02-b.html").write_text(page('<a href="00-지도.html">지도</a>'), encoding="utf-8")
        self.assertIn("quiz", self.codes())

    def test_broken_nav_link_is_error(self):
        (self.d / "02-b.html").write_text(page(QUIZ + '<a href="00-지도.html">지도</a><a href="03-gone.html">다음</a>'), encoding="utf-8")
        self.assertIn("nav", self.codes())

    def test_chapter_without_map_link_is_error(self):
        (self.d / "01-a.html").write_text(page(QUIZ + '<a href="02-b.html">다음</a>'), encoding="utf-8")
        self.assertIn("nav", self.codes())

    def test_page_contract_errors_are_included(self):
        bad = re.sub(r'<meta name="description"[^>]*>', "", page(QUIZ + '<a href="00-지도.html">지도</a>'))
        (self.d / "02-b.html").write_text(bad, encoding="utf-8")
        self.assertIn("meta", self.codes())

    def test_cli_exit_codes(self):
        self.assertEqual(cli.main(["course", "check", str(self.d)]), 0)
        (self.d / "00-지도.html").unlink()
        self.assertEqual(cli.main(["course", "check", str(self.d)]), 1)


    def test_link_to_existing_extra_page_is_fine_and_checked(self):
        (self.d / "01-a.html").write_text(page(QUIZ + '<a href="00-지도.html">지도</a><a href="02-b.html">다음</a><a href="extra.html">더</a>'), encoding="utf-8")
        (self.d / "extra.html").write_text(page('<a href="01-a.html">돌아가기</a>'), encoding="utf-8")
        self.assertEqual(self.codes(), [])
        bad = re.sub(r'<meta name="description"[^>]*>', "", page(""))
        (self.d / "extra.html").write_text(bad, encoding="utf-8")
        self.assertIn(("extra.html", "meta"), [(n, i.code) for n, i in course.check_course(self.d) if i.level == "error"])

    def test_link_to_missing_file_says_file(self):
        (self.d / "02-b.html").write_text(page(QUIZ + '<a href="00-지도.html">지도</a><a href="gone.html">더</a>'), encoding="utf-8")
        msgs = [i.message for _, i in course.check_course(self.d) if i.code == "nav"]
        self.assertEqual(msgs, ["없는 파일로 링크: gone.html"])

    def test_non_utf8_page_is_io_error(self):
        (self.d / "02-b.html").write_bytes("<p>깨짐</p>".encode("euc-kr"))
        self.assertIn("io", self.codes())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["course", "check", str(self.d)]), 1)

    def test_cli_prints_summary_line(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["course", "check", str(self.d)]), 0)
        self.assertEqual(out.getvalue().strip().splitlines()[-1], "course: 지도 1 · 장 2 · 에러 0 · 경고 0")

    def test_missing_folder_is_rc2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(cli.main(["course", "check", str(self.d / "nope")]), 2)
        self.assertIn("폴더가 없습니다", err.getvalue())

    def test_course_check_help_describes_check(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
            cli.main(["course", "check", "-h"])
        self.assertIn("astack course check", out.getvalue())
        self.assertIn("지도·장·퀴즈·링크 검사", out.getvalue())

    def test_check_prints_summary_to_stderr(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(cli.main(["check", str(self.d / "01-a.html")]), 0)
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue().strip(), "check: 파일 1 · 에러 0 · 경고 0")

if __name__ == "__main__":
    unittest.main()
