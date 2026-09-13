from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_skills


class ValidateSkillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.skill = self.root / "skills" / "alpha"
        (self.skill / "agents").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_package(self, frontmatter: str, interface: str) -> None:
        (self.skill / "SKILL.md").write_text(
            f"---\n{frontmatter}\n---\n\n# Alpha\n",
            encoding="utf-8",
        )
        (self.skill / "agents" / "openai.yaml").write_text(
            f"interface:\n{interface}\n",
            encoding="utf-8",
        )

    def validate(self) -> list[str]:
        with patch.object(validate_skills, "ROOT", self.root):
            return validate_skills.validate_skill(self.skill)

    def test_accepts_supported_optional_fields(self) -> None:
        self.write_package(
            "\n".join(
                [
                    "name: alpha",
                    "description: test skill",
                    "license: MIT",
                    "allowed-tools:",
                    "  - Read",
                    "metadata:",
                    "  owner: local",
                ]
            ),
            "\n".join(
                [
                    '  display_name: "Alpha"',
                    '  short_description: "A sufficiently long test description"',
                    '  default_prompt: "Use $alpha for this test."',
                    '  icon_small: "./assets/icon.png"',
                    '  brand_color: "#336699"',
                ]
            ),
        )
        self.assertEqual(self.validate(), [])

    def test_rejects_unknown_fields(self) -> None:
        self.write_package(
            "\n".join(
                [
                    "name: alpha",
                    "description: test skill",
                    "unknown-field: value",
                ]
            ),
            "\n".join(
                [
                    '  display_name: "Alpha"',
                    '  short_description: "A sufficiently long test description"',
                    '  default_prompt: "Use $alpha for this test."',
                    '  unknown_field: "value"',
                ]
            ),
        )
        errors = self.validate()
        self.assertTrue(any("unsupported frontmatter fields ['unknown-field']" in error for error in errors))
        self.assertTrue(any("unsupported interface fields ['unknown_field']" in error for error in errors))


class DiagramValidationTests(unittest.TestCase):
    """Guard the RULES.md text-safety boundary: SVG text never wraps, it clips."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.assets = self.root / "assets"
        self.assets.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def check(self, body: str, *, height: int = 200) -> list[str]:
        path = self.assets / "alpha-flow.svg"
        path.write_text(
            f'<svg viewBox="0 0 680 {height}" width="680" height="{height}"'
            f' xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="680" height="{height}" fill="#FFFFFF"/>{body}</svg>',
            encoding="utf-8",
        )
        with patch.object(validate_skills, "ROOT", self.root):
            return validate_skills.validate_diagram(path)

    def test_accepts_text_inside_its_box(self) -> None:
        body = (
            '<rect x="40" y="20" width="600" height="52"/>'
            '<text x="60" y="40" font-size="12">hello</text>'
        )
        self.assertEqual(self.check(body), [])

    def test_reports_text_past_the_box_bottom(self) -> None:
        body = (
            '<rect x="40" y="20" width="600" height="52"/>'
            '<text x="60" y="70" font-size="12">hello</text>'
        )
        errors = self.check(body)
        self.assertEqual(len(errors), 1)
        self.assertIn("overflows its box", errors[0])

    def test_reports_text_past_the_box_right_edge(self) -> None:
        body = (
            '<rect x="40" y="20" width="120" height="52"/>'
            '<text x="60" y="40" font-size="12">this line is far too wide</text>'
        )
        errors = self.check(body)
        self.assertEqual(len(errors), 1)
        self.assertIn("overflows its box", errors[0])

    def test_reports_centered_text_past_the_box_edge(self) -> None:
        body = (
            '<rect x="190" y="20" width="300" height="44"/>'
            '<text x="340" y="42" text-anchor="middle" font-size="14">'
            "设计评审输入：正文 / 文档 / 文件集 / 文件夹</text>"
        )
        errors = self.check(body)
        self.assertEqual(len(errors), 1)
        self.assertIn("overflows its box", errors[0])

    def test_reports_text_with_no_box_beyond_the_canvas(self) -> None:
        body = f'<text x="60" y="40" font-size="12">{"x" * 200}</text>'
        errors = self.check(body)
        self.assertEqual(len(errors), 1)
        self.assertIn("leaves the canvas", errors[0])

    def test_reports_malformed_svg(self) -> None:
        path = self.assets / "alpha-flow.svg"
        path.write_text("<svg><rect></svg>", encoding="utf-8")
        with patch.object(validate_skills, "ROOT", self.root):
            errors = validate_skills.validate_diagram(path)
        self.assertEqual(len(errors), 1)
        self.assertIn("malformed SVG", errors[0])


if __name__ == "__main__":
    unittest.main()
