from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills" / "chrome-bookmarks"
SCRIPT = PACKAGE / "scripts" / "chrome_bookmarks.py"
SKILL = PACKAGE / "SKILL.md"
WRITEBACK = PACKAGE / "references" / "writeback.md"
TAXONOMY = PACKAGE / "references" / "taxonomy.md"
SCHEMA = PACKAGE / "references" / "schema.md"


def load_script():
    spec = importlib.util.spec_from_file_location("chrome_bookmarks_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def url(name: str) -> dict:
    return {"type": "url", "name": name, "url": f"https://{name}.example"}


def folder(name: str, children: list[dict] | None = None) -> dict:
    return {"type": "folder", "name": name, "children": children or []}


def bookmarks_doc(
    bar: list[dict],
    other: list[dict] | None = None,
    synced: list[dict] | None = None,
) -> dict:
    return {
        "checksum": "0",
        "sync_metadata": {},
        "version": 1,
        "roots": {
            "bookmark_bar": folder("书签栏", bar),
            "other": folder("其他书签", other),
            "synced": folder("移动设备书签", synced),
        },
    }


class ChromeBookmarksSkillTests(unittest.TestCase):
    """Behavior of the writeback gate and CLI, plus open-source hygiene."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.user_data = Path(self.temp.name) / "userdata"
        self.profile_dir = self.user_data / "Profile 5"
        self.profile_dir.mkdir(parents=True)
        (self.user_data / "Local State").write_text(
            json.dumps({"profile": {"last_used": "Profile 5"}}), encoding="utf-8"
        )
        self.live = self.profile_dir / "Bookmarks"
        self.module = load_script()

    def write_doc(self, path: Path, doc: dict) -> Path:
        path.write_text(json.dumps(doc), encoding="utf-8")
        return path

    def run_cli(self, *argv: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *argv],
            capture_output=True,
            text=True,
            check=False,
        )

    def run_write(
        self, src: Path, chrome_running: bool | None = False, extra: tuple[str, ...] = ()
    ) -> tuple[int, str]:
        from contextlib import redirect_stderr, redirect_stdout
        from io import StringIO

        out, err = StringIO(), StringIO()
        argv = ["write", "--src", str(src), "--user-data", str(self.user_data), *extra]
        with (
            mock.patch.object(self.module, "chrome_running", return_value=chrome_running),
            mock.patch.object(sys, "argv", ["chrome_bookmarks.py", *argv]),
            redirect_stdout(out),
            redirect_stderr(err),
        ):
            code = self.module.main()
        return code, out.getvalue() + err.getvalue()

    def test_flags_parse_before_and_after_the_subcommand(self) -> None:
        self.write_doc(self.live, bookmarks_doc([folder("Agent", [url("openai")])]))
        for argv in (
            ("inspect", "--user-data", str(self.user_data)),
            ("--user-data", str(self.user_data), "inspect"),
            ("--assume-quit", "inspect", "--user-data", str(self.user_data)),
        ):
            result = self.run_cli(*argv)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"user_data={self.user_data}", result.stdout)

    def test_default_user_data_follows_the_platform(self) -> None:
        cases = {
            "darwin": "Library/Application Support/Google/Chrome",
            "win32": "Google/Chrome/User Data",
            "linux": ".config/google-chrome",
        }
        for platform, suffix in cases.items():
            with mock.patch.object(self.module.sys, "platform", platform):
                resolved = self.module.default_user_data().as_posix()
                self.assertTrue(resolved.endswith(suffix), f"{platform}: {resolved}")

    def test_write_refuses_when_the_process_check_is_unavailable(self) -> None:
        self.write_doc(self.live, bookmarks_doc([folder("旧")]))
        before = self.live.read_text()
        prepared = self.write_doc(
            Path(self.temp.name) / "prepared.json", bookmarks_doc([folder("Agent")])
        )
        code, output = self.run_write(prepared, chrome_running=None)
        self.assertEqual(code, 2, output)
        self.assertIn("--assume-quit", output)
        self.assertEqual(self.live.read_text(), before)

    def test_assume_quit_writes_with_a_warning(self) -> None:
        self.write_doc(self.live, bookmarks_doc([folder("旧")]))
        prepared = self.write_doc(
            Path(self.temp.name) / "prepared.json", bookmarks_doc([folder("Agent")])
        )
        code, output = self.run_write(prepared, chrome_running=None, extra=("--assume-quit",))
        self.assertEqual(code, 0, output)
        self.assertIn("warning:", output)
        self.assertEqual(
            [
                child["name"]
                for child in json.loads(self.live.read_text())["roots"]["bookmark_bar"]["children"]
            ],
            ["Agent"],
        )

    def test_inspect_reports_every_root(self) -> None:
        self.write_doc(
            self.live,
            bookmarks_doc(
                [folder("Agent", [url("openai")])],
                other=[url("m1"), url("m2")],
                synced=[url("m3")],
            ),
        )
        result = self.run_cli("inspect", "--user-data", str(self.user_data))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("root bookmark_bar (书签栏): urls=1", result.stdout)
        self.assertIn("root other (其他书签): urls=2", result.stdout)
        self.assertIn("root synced (移动设备书签): urls=1", result.stdout)
        self.assertIn("urls_total=4", result.stdout)

    def test_inspect_lists_top_level_folders(self) -> None:
        self.write_doc(self.live, bookmarks_doc([folder("Agent"), folder("归档")]))
        result = self.run_cli("inspect", "--user-data", str(self.user_data))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("top_level_folders=Agent, 归档", result.stdout)

    def test_diff_reports_added_removed_moved_and_renamed(self) -> None:
        old = self.write_doc(
            Path(self.temp.name) / "old.json",
            bookmarks_doc([folder("旧", [url("a"), url("b")])]),
        )
        new = self.write_doc(
            Path(self.temp.name) / "new.json",
            bookmarks_doc(
                [
                    folder(
                        "Agent",
                        [
                            {"type": "url", "name": "a-renamed", "url": "https://a.example"},
                            url("c"),
                        ],
                    )
                ]
            ),
        )
        result = self.run_cli("diff", "--old", str(old), "--new", str(new))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("old_urls=2 new_urls=2", result.stdout)
        self.assertIn("kept=1 added=1 removed=1 moved=1 renamed=1", result.stdout)
        self.assertIn("top_level_change=changed", result.stdout)
        self.assertIn("  removed  https://b.example", result.stdout)
        self.assertIn("  added    https://c.example", result.stdout)

    def test_process_probe_counts_only_the_browser(self) -> None:
        def verdict(stdout: str) -> bool | None:
            result = subprocess.CompletedProcess(args=["ps"], returncode=0, stdout=stdout)
            return self.module._ps_verdict(result)

        self.assertFalse(
            verdict(
                "/Applications/Visual Studio Code.app/Contents/Frameworks/"
                "Electron Framework.framework/Helpers/chrome_crashpad_handler\n"
            )
        )
        self.assertTrue(verdict("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome\n"))
        self.assertTrue(verdict("Google Chrome Helper (Renderer)\n"))
        self.assertTrue(verdict("/Applications/Chromium.app/Contents/MacOS/Chromium\n"))

    def test_write_keeps_the_previous_tree_as_a_rollback_copy(self) -> None:
        self.write_doc(self.live, bookmarks_doc([folder("旧")], other=[url("m1")]))
        prepared = self.write_doc(
            Path(self.temp.name) / "prepared.json",
            bookmarks_doc([folder("Agent"), folder("归档")]),
        )
        code, output = self.run_write(prepared)
        self.assertEqual(code, 0, output)
        self.assertEqual(
            [child["name"] for child in json.loads(self.live.read_text())["roots"]["bookmark_bar"]["children"]],
            ["Agent", "归档"],
        )
        rollback = json.loads((self.profile_dir / "Bookmarks.bak").read_text())
        self.assertEqual([child["name"] for child in rollback["roots"]["bookmark_bar"]["children"]], ["旧"])
        self.assertEqual(len(rollback["roots"]["other"]["children"]), 1)
        self.assertEqual((self.live.stat().st_mode & 0o777), 0o600)
        self.assertEqual(list(self.profile_dir.glob("*.tmp")), [])
        self.assertIn("top_level_folders=Agent, 归档", output)

    def test_write_warns_when_a_root_would_be_emptied(self) -> None:
        self.write_doc(self.live, bookmarks_doc([folder("旧")], other=[url("m1"), url("m2")]))
        prepared = self.write_doc(
            Path(self.temp.name) / "prepared.json", bookmarks_doc([folder("Agent")])
        )
        code, output = self.run_write(prepared)
        self.assertEqual(code, 0, output)
        self.assertIn("warning:", output)
        self.assertIn("其他书签", output)

    def test_write_refuses_a_non_bookmarks_document(self) -> None:
        self.write_doc(self.live, bookmarks_doc([folder("旧")]))
        before = self.live.read_text()
        prepared = self.write_doc(Path(self.temp.name) / "other.json", {"hello": "world"})
        code, output = self.run_write(prepared)
        self.assertEqual(code, 1, output)
        self.assertIn("roots.bookmark_bar", output)
        self.assertEqual(self.live.read_text(), before)

    def test_write_refuses_while_chrome_is_running(self) -> None:
        self.write_doc(self.live, bookmarks_doc([folder("旧")]))
        before = self.live.read_text()
        prepared = self.write_doc(
            Path(self.temp.name) / "prepared.json", bookmarks_doc([folder("Agent")])
        )
        code, output = self.run_write(prepared, chrome_running=True)
        self.assertEqual(code, 2, output)
        self.assertIn("still running", output)
        self.assertEqual(self.live.read_text(), before)
        self.assertFalse((self.profile_dir / "Bookmarks.bak").exists())

    def test_contracts_survive_rewordings(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        writeback = WRITEBACK.read_text(encoding="utf-8")
        taxonomy = TAXONOMY.read_text(encoding="utf-8")
        schema = SCHEMA.read_text(encoding="utf-8")
        self.assertIn("`bookmark_bar`, `other`, `synced`", skill)
        self.assertIn("roots.bookmark_bar", skill)
        self.assertRegex(skill, r"outside this skill package")
        self.assertIn("Bookmarks.bak", writeback)
        self.assertIn("roots.bookmark_bar", writeback)
        self.assertRegex(taxonomy, r"always wins")
        self.assertIn("Default pattern", taxonomy)
        self.assertRegex(taxonomy, r"Rename, merge, or drop")
        self.assertRegex(taxonomy, r"at most three levels")
        self.assertIn("`<company>·<slug>`", taxonomy)
        self.assertRegex(taxonomy, r"work → study → ai → dev → tools → chore → misc")
        for folder in ("work/", "study/", "dev/", "ai/", "tools/", "chore/", "misc/"):
            self.assertRegex(taxonomy, rf"(?m)^{re.escape(folder)}")
        for folder in ("agent/", "relay/"):
            self.assertRegex(taxonomy, rf"(?m)^  {re.escape(folder)}")
        self.assertRegex(taxonomy, r"only when that one domain keeps four or more bookmarks")
        self.assertIn("`<company>·<slug>`", skill)
        self.assertRegex(skill, r"three levels")
        self.assertRegex(
            (PACKAGE / "references" / "cleanup-rules.md").read_text(encoding="utf-8"),
            r"overrides them",
        )
        self.assertIn("references/schema.md", skill)
        self.assertRegex(skill, r"top-level unchanged")
        self.assertRegex(skill, r"never loosen the guard")
        self.assertRegex(writeback, r"(?m)^## Rollback")
        self.assertIn("pgrep -fl", writeback)
        self.assertRegex(writeback, r"never edit the guard")
        self.assertRegex(taxonomy, r"never delete it for being empty")
        self.assertRegex(taxonomy, r"keep their own title")
        self.assertIn("1601", schema)
        self.assertIn("roots.bookmark_bar", schema)

    def test_package_has_no_private_identifiers(self) -> None:
        offenders: list[str] = []
        for path in sorted(PACKAGE.rglob("*")):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern, label in (
                (r"/Users/[A-Za-z0-9._-]+", "absolute home path"),
                (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "email address"),
            ):
                if re.search(pattern, text):
                    offenders.append(f"{path.relative_to(ROOT)}: {label}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
