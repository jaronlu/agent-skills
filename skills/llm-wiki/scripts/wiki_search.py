#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from typing import Any

sys.dont_write_bytecode = True

from _wiki_common import cjk_bigrams, tokens, wikilinks

def score_page(
    page: dict[str, Any],
    text: str,
    query: str,
    *,
    tag: str | None,
    page_type: str | None,
    source: str | None,
) -> tuple[int, list[str]]:
    reasons: list[str] = []
    score = 0
    title = str(page.get("title") or "")
    path = str(page["path"])
    slug = str(page["slug"])
    raw_tags = page.get("tags")
    tags: list[str] = (
        [item for item in raw_tags if isinstance(item, str)]
        if isinstance(raw_tags, list)
        else []
    )
    raw_sources = page.get("sources")
    sources: list[str] = (
        [item for item in raw_sources if isinstance(item, str)]
        if isinstance(raw_sources, list)
        else []
    )

    if tag and tag not in tags:
        return 0, []
    if page_type and page.get("type") != page_type:
        return 0, []
    if source and not any(source in item for item in sources) and source not in path:
        return 0, []

    normalized_query = query.strip().lower()
    haystack = f"{title}\n{path}\n{slug}\n{' '.join(tags)}\n{text}".lower()
    if normalized_query:
        if normalized_query in {
            title.lower(),
            slug.lower(),
            path.lower(),
            f"{slug}.md".lower(),
        }:
            score += 100
            reasons.append("exact")
        if normalized_query in title.lower():
            score += 35
            reasons.append("title")
        if normalized_query in slug.lower() or normalized_query in path.lower():
            score += 25
            reasons.append("path")
        links = " ".join(wikilinks(text)).lower()
        if normalized_query in links:
            score += 20
            reasons.append("wikilink")
        token_hit = False
        for token in tokens(normalized_query):
            if token in title.lower():
                score += 8
            if token in slug.lower():
                score += 6
            occurrences = len(re.findall(re.escape(token), haystack))
            if occurrences:
                token_hit = True
                score += min(occurrences, 12)
        if token_hit:
            # A full token match is stronger evidence than bigram overlap, so
            # keep it above any partial score.
            score += 10
            reasons.append("token")
        if score == 0:
            # CJK queries are one token, so a reworded phrase misses every full
            # token. Shared two-character bigrams still surface related pages
            # with a small score and an explicit partial reason.
            partial = [item for item in cjk_bigrams(normalized_query) if item in haystack]
            if not partial:
                return 0, []
            score += min(len(partial), 6)
            reasons.append("partial")
    elif tag or page_type or source:
        score = 1
        reasons.append("filter")
    else:
        score = 1
        reasons.append("list")

    if tag:
        score += 15
        reasons.append("tag")
    if page_type:
        score += 10
        reasons.append("type")
    if source:
        score += 15
        reasons.append("source")
    return score, sorted(set(reasons))


def main() -> int:
    from _wiki_common import (
        UnsupportedContentError,
        compact_page,
        dump_json,
        iter_scope,
        parse_frontmatter,
        read_text,
        resolve_layout,
        resolve_root,
        snippet,
    )

    parser = argparse.ArgumentParser(
        description="Search ~/llm-wiki with compact metadata output."
    )
    parser.add_argument(
        "--query",
        "-q",
        default="",
        help="Text, slug, title, tag, or concept to search for.",
    )
    parser.add_argument(
        "--root", help="Wiki root. Defaults to $LLM_WIKI_ROOT or ~/llm-wiki."
    )
    parser.add_argument(
        "--config",
        help="Layout JSON path. Defaults to <root>/llm-wiki.json when present.",
    )
    parser.add_argument("--scope", choices=("formal", "raw", "all"), default="formal")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--tag", help="Filter by tag. When combined with --type or --source, all filters must match (AND).")
    parser.add_argument("--type", dest="page_type", help="Filter by page type (AND when combined with other filters).")
    parser.add_argument(
        "--source",
        help="Filter formal pages by frontmatter source path, or raw paths by path.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be >= 0")

    root = resolve_root(args.root)
    if not root.is_dir():
        print(f"wiki root not found: {root}", file=sys.stderr)
        return 2

    try:
        layout = resolve_layout(root, args.config)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    results: list[dict[str, Any]] = []
    skipped_unsupported = 0
    try:
        paths = iter_scope(root, args.scope, layout)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    for path in paths:
        try:
            text = read_text(path)
        except UnsupportedContentError:
            skipped_unsupported += 1
            continue
        except OSError:
            continue
        page = compact_page(root, path, text)
        _, body = parse_frontmatter(text)
        score, reasons = score_page(
            page,
            text,
            args.query,
            tag=args.tag,
            page_type=args.page_type,
            source=args.source,
        )
        if not score:
            continue
        page.update({
            "score": score,
            "match_reasons": reasons,
            "snippet": snippet(body or text, args.query),
        })
        results.append(page)

    results.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    page_results = results[: args.limit]
    payload = {
        "root": str(root),
        "config": str(layout.path) if layout.path else None,
        "scope": args.scope,
        "query": args.query,
        "count": len(page_results),
        "total": len(results),
        "truncated": len(results) > len(page_results),
        "skipped_unsupported": skipped_unsupported,
        "results": page_results,
    }
    if args.json:
        dump_json(payload)
    else:
        for result in payload["results"]:
            print(f"{result['score']:>3} {result['path']} :: {result['title']}")
            if result.get("snippet"):
                print(f"    {result['snippet']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
