import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from astack_cli import check  # noqa: E402

GOOD = (Path(__file__).parent / "fixtures/good.html").read_text(encoding="utf-8")


def codes(html, level="error"):
    return [i.code for i in check.check_html(html) if i.level == level]


class CheckTest(unittest.TestCase):
    def test_good_fixture_has_no_errors(self):
        self.assertEqual(codes(GOOD), [])

    def test_missing_meta_fails(self):
        html = GOOD.replace('<meta name="rooms:machine" content="MacBook-Pro">', "")
        self.assertIn("meta", codes(html))

    def test_placeholder_metas_fail(self):
        for name, val in (("description", "[한 줄]"), ("rooms:created", "[RFC3339 지금 시각]"), ("rooms:machine", "[머신 이름]")):
            html = re.sub(rf'(<meta name="{name}" content=")[^"]*', rf"\g<1>{val}", GOOD)
            self.assertNotEqual(html, GOOD, name)
            self.assertIn("meta", codes(html), name)

    def test_bracketed_words_in_description_are_not_placeholders(self):
        html = re.sub(r'(<meta name="description" content=")[^"]*', r"\g<1>[번역] 문서 [초안]", GOOD)
        self.assertNotIn("meta", codes(html))

    def test_created_must_be_rfc3339(self):
        html = GOOD.replace("2026-10-05T14:12:09+09:00", "yesterday")
        msgs = [i.message for i in check.check_html(html) if i.code == "meta"]
        self.assertTrue(any("RFC3339" in m for m in msgs), msgs)

    def test_meta_after_64kb_fails(self):
        big = "<style>" + ("a{}" * 30000) + "</style>"
        html = GOOD.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + big)
        msgs = [i.message for i in check.check_html(html) if i.code == "meta"]
        self.assertTrue(any("64KB" in m for m in msgs), msgs)

    def test_stray_title_in_body_fails(self):
        html = GOOD.replace("&lt;title&gt;이라는", "<title>이라는")
        self.assertIn("title", codes(html))

    def test_external_files_fail_but_links_pass(self):
        for bad in ['<script src="x.js"></script>', '<img src="images/a.png">',
                    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jost">',
                    '<div style="background:url(a.png)"></div>']:
            html = GOOD.replace("</body>", bad + "</body>")
            self.assertIn("external", codes(html), bad)
        ok = GOOD.replace("</body>", '<img src="data:image/png;base64,AAA="><svg><path marker-end="url(#ar)"/></svg></body>')
        self.assertEqual(codes(ok), [])

    def test_layers_and_source_required(self):
        self.assertIn("layer", codes(GOOD.replace('data-astack="3m"', "")))
        self.assertIn("source", codes(GOOD.replace('data-astack="source"', "")))

    def test_unreplaced_marker_fails(self):
        self.assertIn("marker", codes(GOOD.replace("</head>", "<!--astack:css--></head>")))

    def test_slop_and_long_sentence_are_warnings(self):
        html = GOOD.replace("<p>바뀐 곳은 두 군데다.</p>",
                            "<p>핵심은 이것이다. " + "아주 " * 30 + "긴 문장이다. 끝.</p>")
        self.assertEqual(codes(html), [])
        self.assertIn("slop", codes(html, "warn"))
        self.assertIn("long", codes(html, "warn"))

    def test_code_and_pre_are_not_prose(self):
        text = check.prose_text("<p>보인다.</p><pre>핵심은 숨김</pre><code>매우 숨김</code>")
        self.assertIn("보인다", text)
        self.assertNotIn("숨김", text)

    def test_meta_outside_64kb_has_64kb_message(self):
        # Meta present but after 64KB should say "밖에 있습니다" with "64KB"
        big = "<style>" + ("a{}" * 30000) + "</style>"
        html = GOOD.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + big)
        msgs = [i.message for i in check.check_html(html) if i.code == "meta"]
        self.assertTrue(any("밖에 있습니다" in m and "64KB" in m for m in msgs), msgs)

    def test_missing_meta_has_no_64kb_message(self):
        # Meta truly absent should say "없습니다" without "64KB" in that part
        html = GOOD.replace('<meta name="description" content="Rooms가 메타를 앞 64KB에서만 읽는 이유">', "")
        msgs = [i.message for i in check.check_html(html) if i.code == "meta"]
        self.assertTrue(any("없습니다" in m for m in msgs), msgs)
        self.assertFalse(any("64KB" in m for m in msgs if "없습니다" in m),
                        "Missing meta message should not mention 64KB")

    def test_many_short_list_items_no_long_warning(self):
        # Many short <li> items should not trigger long-sentence warning
        html = GOOD.replace("<section data-astack=\"3m\"><p>바뀐 곳은 두 군데다.</p>",
                           "<section data-astack=\"3m\"><ul><li>항목1</li><li>항목2</li>" +
                           ("<li>항목</li>" * 20) + "</ul>")
        warns = codes(html, "warn")
        self.assertNotIn("long", warns, f"Should not warn on list items: {warns}")

    def test_genuinely_long_sentence_still_warns(self):
        # One genuinely long sentence should still warn
        html = GOOD.replace("<p>바뀐 곳은 두 군데다.</p>",
                           "<p>" + "단어 " * 30 + "긴 문장.</p>")
        warns = codes(html, "warn")
        self.assertIn("long", warns)

    def test_svg_title_does_not_count(self):
        # <title> inside <svg> should not trigger error
        html = GOOD.replace("</body>", '<svg><title>다이어그램</title></svg></body>')
        self.assertNotIn("title", codes(html), "SVG title should not count")

    def test_raw_title_in_body_still_errors(self):
        # A real <title> tag in body should still error
        html = GOOD.replace("</body>", '<title>이건 에러</title></body>')
        self.assertIn("title", codes(html))

    def test_meta_content_with_double_quote_apostrophe(self):
        # Meta content with apostrophe inside double quotes should be read correctly
        # Old regex content=["']([^"']*)["'] would capture "It" (stops at apostrophe)
        # New regex content=(["'])((?:(?!\1).)*?)\1 captures "It's working"
        value = check._meta('<meta name="description" content="It\'s working">', "description")
        self.assertEqual(value, "It's working")

    def test_meta_content_with_single_quote_doublequote(self):
        # Meta content with double quotes inside single quotes should be read correctly
        # Old regex would capture "say" (stops at double quote)
        # New regex captures the full value
        value = check._meta('<meta name="description" content=\'say "hi" there\'>', "description")
        self.assertEqual(value, 'say "hi" there')

    def test_url_in_code_no_error(self):
        # url() inside <code> should not trigger external error
        html = GOOD.replace("</body>", '<code>background: url(image.png)</code></body>')
        self.assertNotIn("external", codes(html), "url() in code should not error")

    def test_url_in_pre_no_error(self):
        # url() inside <pre> should not trigger external error
        html = GOOD.replace("</body>", '<pre>background: url(image.png)</pre></body>')
        self.assertNotIn("external", codes(html), "url() in pre should not error")

    def test_url_in_style_attribute_still_errors(self):
        # url() in style attribute should still trigger error
        html = GOOD.replace("</body>", '<div style="background: url(image.png)"></div></body>')
        self.assertIn("external", codes(html), "url() in style attribute should error")

    def test_url_in_style_attr_with_single_quote_double_quote(self):
        # Regression test: style='background:url("a.png")' should still trigger error
        # Old regex style=["']([^"']*)["'] would capture "background:url(" (stops at ")
        # New regex \bstyle=(["'])(.*?)\1 captures the full style value
        html = GOOD.replace("</body>", '<div style=\'background:url("a.png")\'/></body>')
        self.assertIn("external", codes(html), "url() in single-quoted style with double-quote should error")

    def test_url_in_style_attr_with_double_quote_single_quote(self):
        # Regression test: style="background:url('b.png')" should still trigger error
        # Old regex would capture "background:url(" (stops at ')
        html = GOOD.replace("</body>", '<div style="background:url(\'b.png\')"/></body>')
        self.assertIn("external", codes(html), "url() in double-quoted style with single-quote should error")

    def test_unfilled_braces_fail(self):
        html = GOOD.replace("</body>", "<p>{{SPEAKER}}의 발표</p></body>")
        self.assertIn("placeholder", codes(html))

    def test_braces_inside_code_are_fine(self):
        html = GOOD.replace("</body>", "<pre><code>{{ value }}</code></pre></body>")
        self.assertNotIn("placeholder", codes(html))

    def test_placeholder_in_attribute_fails(self):
        html = GOOD.replace("</body>", '<section data-cap="{{캡션}}"></section></body>')
        self.assertIn("placeholder", codes(html))

    def test_placeholder_in_table_fails(self):
        html = GOOD.replace("</body>", "<table><tr><td>{{값}}</td></tr></table></body>")
        self.assertIn("placeholder", codes(html))

    def test_placeholder_in_svg_fails(self):
        html = GOOD.replace("</body>", "<svg><text>{{라벨}}</text></svg></body>")
        self.assertIn("placeholder", codes(html))

    def test_code_slot_placeholder_fails_even_inside_code(self):
        html = GOOD.replace("</body>", '<pre data-lang="auto"><code>{{실제 코드}}</code></pre></body>')
        self.assertIn("placeholder", codes(html))

    def test_duplicate_id_warns(self):
        svg = '<svg><defs><marker id="ah"></marker></defs></svg>'
        html = GOOD.replace("</body>", svg + svg + "</body>")
        self.assertIn("dup-id", codes(html, "warn"))
        self.assertNotIn("dup-id", codes(html))
        msgs = [i.message for i in check.check_html(html) if i.code == "dup-id"]
        self.assertEqual(msgs, ["중복 id: ah (그림 사본이면 접두사)"])

    def test_ids_in_code_and_comments_are_not_duplicates(self):
        html = GOOD.replace("</body>", '<p id="x">a</p><pre><code>&lt;p id="x"&gt;</code></pre><code>id="x"</code><!-- id="x" --></body>')
        self.assertNotIn("dup-id", codes(html, "warn"))

    def test_question_and_jyo_endings_split_sentences(self):
        half = "이 " * 20
        html = GOOD.replace("<p>바뀐 곳은 두 군데다.</p>", f"<p>{half}붙죠. 그렇다면 {half}할까요? 그래서 {half}끝.</p>")
        self.assertNotIn("long", codes(html, "warn"))

    def test_abbreviation_does_not_split(self):
        self.assertEqual(check.sentences("A vs. B 비교다. 다음."), ["A vs. B 비교다.", "다음."])

    def test_english_sentence_is_not_counted(self):
        html = GOOD.replace("<p>바뀐 곳은 두 군데다.</p>", "<p>" + "word " * 40 + "end.</p>")
        self.assertNotIn("long", codes(html, "warn"))

    def test_adjacent_links_are_separate(self):
        item = '<a class="index-item" href="#c">' + "챕터 " * 10 + "</a>"
        html = GOOD.replace("<p>바뀐 곳은 두 군데다.</p>", "<nav>" + item * 3 + "</nav>")
        self.assertNotIn("long", codes(html, "warn"))

    def test_source_footer_is_not_counted_for_long_or_slop(self):
        html = GOOD.replace('data-astack="source">', 'data-astack="source">' + "핵심은 " + "요청 " * 30 + "썼다. ")
        self.assertNotEqual(html, GOOD)
        self.assertNotIn("long", codes(html, "warn"))
        self.assertNotIn("slop", codes(html, "warn"))

    def test_source_without_claude_code_line_fails(self):
        html = GOOD.replace("Claude Code가 썼습니다", "썼다")
        msgs = [i.message for i in check.check_html(html) if i.code == "source"]
        self.assertTrue(any("Claude Code가 썼습니다" in m for m in msgs), msgs)

    def test_data_img_file_is_external(self):
        html = GOOD.replace("</body>", '<section data-img="slides/s1.jpg"></section></body>')
        self.assertIn("external", codes(html))


if __name__ == "__main__":
    unittest.main()
