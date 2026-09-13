from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "git-commit" / "SKILL.md"
DEFAULTS = ROOT / "skills" / "git-commit" / "references" / "default-rules.md"
EXECUTION = ROOT / "skills" / "git-commit" / "references" / "commit-execution.md"
WORKFLOW = ROOT / "skills" / "git-commit" / "references" / "workflow.md"


class GitCommitSkillContractTests(unittest.TestCase):
    """Contract checks for the git-commit skill.

    Assert patterns, not prose. Wording is expected to evolve; the contract is
    not. Rewording a guarantee in the skill must not break these tests unless
    the guarantee itself is removed.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.defaults = DEFAULTS.read_text(encoding="utf-8")
        cls.execution = EXECUTION.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def assert_contract(self, text: str, pattern: str, label: str) -> None:
        self.assertRegex(text, pattern, f"missing contract: {label}")

    def test_breaking_change_supports_subject_or_footer_marker(self) -> None:
        self.assertIn("`!` before `:` or a `BREAKING CHANGE:` footer", self.skill)
        self.assertIn("either form is valid, and both may be used", self.skill)
        self.assertIn("`BREAKING-CHANGE:` is a valid synonym", self.defaults)
        self.assertIn("BREAKING CHANGE: clients must migrate", self.defaults)

    def test_message_and_commit_modes_preserve_the_staging_boundary(self) -> None:
        self.assert_contract(
            self.skill, r"Message mode.*draft a message without changing Git state",
            "message mode does not touch Git state",
        )
        self.assert_contract(
            self.skill, r"Commit mode.*create one or more atomic commits",
            "commit mode creates atomic commits",
        )
        self.assert_contract(
            self.skill, r"Never stage changes outside the selected scope",
            "staging stays inside the selected scope",
        )
        self.assert_contract(
            self.skill, r"use only the staged diff as message evidence",
            "staged diff is the message evidence",
        )
        self.assert_contract(
            self.skill, r"leave unstaged and untracked changes out",
            "unstaged and untracked changes stay out of the message",
        )
        self.assert_contract(
            self.workflow, r"`MM file` — both staged and unstaged",
            "ambiguous porcelain columns have worked examples",
        )

    def test_porcelain_status_columns_determine_the_commit_scope(self) -> None:
        """Guard the XY-column rule: `X` is staged, `Y` is unstaged, `??` is untracked."""
        self.assert_contract(self.skill, r"porcelain", "porcelain status is the scope source")
        self.assert_contract(
            self.skill, r"X` is the index/staged state and `Y` is the working-tree/unstaged",
            "X/Y column semantics",
        )
        self.assert_contract(
            self.skill, r"\?` in `\?\?` means untracked, not staged",
            "?? means untracked, not staged",
        )
        self.assert_contract(
            self.skill, r"Do not infer staging boundaries from the number of edited files",
            "staging boundaries are not inferred from file counts",
        )

    def test_incompatible_repository_rules_and_split_intents_stop(self) -> None:
        self.assert_contract(
            self.skill,
            r"Scope is required and must name a module, package, or area that already exists",
            "scopes must name an existing area",
        )
        self.assert_contract(self.skill, r"never invent one", "scopes are never invented")
        self.assertIn("feat(common&share&tool)", self.skill)
        self.assertIn("feat(common&share&tool)", self.defaults)
        self.assert_contract(
            self.skill,
            r"split them into separate commits",
            "a joined scope never merges unrelated intents",
        )
        self.assert_contract(
            self.execution,
            r"Quote every `-m` argument",
            "shell metacharacters in a scope stay quoted",
        )
        self.assert_contract(
            self.skill, r"incompatible message format, stop and report the conflict",
            "incompatible repository rules stop the run",
        )
        self.assert_contract(
            self.defaults, r"If no intent dominates, recommend splitting",
            "no dominant intent recommends splitting",
        )
        self.assert_contract(
            self.skill, r"Never include unrelated user changes",
            "unrelated user changes are never absorbed",
        )

    def test_one_language_per_run(self) -> None:
        self.assert_contract(
            self.skill,
            r"Use one language for every message in a run",
            "one language per run",
        )
        self.assert_contract(
            self.skill,
            r"never mix languages inside a subject, inside a body, or between the commits",
            "no language mixing inside a message or across commits",
        )
        self.assert_contract(
            self.skill,
            r"Leave identifiers, file names, API names, and type names untranslated",
            "identifiers stay untranslated",
        )

    def test_every_reference_is_routed_from_the_skill(self) -> None:
        """SKILL.md must link each reference it defers to, with no nested chain."""
        references = sorted(
            path.name for path in (SKILL.parent / "references").glob("*.md")
        )
        self.assertTrue(references, "the skill must keep its references")
        for name in references:
            self.assertIn(
                f"references/{name}",
                self.skill,
                f"{name} is not routed from SKILL.md",
            )

    def test_repository_rule_discovery_reaches_message_mode(self) -> None:
        """Regression: discovery used to sit behind a commit-mode-only route."""
        self.assert_contract(
            self.skill,
            r"Discover enforceable commit rules before writing any message, in both modes",
            "discovery is mandatory in both modes",
        )
        self.assert_contract(
            self.skill,
            r"Commit mode, or any message mode that inspects the diff",
            "the workflow route reaches message mode",
        )
        self.assert_contract(
            self.workflow,
            r"Also check paths that `git status --short` reports as untracked",
            "discovery also covers rule files that are not tracked yet",
        )

    def test_staging_boundary_conditions_are_pinned(self) -> None:
        self.assert_contract(
            self.skill,
            r"Ask exactly one A/B question only when at least one path has an actual staged/index status",
            "the A/B question condition is stated",
        )
        self.assert_contract(
            self.skill,
            r"do not ask A/B for multiple unstaged files",
            "an empty index does not trigger the A/B question",
        )
        self.assert_contract(
            self.workflow,
            r"`A  file` — staged new file",
            "staged new files appear among the porcelain examples",
        )
        self.assert_contract(
            self.workflow,
            r"`AM file` — staged new file, edited again afterwards",
            "staged-then-edited files appear among the porcelain examples",
        )

    def test_execution_guards_the_index_and_the_operation_state(self) -> None:
        self.assert_contract(
            self.execution,
            r"`MERGE_HEAD`, `REBASE_HEAD`, `CHERRY_PICK_HEAD`",
            "an in-progress merge, rebase, or cherry-pick stops the run",
        )
        self.assert_contract(
            self.execution,
            r"git apply --cached",
            "hunk staging has a non-interactive path",
        )

    def test_sensitive_and_high_risk_git_operations_require_explicit_request(
        self,
    ) -> None:
        self.assert_contract(self.skill, r"Never expose secret values", "secrets stay masked")
        self.assert_contract(
            self.skill, r"never commit suspected secret", "suspected secrets are never committed"
        )
        self.assert_contract(
            self.skill, r"pause and ask", "unsuitable changes pause for a decision"
        )
        self.assert_contract(
            self.skill, r"Do not create or switch branches, push, amend, rebase",
            "high-risk Git operations need an explicit request",
        )
        self.assert_contract(
            self.execution,
            r"Do not amend, bypass hooks, disable signing, or use `--no-verify`",
            "commit execution keeps hooks and signing intact",
        )

    def test_commit_verification_checks_the_recorded_path_set(self) -> None:
        self.assert_contract(
            self.execution, r"Record that group's staged path set",
            "the intended staged path set is recorded",
        )
        self.assert_contract(
            self.execution, r"Read the committed path set", "the committed path set is read back"
        )
        self.assert_contract(
            self.execution, r"committed paths match the recorded staged set",
            "committed paths are compared with the recorded set",
        )


class GitCommitWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.git("init")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test User")
        (self.repo / "README.md").write_text("base\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-m", "chore: initialize repository")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            check=check,
            text=True,
            capture_output=True,
        )

    def test_cached_diff_excludes_unstaged_and_untracked_changes(self) -> None:
        (self.repo / "staged.py").write_text("staged = True\n", encoding="utf-8")
        self.git("add", "staged.py")
        (self.repo / "README.md").write_text("unstaged\n", encoding="utf-8")
        (self.repo / "untracked.py").write_text("untracked = True\n", encoding="utf-8")

        self.assertEqual(
            self.git("diff", "--cached", "--name-only").stdout.splitlines(),
            ["staged.py"],
        )
        self.assertEqual(
            self.git("diff", "--name-only").stdout.splitlines(), ["README.md"]
        )
        self.assertIn("?? untracked.py", self.git("status", "--short").stdout)

    def test_empty_index_has_no_cached_diff(self) -> None:
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")

        self.assertEqual(self.git("diff", "--cached", "--name-only").stdout, "")
        self.assertEqual(
            self.git("diff", "--name-only").stdout.splitlines(), ["README.md"]
        )

    def test_rejected_hook_preserves_the_staged_path_set(self) -> None:
        (self.repo / "staged.py").write_text("staged = True\n", encoding="utf-8")
        self.git("add", "staged.py")
        before = self.git("diff", "--cached", "--name-only").stdout
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)

        result = self.git("commit", "-m", "feat: add staged module", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("diff", "--cached", "--name-only").stdout, before)
        self.assertEqual(
            self.git("log", "-1", "--format=%s").stdout.strip(),
            "chore: initialize repository",
        )

    def test_successful_commit_matches_recorded_staged_paths(self) -> None:
        (self.repo / "staged.py").write_text("staged = True\n", encoding="utf-8")
        self.git("add", "staged.py")
        (self.repo / "untracked.py").write_text("untracked = True\n", encoding="utf-8")
        intended_paths = self.git("diff", "--cached", "--name-only").stdout.splitlines()

        self.git("commit", "-m", "feat: add staged module")

        committed_paths = self.git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"
        ).stdout.splitlines()
        self.assertEqual(committed_paths, intended_paths)
        self.assertIn("?? untracked.py", self.git("status", "--short").stdout)


if __name__ == "__main__":
    unittest.main()
