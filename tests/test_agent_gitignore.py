"""Tests for the agent-gitignore skill script."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "agent-gitignore" / "scripts" / "add-entries.sh"


class AgentGitignoreScriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        # Isolate Git from the host's global config, hooks, and excludes file so
        # the test does not depend on machine-specific ignore rules.
        self.env = os.environ.copy()
        self.env["HOME"] = self.tempdir.name
        self.env["XDG_CONFIG_HOME"] = self.tempdir.name
        self.env["GIT_CONFIG_GLOBAL"] = str(self.repo / "gitconfig-global")
        self.env["GIT_CONFIG_NOSYSTEM"] = "1"
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo,
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def run_script(self, *args: str) -> str:
        result = subprocess.run(
            ["/bin/sh", str(SCRIPT), *args],
            cwd=self.repo,
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def write(self, path: str, content: str = "x\n") -> None:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def commit_initial_gitignore(self) -> None:
        self.write(".gitignore", "seed\n")
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "seed")

    def test_adds_present_untracked_artifacts_and_commits_only_gitignore(self) -> None:
        self.commit_initial_gitignore()
        self.write(".workbuddy/memory/m.md")
        self.write(".mimosa/state.json")
        self.write(".claude/settings.local.json", "{}\n")
        self.write("notes.txt")

        output = self.run_script()

        gitignore = (self.repo / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("# agent runtime artifacts", gitignore)
        self.assertIn(".workbuddy/", gitignore)
        self.assertIn(".mimosa/", gitignore)
        self.assertIn(".claude/settings.local.json", gitignore)
        self.assertIn("committed:", output)
        # Only .gitignore may enter the automatic commit.
        self.assertEqual(self.git("show", "--pretty=", "--name-only", "HEAD"), ".gitignore")
        self.assertIn("?? notes.txt", self.git("status", "--porcelain"))

    def test_tracked_artifact_is_reported_and_skipped(self) -> None:
        self.commit_initial_gitignore()
        self.write(".workbuddy/tracked.md")
        self.git("add", ".workbuddy/tracked.md")
        self.git("commit", "-qm", "track")
        self.write(".mimosa/state.json")

        output = self.run_script("--no-commit")

        self.assertIn("tracked, unaffected: .workbuddy/tracked.md (workbuddy; unaffected)", output)
        gitignore = (self.repo / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".mimosa/", gitignore)
        self.assertIn(".workbuddy/", gitignore)

    def test_partially_tracked_directory_is_reported_and_rule_added(self) -> None:
        self.commit_initial_gitignore()
        self.write(".workbuddy/tracked.md")
        self.git("add", ".workbuddy/tracked.md")
        self.git("commit", "-qm", "track")
        self.write(".workbuddy/untracked.md")

        output = self.run_script("--no-commit")

        self.assertIn("tracked, unaffected: .workbuddy/tracked.md (workbuddy; unaffected)", output)
        self.assertIn("\n.workbuddy/\n", (self.repo / ".gitignore").read_text(encoding="utf-8"))
        self.assertEqual(self.git("check-ignore", ".workbuddy/untracked.md"), ".workbuddy/untracked.md")

    def test_non_git_directory_reports_write_without_invoking_git(self) -> None:
        outside_temp = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temp.cleanup)
        outside = Path(outside_temp.name)
        (outside / ".workbuddy").mkdir()
        env = self.env.copy()
        env["PATH"] = "/usr/bin:/bin"

        result = subprocess.run(
            ["/bin/sh", str(SCRIPT), "--no-commit"],
            cwd=outside,
            env=env,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not a git repository", result.stdout)
        self.assertIn("review whether to keep .gitignore", result.stdout)
        self.assertIn(".workbuddy/", (outside / ".gitignore").read_text(encoding="utf-8"))

    def test_second_run_is_idempotent_and_creates_no_commit(self) -> None:
        self.write(".workbuddy/memory/m.md")
        self.run_script()
        head = self.git("rev-parse", "HEAD")
        output = self.run_script()
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertIn("already ignored: .workbuddy/ (workbuddy)", output)

    def test_only_filters_to_requested_agent(self) -> None:
        self.write(".workbuddy/memory/m.md")
        self.write(".mimosa/state.json")
        output = self.run_script("--only", "workbuddy", "--dry-run")
        self.assertIn("would add: .workbuddy/ (workbuddy)", output)
        self.assertNotIn(".mimosa/", output)

    def test_unknown_agent_is_rejected(self) -> None:
        result = subprocess.run(
            ["/bin/sh", str(SCRIPT), "--only", "nope"],
            cwd=self.repo,
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown agent in --only: nope", result.stderr)


if __name__ == "__main__":
    unittest.main()
