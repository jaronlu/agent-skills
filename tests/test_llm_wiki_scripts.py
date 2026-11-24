from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEARCH = ROOT / "skills" / "llm-wiki" / "scripts" / "wiki_search.py"
PAGE = ROOT / "skills" / "llm-wiki" / "scripts" / "wiki_page.py"
VALIDATE = ROOT / "skills" / "llm-wiki" / "scripts" / "wiki_validate.py"
SKILL_DIR = ROOT / "skills" / "llm-wiki"


class LlmWikiScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.write_page(
            "domains/agent/concepts/agent-runtime.md",
            """---
title: Agent Runtime
created: 2026-07-10
updated: 2026-07-10
type: concept
tags: [ai, agent]
sources: [raw/runtime.md]
confidence: high
---

# Agent Runtime

Runtime content links to [[domains/agent/concepts/tool-calling]].
""",
        )
        self.write_page(
            "domains/agent/concepts/tool-calling.md",
            """---
title: Tool Calling
created: 2026-07-10
updated: 2026-07-10
type: concept
tags: [ai, agent]
sources: [raw/tools.md]
confidence: medium
---

# Tool Calling

Backlink target.
""",
        )
        self.write_page("raw/runtime.md", "# Raw runtime\n\nsource facts")
        self.write_page("index.md", "# Wiki Index\n\n- [[domains/agent/concepts/agent-runtime]]")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_page(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_bytes(self, relative: str, content: bytes) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def run_json(self, script: Path, *args: str) -> dict[str, Any]:
        completed = subprocess.run(
            [sys.executable, str(script), "--root", str(self.root), *args, "--json"],
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(completed.stdout)

    def test_search_returns_compact_metadata(self) -> None:
        payload = self.run_json(SEARCH, "--query", "runtime", "--limit", "1")
        self.assertEqual(payload["count"], 1)
        result = payload["results"][0]
        self.assertEqual(result["slug"], "domains/agent/concepts/agent-runtime")
        self.assertEqual(result["confidence"], "high")
        self.assertIn("Runtime", result["snippet"])

    def test_search_snippet_comes_from_page_body(self) -> None:
        payload = self.run_json(SEARCH, "--query", "runtime", "--limit", "1")
        snippet = payload["results"][0]["snippet"]
        self.assertIn("Runtime content", snippet)
        self.assertNotIn("title:", snippet)
        self.assertNotIn("sources:", snippet)

    def test_search_gives_partial_credit_for_chinese_phrasing_variants(self) -> None:
        self.write_page(
            "domains/agent/concepts/cjk-runtime.md",
            "# 运行时上下文\n\n智能体的运行时上下文负责注入依赖。\n",
        )
        payload = self.run_json(SEARCH, "--query", "智能体运行时", "--limit", "10")
        result = next(
            item
            for item in payload["results"]
            if item["slug"] == "domains/agent/concepts/cjk-runtime"
        )
        self.assertIn("partial", result["match_reasons"])
        self.assertIn("运行时", result["snippet"])

    def test_backlinks_include_wikilinks_that_use_page_titles(self) -> None:
        self.write_page(
            "entities/runtime-fan.md",
            "# Runtime fan\n\nSee [[Agent Runtime]].\n",
        )
        payload = self.run_json(
            PAGE,
            "domains/agent/concepts/agent-runtime",
            "--max-chars",
            "10",
            "--with-backlinks",
        )
        slugs = [item["slug"] for item in payload["backlinks"]]
        self.assertIn("entities/runtime-fan", slugs)

    def test_search_reports_total_and_truncation(self) -> None:
        payload = self.run_json(SEARCH, "--query", "runtime", "--limit", "1")
        self.assertEqual(payload["count"], 1)
        self.assertGreater(payload["total"], 1)
        self.assertTrue(payload["truncated"])

    def test_page_deduplicates_wikilinks(self) -> None:
        self.write_page(
            "domains/agent/concepts/dupes.md",
            "# Dupes\n\n[[Tool Calling]] and [[Tool Calling]] and [[Tool Calling|alias]].\n",
        )
        payload = self.run_json(PAGE, "domains/agent/concepts/dupes", "--json")
        self.assertEqual(payload["wikilinks"], ["Tool Calling"])

    def test_backlinks_report_total_when_limited(self) -> None:
        for index in range(2):
            self.write_page(
                f"entities/runtime-fan-{index}.md",
                f"# Runtime fan {index}\n\nSee [[Agent Runtime]].\n",
            )
        payload = self.run_json(
            PAGE,
            "domains/agent/concepts/agent-runtime",
            "--max-chars",
            "10",
            "--with-backlinks",
            "--backlink-limit",
            "1",
        )
        self.assertEqual(len(payload["backlinks"]), 1)
        self.assertGreaterEqual(payload["backlinks_total"], 2)
        self.assertTrue(payload["backlinks_truncated"])

    def test_page_reads_slug_and_backlinks(self) -> None:
        payload = self.run_json(
            PAGE,
            "domains/agent/concepts/tool-calling",
            "--max-chars",
            "10",
            "--with-backlinks",
        )
        self.assertEqual(payload["title"], "Tool Calling")
        self.assertEqual(payload["returned_chars"], 10)
        self.assertTrue(payload["truncated"])
        self.assertEqual(payload["backlinks"][0]["slug"], "domains/agent/concepts/agent-runtime")

    def test_raw_scope_reads_raw_source(self) -> None:
        payload = self.run_json(PAGE, "raw/runtime.md", "--scope", "raw", "--max-chars", "200")
        self.assertEqual(payload["path"], "raw/runtime.md")
        self.assertIn("source facts", payload["content"])

    def test_search_skips_binary_raw_sources(self) -> None:
        self.write_bytes("raw/source.pdf", b"%PDF-1.7\x00binary")
        payload = self.run_json(SEARCH, "--query", "runtime", "--scope", "raw")
        self.assertEqual(payload["skipped_unsupported"], 1)
        self.assertEqual(payload["results"][0]["path"], "raw/runtime.md")

    def test_page_rejects_binary_raw_source(self) -> None:
        self.write_bytes("raw/source.pdf", b"%PDF-1.7\x00binary")
        completed = subprocess.run(
            [
                sys.executable,
                str(PAGE),
                "--root",
                str(self.root),
                "raw/source.pdf",
                "--scope",
                "raw",
                "--json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["error"], "unsupported content")
        self.assertEqual(payload["path"], "raw/source.pdf")

    def test_page_reads_utf16_with_bom_and_preserves_frontmatter(self) -> None:
        content = "---\ntitle: UTF-16 Page\n---\n\n# Encoded content"
        for byte_order in ("utf-16-le", "utf-16-be"):
            bom = b"\xff\xfe" if byte_order == "utf-16-le" else b"\xfe\xff"
            relative = f"raw/{byte_order}.md"
            self.write_bytes(relative, bom + content.encode(byte_order))
            payload = self.run_json(
                PAGE, relative, "--scope", "raw", "--max-chars", "200"
            )
            self.assertEqual(payload["title"], "UTF-16 Page")
            self.assertIn("Encoded content", payload["content"])

    def test_page_reads_bomless_utf16_when_byte_order_is_unambiguous(self) -> None:
        content = "---\ntitle: ASCII Page\n---\n\n# ASCII content"
        for byte_order in ("utf-16-le", "utf-16-be"):
            relative = f"raw/bomless-{byte_order}.md"
            self.write_bytes(relative, content.encode(byte_order))
            payload = self.run_json(
                PAGE, relative, "--scope", "raw", "--max-chars", "200"
            )
            self.assertEqual(payload["title"], "ASCII Page")

    def test_page_rejects_non_utf8_binary_without_null_bytes(self) -> None:
        self.write_bytes("raw/image.png", b"\x89PNG\r\n\x1a\n")
        completed = subprocess.run(
            [
                sys.executable,
                str(PAGE),
                "--root",
                str(self.root),
                "raw/image.png",
                "--scope",
                "raw",
                "--json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["error"], "unsupported content")

    def test_custom_layout_json_controls_formal_and_raw_scopes(self) -> None:
        self.write_page("notes/concepts/runtime.md", "# Custom runtime\n\ncustom formal page")
        self.write_page("sources/runtime.txt", "custom raw source")
        self.write_page(
            "llm-wiki.json",
            json.dumps(
                {
                    "formal": ["notes/**/*.md"],
                    "raw": ["sources/**/*"],
                }
            ),
        )

        formal = self.run_json(SEARCH, "--query", "custom", "--limit", "5")
        self.assertEqual([item["path"] for item in formal["results"]], ["notes/concepts/runtime.md"])
        raw = self.run_json(SEARCH, "--query", "custom", "--scope", "raw", "--limit", "5")
        self.assertEqual([item["path"] for item in raw["results"]], ["sources/runtime.txt"])

    def test_custom_layout_page_lookup_uses_configured_scope(self) -> None:
        self.write_page("notes/concepts/runtime.md", "# Custom runtime\n\ncustom formal page")
        self.write_page(
            "llm-wiki.json",
            json.dumps({"formal": ["notes/**/*.md"], "raw": ["sources/**/*"]}),
        )
        payload = self.run_json(PAGE, "notes/concepts/runtime", "--max-chars", "100")
        self.assertEqual(payload["path"], "notes/concepts/runtime.md")

    def test_layout_rejects_patterns_that_escape_root(self) -> None:
        self.write_page("llm-wiki.json", json.dumps({"formal": ["../outside/**/*.md"]}))
        completed = subprocess.run(
            [sys.executable, str(SEARCH), "--root", str(self.root), "--query", "runtime", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("outside root", completed.stderr)

    def test_custom_layout_skips_symlinks_that_escape_root(self) -> None:
        outside = Path(self.temp.name).parent / f"outside-{self.root.name}"
        outside.mkdir()
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        (outside / "secret.md").write_text("secret", encoding="utf-8")
        (self.root / "notes").mkdir(parents=True, exist_ok=True)
        (self.root / "notes" / "outside.md").symlink_to(outside / "secret.md")
        self.write_page(
            "llm-wiki.json",
            json.dumps({"formal": ["notes/**/*.md"], "raw": []}),
        )
        payload = self.run_json(SEARCH, "--query", "secret", "--limit", "5")
        self.assertEqual(payload["count"], 0)

    def test_legacy_hidden_layout_filename_is_still_supported(self) -> None:
        self.write_page("notes/concepts/runtime.md", "# Custom runtime\n\nlegacy config")
        self.write_page(
            ".llm-wiki.json",
            json.dumps({"formal": ["notes/**/*.md"], "raw": ["sources/**/*"]}),
        )
        payload = self.run_json(SEARCH, "--query", "legacy", "--limit", "5")
        self.assertEqual(payload["results"][0]["path"], "notes/concepts/runtime.md")

    def test_validate_forwards_explicit_layout_to_native_lint(self) -> None:
        lint = self.root / "scripts" / "wiki_lint.py"
        lint.parent.mkdir(parents=True, exist_ok=True)
        lint.write_text(
            "import json, sys\nprint(json.dumps(sys.argv[1:]))\n",
            encoding="utf-8",
        )
        config = self.root / "custom-layout.json"
        config.write_text("{}", encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(VALIDATE),
                "--root",
                str(self.root),
                "--config",
                str(config),
                "--json",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(json.loads(payload["stdout"]), ["--config", str(config)])

    def test_validate_failure_emits_one_json_object_with_hint(self) -> None:
        lint = self.root / "scripts" / "wiki_lint.py"
        lint.parent.mkdir(parents=True, exist_ok=True)
        lint.write_text(
            "import sys\nprint('unrecognized arguments: --config', file=sys.stderr)\n"
            "raise SystemExit(2)\n",
            encoding="utf-8",
        )
        config = self.root / "custom-layout.json"
        config.write_text("{}", encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(VALIDATE),
                "--root",
                str(self.root),
                "--config",
                str(config),
                "--json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(len(payload["hints"]), 1)

    def test_validate_rejects_non_positive_timeout(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(VALIDATE), "--root", str(self.root), "--timeout", "0"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("--timeout must be > 0", completed.stderr)

    def test_installed_script_does_not_create_bytecode_in_skill(self) -> None:
        installed_scripts = self.root / "installed-skill" / "scripts"
        shutil.copytree(
            SKILL_DIR / "scripts",
            installed_scripts,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        self.run_json(installed_scripts / "wiki_search.py", "--query", "runtime", "--limit", "1")
        generated = [
            path
            for path in installed_scripts.rglob("*")
            if path.name == "__pycache__" or path.suffix == ".pyc"
        ]
        self.assertEqual(generated, [])

    def test_documented_script_paths_are_skill_relative(self) -> None:
        docs = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "references" / "search-and-retrieve.md",
            SKILL_DIR / "references" / "maintenance.md",
        ]
        for path in docs:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("skills/llm-wiki/scripts", text)
            self.assertIn("$SKILL_DIR/scripts", text)


class LlmWikiLayoutDocTests(unittest.TestCase):
    """The documented layout must not drift from the script constants.

    The defaults were previously restated in three places with three different
    values. The script is the source of truth; `references/layout-config.md` is
    the only document allowed to spell them out.
    """

    def script_defaults(self) -> dict[str, tuple[str, ...]]:
        # Parsed with ast rather than imported: importing would write
        # __pycache__ into the skill package, which the repo validator rejects.
        source = (SKILL_DIR / "scripts" / "_wiki_common.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        defaults: dict[str, tuple[str, ...]] = {}
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("DEFAULT_"):
                    try:
                        value = ast.literal_eval(node.value)
                    except ValueError:
                        continue
                    if isinstance(value, tuple):
                        defaults[target.id] = value
        return defaults

    def test_layout_reference_documents_every_script_default(self) -> None:
        text = (SKILL_DIR / "references" / "layout-config.md").read_text(encoding="utf-8")
        defaults = self.script_defaults()
        self.assertIn("DEFAULT_FORMAL_GLOBS", defaults)
        self.assertIn("DEFAULT_RAW_GLOBS", defaults)
        for pattern in (*defaults["DEFAULT_FORMAL_GLOBS"], *defaults["DEFAULT_RAW_GLOBS"]):
            self.assertRegex(
                text, re.escape(pattern), f"layout-config.md is missing default {pattern!r}"
            )

    def formal_globs(self) -> tuple[str, ...]:
        """Only glob-syntax patterns are checked.

        Bare filenames such as `index.md` or `SCHEMA.md` are legitimately named
        elsewhere (intent routing, governance reads); a glob can only come from
        a layout definition.
        """
        return tuple(p for p in self.script_defaults()["DEFAULT_FORMAL_GLOBS"] if "*" in p)

    def test_skill_does_not_restate_default_globs(self) -> None:
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for pattern in self.formal_globs():
            self.assertNotIn(pattern, text, f"SKILL.md restates default {pattern!r}")

    def test_search_reference_does_not_restate_formal_globs(self) -> None:
        text = (SKILL_DIR / "references" / "search-and-retrieve.md").read_text(encoding="utf-8")
        for pattern in self.formal_globs():
            self.assertNotIn(
                pattern, text, f"search-and-retrieve.md restates default {pattern!r}"
            )


if __name__ == "__main__":
    unittest.main()
