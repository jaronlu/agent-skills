from __future__ import annotations

import json
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


class SkillContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.skill = self.root / "skills" / "alpha"
        self.skill.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_skill(self, body: str, frontmatter: str = "name: alpha\ndescription: test skill\n") -> None:
        (self.skill / "SKILL.md").write_text(
            f"---\n{frontmatter}---\n\n{body}",
            encoding="utf-8",
        )

    def validate(self) -> list[str]:
        with patch.object(validate_skills, "ROOT", self.root):
            return validate_skills.validate_skill(self.skill)

    def test_rejects_skill_over_500_lines(self) -> None:
        body = "# Alpha\n" + "\n".join(f"line {index}" for index in range(500))
        self.write_skill(body)
        errors = self.validate()
        self.assertTrue(any("exceeds 500 lines" in error for error in errors))

    def test_rejects_duplicate_frontmatter_field(self) -> None:
        self.write_skill(
            "# Alpha\n",
            "name: alpha\ndescription: test skill\nname: alpha\n",
        )
        errors = self.validate()
        self.assertTrue(any("duplicate frontmatter field: name" in error for error in errors))

    def test_rejects_missing_resource_path(self) -> None:
        self.write_skill("# Alpha\n\nRead `references/missing.md`.\n")
        errors = self.validate()
        self.assertTrue(any("referenced resource does not exist" in error for error in errors))

    def test_rejects_unreferenced_reference(self) -> None:
        (self.skill / "references").mkdir()
        (self.skill / "references" / "guide.md").write_text("guide", encoding="utf-8")
        self.write_skill("# Alpha\n")
        errors = self.validate()
        self.assertTrue(
            any("packaged resource is not referenced from SKILL.md" in error for error in errors)
        )

    def test_accepts_referenced_resource(self) -> None:
        (self.skill / "references").mkdir()
        (self.skill / "references" / "guide.md").write_text("guide", encoding="utf-8")
        self.write_skill("# Alpha\n\nRead `references/guide.md`.\n")
        self.assertEqual(self.validate(), [])


class DiagramContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.assets = self.root / "assets"
        self.assets.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_flow(
        self,
        attrs: str = 'width="680" height="200" viewBox="0 0 680 200" role="img" font-family="system-ui"',
        body: str = "<title>Alpha</title><desc>Alpha flow</desc>",
    ) -> list[str]:
        path = self.assets / "alpha-flow.svg"
        path.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" {attrs}>{body}</svg>',
            encoding="utf-8",
        )
        with patch.object(validate_skills, "ROOT", self.root):
            root, error = validate_skills.parse_svg(path)
            self.assertIsNone(error)
            return validate_skills.validate_flow_spec(path, root)

    def test_accepts_valid_flow_root(self) -> None:
        self.assertEqual(self.write_flow(), [])

    def test_reports_missing_accessibility(self) -> None:
        errors = self.write_flow(
            'width="680" height="200" viewBox="0 0 680 200" font-family="system-ui"',
            "",
        )
        self.assertTrue(any('role="img"' in error for error in errors))
        self.assertTrue(any("missing a non-empty <title>" in error for error in errors))
        self.assertTrue(any("missing a non-empty <desc>" in error for error in errors))

    def test_reports_wrong_width(self) -> None:
        errors = self.write_flow('width="1200" height="200" viewBox="0 0 1200 200" role="img" font-family="system-ui"')
        self.assertTrue(any("width must be 680" in error for error in errors))
        self.assertTrue(any("flow diagram viewBox must be" in error for error in errors))

    def test_classifies_diagram_names(self) -> None:
        names = {"alpha"}
        self.assertEqual(validate_skills.classify_root_diagram("alpha-flow.svg", names), ("flow", "alpha"))
        self.assertEqual(
            validate_skills.classify_root_diagram("alpha-review-flow.svg", names),
            ("topic-flow", "alpha"),
        )
        self.assertEqual(
            validate_skills.classify_root_diagram("repository-overview.svg", names),
            ("repo", None),
        )
        self.assertEqual(validate_skills.classify_root_diagram("other.svg", names), ("unknown", None))

    def test_root_diagrams_require_primary_and_reject_unknown(self) -> None:
        (self.assets / "unexpected.svg").write_text("<svg xmlns=\"http://www.w3.org/2000/svg\"/>", encoding="utf-8")
        with patch.object(validate_skills, "ROOT", self.root):
            errors, names = validate_skills.validate_root_diagrams({"alpha"})
        self.assertIn("unexpected.svg", names)
        self.assertTrue(any("unrecognized root diagram" in error for error in errors))
        self.assertTrue(any("missing required skill diagram" in error for error in errors))

    def test_catalog_requires_diagram_entry(self) -> None:
        for catalog in ("README.md", "README_zh-CN.md"):
            (self.root / catalog).write_text("skills/alpha/SKILL.md\n", encoding="utf-8")
        with patch.object(validate_skills, "ROOT", self.root):
            errors = validate_skills.validate_catalog({"alpha"}, {"alpha-flow.svg"})
        self.assertTrue(any("missing diagram entry for alpha-flow.svg" in error for error in errors))
        self.assertEqual(len(errors), 2)


class DistributionValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir(parents=True)
        self.config = self.root / "config" / "skill-links.toml"
        self.source = self.root / "source"
        for name in ("alpha", "beta", "gamma"):
            skill = self.source / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: test\n---\n", encoding="utf-8"
            )
        self.target = self.root / "target"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def check(self, body: str, skill_names: set[str] | None = None) -> list[str]:
        body = body.replace(
            "[distribution]",
            f"[distribution]\nsource = {json.dumps(str(self.source))}",
        )
        self.config.write_text(body, encoding="utf-8")
        with patch.object(validate_skills, "ROOT", self.root), patch.object(
            validate_skills, "CONFIG_PATH", self.config
        ):
            return validate_skills.validate_distribution(skill_names or {"alpha", "beta"})

    def test_accepts_complete_coverage(self) -> None:
        config = """\
version = 1
[distribution]
[targets.agents]
path = "~/.agents/skills"
skills = ["alpha", "beta"]
excluded = []
"""
        self.assertEqual(self.check(config), [])

    def test_accepts_omitted_excluded_list(self) -> None:
        config = """\
version = 1
[distribution]
[targets.agents]
path = "~/.agents/skills"
skills = ["alpha", "beta"]
"""
        self.assertEqual(self.check(config), [])

    def test_reports_uncovered_skill(self) -> None:
        config = """\
version = 1
[distribution]
[targets.agents]
path = "~/.agents/skills"
skills = ["alpha"]
excluded = []
"""
        errors = self.check(config)
        self.assertTrue(any("does not install or exclude: ['beta']" in error for error in errors))

    def test_reports_overlap(self) -> None:
        config = """\
version = 1
[distribution]
[targets.agents]
path = "~/.agents/skills"
skills = ["alpha", "beta"]
excluded = ["beta"]
"""
        errors = self.check(config)
        self.assertTrue(any("both installed and excluded" in error for error in errors))

    def test_reports_unknown_skill(self) -> None:
        config = """\
version = 1
[distribution]
[targets.agents]
path = "~/.agents/skills"
skills = ["alpha", "beta", "delta"]
"""
        errors = self.check(config)
        self.assertTrue(any("unknown or invalid skill" in error for error in errors))

    def test_accepts_profile_targets(self) -> None:
        config = """\
version = 1
[distribution]
[profiles.core]
skills = ["alpha"]
excluded = ["beta", "gamma"]
[profiles.full]
extends = "core"
skills = ["beta"]
[targets.agents]
path = "~/.agents/skills"
profile = "full"
"""
        self.assertEqual(
            self.check(config, {"alpha", "beta", "gamma"}),
            [],
        )

    def test_profile_target_must_cover_every_skill(self) -> None:
        config = """\
version = 1
[distribution]
[profiles.core]
skills = ["alpha"]
excluded = ["beta"]
[targets.agents]
path = "~/.agents/skills"
profile = "core"
"""
        errors = self.check(config, {"alpha", "beta", "gamma"})
        self.assertTrue(any("does not install or exclude: ['gamma']" in error for error in errors))

    def test_requires_agents_target(self) -> None:
        config = """\
version = 1
[distribution]
[targets.other]
path = "~/.other/skills"
skills = ["alpha", "beta"]
"""
        errors = self.check(config)
        self.assertTrue(any("missing required [targets.agents]" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
