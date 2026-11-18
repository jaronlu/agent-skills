#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

from _wiki_common import (
    UnsupportedContentError,
    WikiLayout,
    compact_page,
    dump_json,
    ensure_inside,
    iter_scope,
    page_slug,
    parse_frontmatter,
    read_text,
    rel,
    resolve_layout,
    resolve_root,
    wikilinks,
)

def resolve_page(
    root: Path, target: str, scope: str, layout: WikiLayout | None = None
) -> Path | None:
    target = target.strip()
    direct_candidates = [root / target]
    if not target.endswith(".md"):
        direct_candidates.append(root / f"{target}.md")
    for candidate in direct_candidates:
        try:
            resolved = ensure_inside(root, candidate)
        except ValueError:
            continue
        if resolved.is_file() and resolved in iter_scope(root, scope, layout):
            return resolved

    normalized = target[:-3] if target.endswith(".md") else target
    normalized = normalized.strip("/")
    for path in iter_scope(root, scope, layout):
        try:
            text = read_text(path)
        except UnsupportedContentError:
            continue
        page = compact_page(root, path, text)
        if normalized in {
            page_slug(root, path),
            rel(root, path),
            path.stem,
            str(page.get("title")),
        }:
            return path
    return None


def backlinks(
    root: Path, path: Path, text: str, *, layout: WikiLayout | None = None
) -> list[dict[str, Any]]:
    page = compact_page(root, path, text)
    names = {page_slug(root, path), rel(root, path), path.stem}
    title = page.get("title")
    if isinstance(title, str) and title:
        names.add(title)
    found: list[dict[str, Any]] = []
    for candidate in iter_scope(root, "formal", layout):
        if candidate == path:
            continue
        try:
            candidate_text = read_text(candidate)
        except (UnsupportedContentError, OSError):
            continue
        if names.intersection(wikilinks(candidate_text)):
            found.append(compact_page(root, candidate, candidate_text))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read one ~/llm-wiki page by slug or path."
    )
    parser.add_argument("target", help="Slug or path, with or without .md.")
    parser.add_argument(
        "--root", help="Wiki root. Defaults to $LLM_WIKI_ROOT or ~/llm-wiki."
    )
    parser.add_argument(
        "--config",
        help="Layout JSON path. Defaults to <root>/llm-wiki.json when present.",
    )
    parser.add_argument("--scope", choices=("formal", "raw", "all"), default="formal")
    parser.add_argument("--max-chars", type=int, default=12000)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--with-backlinks", action="store_true")
    parser.add_argument("--backlink-limit", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.backlink_limit < 0:
        parser.error("--backlink-limit must be >= 0")

    root = resolve_root(args.root)
    if not root.is_dir():
        print(f"wiki root not found: {root}", file=sys.stderr)
        return 2

    try:
        layout = resolve_layout(root, args.config)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        path = resolve_page(root, args.target, args.scope, layout)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if path is None:
        payload = {
            "error": "page not found",
            "target": args.target,
            "scope": args.scope,
            "root": str(root),
            "config": str(layout.path) if layout.path else None,
        }
        if args.json:
            dump_json(payload)
        else:
            print(payload["error"], file=sys.stderr)
        return 2

    try:
        text = read_text(path)
    except UnsupportedContentError as exc:
        payload = {
            "error": "unsupported content",
            "details": str(exc),
            "path": rel(root, path),
            "scope": args.scope,
            "root": str(root),
            "config": str(layout.path) if layout.path else None,
        }
        if args.json:
            dump_json(payload)
        else:
            print(payload["error"], file=sys.stderr)
        return 2
    frontmatter, body = parse_frontmatter(text)
    offset = max(0, args.offset)
    max_chars = max(0, args.max_chars)
    content = body[offset : offset + max_chars] if max_chars else ""
    payload: dict[str, Any] = compact_page(root, path, text)
    payload.update({
        "root": str(root),
        "config": str(layout.path) if layout.path else None,
        "frontmatter": frontmatter,
        "wikilinks": wikilinks(body),
        "total_chars": len(body),
        "offset": offset,
        "returned_chars": len(content),
        "truncated": offset + len(content) < len(body),
        "content": content,
    })
    if args.with_backlinks:
        all_backlinks = backlinks(root, path, text, layout=layout)
        payload["backlinks"] = all_backlinks[: args.backlink_limit]
        payload["backlinks_total"] = len(all_backlinks)
        payload["backlinks_truncated"] = len(all_backlinks) > args.backlink_limit

    if args.json:
        dump_json(payload)
    else:
        print(f"# {payload['title']}\n")
        print(content)
        if payload["truncated"]:
            print("\n[truncated]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
