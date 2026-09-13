from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.manage_skill_links import ConfigError, apply_plan, build_plan, load_config, main, verify


class SkillLinkManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.target = self.root / "target"
        self.config_path = self.root / "skill-links.toml"
        self.create_skill("alpha")
        self.create_skill("beta")
        self.write_config(["alpha"])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def create_skill(self, name: str) -> None:
        skill = self.source / "skills" / name
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: test\n---\n", encoding="utf-8")

    def write_config(
        self, skills: list[str], *, source: Path | None = None, mode: str | None = None
    ) -> None:
        source = source or self.source
        quoted = ", ".join(json.dumps(skill) for skill in skills)
        mode_line = [f"mode = {json.dumps(mode)}"] if mode else []
        self.config_path.write_text(
            "\n".join(
                [
                    "version = 1",
                    "",
                    "[distribution]",
                    f"source = {json.dumps(str(source))}",
                    "",
                    "[targets.test]",
                    f"path = {json.dumps(str(self.target))}",
                    f"skills = [{quoted}]",
                    *mode_line,
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def sync(self) -> None:
        config = load_config(self.config_path)
        plan = build_plan(config)
        apply_plan(plan)
        verify(config)

    def test_creates_links_and_second_sync_is_noop(self) -> None:
        self.sync()
        link = self.target / "alpha"
        self.assertTrue(link.is_symlink())
        self.assertEqual(Path(os.readlink(link)), self.source / "skills" / "alpha")

        config = load_config(self.config_path)
        plan = build_plan(config)
        self.assertFalse(plan.changes)
        self.assertEqual([op.action for op in plan.operations], ["keep"])

    def test_rejects_duplicate_config_entries(self) -> None:
        self.write_config(["alpha", "alpha"])
        with self.assertRaisesRegex(ConfigError, "duplicates"):
            load_config(self.config_path)

    def test_replaces_existing_directory(self) -> None:
        (self.target / "alpha").mkdir(parents=True)
        (self.target / "alpha" / "old.txt").write_text("old", encoding="utf-8")
        config = load_config(self.config_path)
        plan = build_plan(config)
        self.assertEqual([op.action for op in plan.changes], ["replace"])
        apply_plan(plan)
        self.assertTrue((self.target / "alpha").is_symlink())
        self.assertEqual(Path(os.readlink(self.target / "alpha")), self.source / "skills" / "alpha")

    def test_real_file_is_conflict(self) -> None:
        self.target.mkdir(parents=True)
        (self.target / "alpha").write_text("old", encoding="utf-8")
        config = load_config(self.config_path)
        plan = build_plan(config)
        self.assertEqual(plan.conflicts[0].detail, "real file exists")

    def test_replaces_external_link(self) -> None:
        self.target.mkdir(parents=True)
        (self.target / "alpha").symlink_to(self.root / "external", target_is_directory=True)
        config = load_config(self.config_path)
        plan = build_plan(config)
        self.assertEqual([op.action for op in plan.changes], ["replace"])
        apply_plan(plan)
        self.assertEqual(Path(os.readlink(self.target / "alpha")), self.source / "skills" / "alpha")

    def test_leaves_deselected_link_untouched(self) -> None:
        self.sync()
        self.write_config([])
        config = load_config(self.config_path)
        plan = build_plan(config)
        self.assertFalse(plan.operations)
        apply_plan(plan)
        self.assertTrue((self.target / "alpha").is_symlink())

    def test_source_move_replaces_existing_link(self) -> None:
        self.sync()
        moved = self.root / "moved source"
        self.source.rename(moved)
        self.write_config(["alpha"], source=moved)

        config = load_config(self.config_path)
        plan = build_plan(config)
        self.assertEqual([op.action for op in plan.changes], ["replace"])
        apply_plan(plan)
        verify(config)
        self.assertEqual(Path(os.readlink(self.target / "alpha")), moved / "skills" / "alpha")

    def test_reports_duplicate_alias(self) -> None:
        self.sync()
        (self.target / "alias").symlink_to(self.source / "skills" / "alpha", target_is_directory=True)
        config = load_config(self.config_path)
        plan = build_plan(config)
        self.assertTrue(any("duplicate alias" in op.detail for op in plan.conflicts))

    def test_unlink_removes_current_configured_link_only(self) -> None:
        self.sync()
        external = self.target / "external"
        external.symlink_to(self.root / "elsewhere", target_is_directory=True)
        config = load_config(self.config_path)
        plan = build_plan(config, unlink_all=True)
        apply_plan(plan)
        self.assertFalse(os.path.lexists(self.target / "alpha"))
        self.assertTrue(external.is_symlink())

    def test_check_ignores_deselected_link(self) -> None:
        self.sync()
        self.write_config([])

        args = ["check", "--config", str(self.config_path)]
        self.assertEqual(main(args), 0)
        self.assertTrue((self.target / "alpha").is_symlink())

    def test_copy_mode_publishes_a_real_directory_and_is_idempotent(self) -> None:
        self.write_config(["alpha"], mode="copy")
        self.sync()

        published = self.target / "alpha"
        self.assertFalse(published.is_symlink())
        self.assertTrue((published / "SKILL.md").is_file())

        plan = build_plan(load_config(self.config_path))
        self.assertFalse(plan.changes)
        self.assertEqual([op.action for op in plan.operations], ["keep"])

    def test_copy_mode_replaces_an_outdated_copy(self) -> None:
        self.write_config(["alpha"], mode="copy")
        self.sync()
        published = self.target / "alpha" / "SKILL.md"
        published.write_text("stale\n", encoding="utf-8")

        config = load_config(self.config_path)
        plan = build_plan(config)
        self.assertEqual([op.action for op in plan.changes], ["replace"])
        self.assertEqual(plan.changes[0].detail, "outdated copy")

        apply_plan(plan)
        verify(config)
        self.assertTrue(published.read_text(encoding="utf-8").startswith("---"))

    def test_copy_mode_converts_a_legacy_symlink_into_a_copy(self) -> None:
        self.sync()
        self.assertTrue((self.target / "alpha").is_symlink())

        self.write_config(["alpha"], mode="copy")
        config = load_config(self.config_path)
        plan = build_plan(config)
        self.assertEqual([op.action for op in plan.changes], ["replace"])
        self.assertEqual(plan.changes[0].detail, "non-directory entry")

        apply_plan(plan)
        verify(config)
        self.assertFalse((self.target / "alpha").is_symlink())
        self.assertTrue((self.target / "alpha" / "SKILL.md").is_file())

    def test_unlink_removes_only_a_managed_copy(self) -> None:
        self.write_config(["alpha"], mode="copy")
        self.sync()
        external = self.target / "external"
        external.mkdir()

        config = load_config(self.config_path)
        apply_plan(build_plan(config, unlink_all=True))
        self.assertFalse(os.path.lexists(self.target / "alpha"))
        self.assertTrue(external.is_dir())

    def test_rejects_unknown_sync_mode(self) -> None:
        self.write_config(["alpha"], mode="binary")
        with self.assertRaisesRegex(ConfigError, "mode must be"):
            load_config(self.config_path)


if __name__ == "__main__":
    unittest.main()
