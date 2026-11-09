"""Tests for the chinese-text-fixer skill script."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.dont_write_bytecode = True

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "chinese-text-fixer"
    / "scripts"
    / "fix_text.py"
)
SPEC = importlib.util.spec_from_file_location("chinese_text_fixer", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def analyze(
    text: str, profile: str = "standard", markdown: bool = False, fix_entities: bool = False
):
    return MODULE.analyze(
        text,
        profile,
        markdown=markdown,
        fix_entities=fix_entities,
        html_like=False,
    )


class QuoteRulesTest(unittest.TestCase):
    def test_reversed_closing_quote_is_fixed(self):
        findings, fixed = analyze("“数据怎么流转/谁响应手势“")
        self.assertEqual(fixed, "“数据怎么流转/谁响应手势”")
        self.assertEqual([finding.rule for finding in findings], ["QT001"])
        self.assertEqual(findings[0].severity, "fix")

    def test_valid_pairs_are_unchanged(self):
        text = "他说：“你好，世界。”然后离开。"
        findings, fixed = analyze(text)
        self.assertEqual(fixed, text)
        self.assertEqual(findings, [])

    def test_unclosed_quote_is_reported_not_completed(self):
        text = "他说“你好，然后走了。"
        findings, fixed = analyze(text)
        self.assertEqual(fixed, text)
        self.assertIn("QT002", {finding.rule for finding in findings})
        self.assertTrue(all(finding.severity == "review" for finding in findings))

    def test_inch_marks_are_not_treated_as_quotes(self):
        text = "价格 6” 和 6“ 屏幕，中文“提示”。"
        findings, fixed = analyze(text)
        self.assertEqual(fixed, text)
        self.assertEqual(findings, [])

    def test_unclosed_quote_does_not_flip_later_opener(self):
        text = "他问“为什么？\n\n她回答：“好的。”"
        findings, fixed = analyze(text)
        self.assertEqual(fixed, text)
        self.assertIn("QT002", {finding.rule for finding in findings})
        self.assertTrue(all(finding.severity == "review" for finding in findings))

    def test_closing_quote_after_digit_pairs_with_open_quote(self):
        text = "他说“6”"
        findings, fixed = analyze(text)
        self.assertEqual(fixed, text)
        self.assertEqual(findings, [])


class PunctuationRulesTest(unittest.TestCase):
    def test_halfwidth_punctuation_becomes_fullwidth_only_after_cjk(self):
        findings, fixed = analyze("第一,第二. 完成")
        self.assertEqual(fixed, "第一，第二。 完成")
        self.assertTrue(findings)

    def test_numbers_and_filenames_are_left_alone(self):
        text = "版本 1.0 发布于 2024.10.01，文件是 notes.md。"
        findings, fixed = analyze(text)
        self.assertEqual(fixed, text)
        self.assertEqual(findings, [])

    def test_repeated_punctuation_collapses(self):
        findings, fixed = analyze("中文，，重复。。标点！！")
        self.assertEqual(fixed, "中文，重复。标点！")

    def test_space_before_chinese_punctuation_is_removed(self):
        findings, fixed = analyze("中文 ， 后面（ 括号）")
        self.assertEqual(fixed, "中文， 后面（括号）")


class InvisibleAndEntityTest(unittest.TestCase):
    def test_zero_width_space_and_bom_are_removed(self):
        findings, fixed = analyze("中\u200b文\ufeff文本")
        self.assertEqual(fixed, "中文文本")
        self.assertEqual({finding.rule for finding in findings}, {"ZW001"})

    def test_zwj_is_reported_but_preserved(self):
        text = "👩\u200d💻"
        findings, fixed = analyze(text)
        self.assertEqual(fixed, text)
        self.assertEqual(findings[0].rule, "ZW002")

    def test_entities_are_reported_by_default(self):
        text = "中文 &quot;引号&quot;"
        findings, fixed = analyze(text)
        self.assertEqual(fixed, text)
        self.assertIn("EN001", {finding.rule for finding in findings})

    def test_strict_profile_decodes_visible_entities(self):
        findings, fixed = analyze("中文&mdash;文本", profile="strict")
        self.assertEqual(fixed, "中文—文本")
        self.assertEqual([finding.severity for finding in findings], ["fix"])

    def test_entities_decoding_to_invisible_chars_stay_literal(self):
        for text in ("中文&nbsp;文本", "中文&#8203;文本"):
            findings, fixed = analyze(text, profile="strict")
            self.assertEqual(fixed, text)
            self.assertEqual([finding.severity for finding in findings], ["review"])

    def test_mojibake_is_never_rewritten(self):
        text = "中文 锟斤拷 乱码"
        findings, fixed = analyze(text)
        self.assertEqual(fixed, text)
        self.assertEqual([finding.rule for finding in findings], ["MO001"])


class MarkdownProtectionTest(unittest.TestCase):
    def test_frontmatter_fences_and_inline_code_are_protected(self):
        text = (
            "---\n"
            'description: "使用 “错误“ 引号"\n'
            "---\n\n"
            "正文：“正确“ 和 `代码““`。\n\n"
            "```\n"
            "“代码块“\n"
            "```\n"
        )
        findings, fixed = analyze(text, markdown=True)
        self.assertIn("正文：“正确” 和 `代码““`。", fixed)
        self.assertIn('description: "使用 “错误“ 引号"', fixed)
        self.assertIn("“代码块“", fixed)


class CommandLineTest(unittest.TestCase):
    def test_apply_writes_fix_and_preserves_crlf(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.md"
            path.write_bytes("开头 “错“ ，注意,标点.\r\n".encode("utf-8"))
            stream = io.StringIO()
            with redirect_stdout(stream):
                code = MODULE.main([str(path), "--apply"])
            self.assertEqual(code, 0)
            self.assertEqual(
                path.read_bytes(),
                "开头 “错”，注意，标点。\r\n".encode("utf-8"),
            )

    def test_second_apply_is_clean_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.md"
            path.write_text("正文“错“。", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(MODULE.main([str(path), "--apply"]), 0)
            before = path.read_bytes()
            with redirect_stdout(io.StringIO()):
                self.assertEqual(MODULE.main([str(path), "--apply"]), 0)
            self.assertEqual(path.read_bytes(), before)

    def test_non_utf8_file_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.txt"
            path.write_bytes(b"caf\xe9 \x00")
            stream = io.StringIO()
            with redirect_stdout(stream):
                code = MODULE.main([str(path)])
            self.assertEqual(code, 1)
            self.assertIn("skipped", stream.getvalue())

    def test_nul_anywhere_in_file_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "late-nul.txt"
            path.write_bytes(b"a" * 5000 + b"\x00" + "正文".encode("utf-8"))
            stream = io.StringIO()
            with redirect_stdout(stream):
                code = MODULE.main([str(path)])
            self.assertEqual(code, 1)
            self.assertIn("skipped", stream.getvalue())

    def test_fixed_prints_corrected_text_and_returns_zero(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = MODULE.main(["--text", "中文 ，", "--fixed"])
        self.assertEqual(code, 0)
        self.assertEqual(stream.getvalue(), "中文，")

    def test_fixed_returns_one_when_review_remains(self):
        with redirect_stdout(io.StringIO()):
            code = MODULE.main(["--text", "他说“你好", "--fixed"])
        self.assertEqual(code, 1)

    def test_fixed_with_json_is_rejected(self):
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
            MODULE.main(["--text", "中文 ，", "--fixed", "--format", "json"])

    def test_json_reports_original_line_and_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.md"
            path.write_text("第一行\n正文“错“。\n", encoding="utf-8")
            stream = io.StringIO()
            with redirect_stdout(stream):
                MODULE.main([str(path), "--format", "json"])
            issue = json.loads(stream.getvalue())["files"][0]["issues"][0]
            self.assertEqual(issue["rule"], "QT001")
            self.assertEqual((issue["line"], issue["column"]), (2, 5))


if __name__ == "__main__":
    unittest.main()
