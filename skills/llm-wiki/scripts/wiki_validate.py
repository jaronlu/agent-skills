#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Any

sys.dont_write_bytecode = True

def main() -> int:
    from _wiki_common import dump_json, resolve_root

    parser = argparse.ArgumentParser(
        description="Run wiki-native lint with compact structured output."
    )
    parser.add_argument(
        "--root", help="Wiki root. Defaults to $LLM_WIKI_ROOT or ~/llm-wiki."
    )
    parser.add_argument(
        "--config",
        help="Layout JSON path. Defaults to <root>/llm-wiki.json when present.",
    )
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be > 0")

    root = resolve_root(args.root)
    lint = root / "scripts" / "wiki_lint.py"
    if not lint.is_file():
        missing_payload = {
            "ok": False,
            "error": "wiki_lint.py not found",
            "root": str(root),
        }
        if args.json:
            dump_json(missing_payload)
        else:
            print(missing_payload["error"], file=sys.stderr)
        return 2

    command = [sys.executable, str(lint)]
    if args.strict:
        command.append("--strict")
    if args.config:
        command.extend(("--config", args.config))
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            timeout=args.timeout,
            check=False,
        )
        payload: dict[str, Any] = {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "root": str(root),
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except subprocess.TimeoutExpired as exc:
        payload = {
            "ok": False,
            "error": "timeout",
            "timeout": args.timeout,
            "root": str(root),
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
        }
    except OSError as exc:
        payload = {
            "ok": False,
            "error": "unable to run wiki_lint.py",
            "details": str(exc),
            "root": str(root),
        }

    if not payload["ok"] and args.config and payload.get("stderr"):
        hint = (
            "note: the wiki's wiki_lint.py may not support --config;"
            " upgrade wiki scripts or remove the layout configuration"
        )
        if args.json:
            hints = payload.get("hints")
            if not isinstance(hints, list):
                hints = []
            hints.append(hint)
            payload["hints"] = hints
        else:
            print(hint, file=sys.stderr)
    if args.json:
        dump_json(payload)
    else:
        print(payload.get("stdout") or payload.get("error") or "")
        if payload.get("stderr"):
            print(payload["stderr"], file=sys.stderr)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
