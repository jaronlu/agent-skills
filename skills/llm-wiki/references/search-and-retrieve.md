# Search And Retrieve

Use this reference for read-only lookup and wiki-backed answers.

## Workflow

If the wiki's `AGENTS.md` or `README.md` documents an entry route (for example index-first), follow it; use the script to search within or after that route.

1. Search with the script before opening files:

   ```bash
   python3 "$SKILL_DIR/scripts/wiki_search.py" --query "<query>" --scope formal --limit 8 --json
   ```

2. Prefer results in this order:
   - exact slug or title
   - wiki index catalog match
   - tag or type match
   - wikilink inbound/outbound match
   - full-text match
3. Read only the smallest sufficient pages:

   ```bash
   python3 "$SKILL_DIR/scripts/wiki_page.py" "<slug-or-path>" --max-chars 12000 --json
   ```

4. Expand through backlinks or outbound links only when the current page is insufficient.
5. Stop searching once there is enough evidence to answer the user's question.

## Scope

- `--scope formal`: search formal wiki pages only. Use for most answers.
- `--scope raw`: search raw evidence only. Use when formal pages are missing or the user asks for source material.
- `--scope all`: search formal and raw areas. Use sparingly; ranking does not guarantee that formal results precede raw results.

By default, formal pages are the built-in globs listed in [layout-config.md](layout-config.md); a custom `llm-wiki.json` replaces them with its own `formal` globs. Do not restate the default list here.

Raw scope covers UTF-8 text files under the configured raw globs, `raw/**/*` and `workshop/*/raw/**/*` by default. Raw and formal are disjoint. Binary files such as PDF, XLSX, and XMind are excluded from search; direct reads return an unsupported-content error and require a file-specific tool.

Search JSON reports the number of excluded files in `skipped_unsupported`.

## Retrieval Discipline

- Do not open the wiki change log for normal answers unless recency or maintenance history matters.
- Do not read the wiki schema file for simple retrieval; scripts expose enough metadata for lookup.
- When formal evidence should take priority, search `--scope formal` first and fall back to `--scope raw`; do not depend on `--scope all` ordering.
- Keep result limits small, then rerun with a narrower query if needed.
- `count` is the number of results returned after `--limit`; `total` is the number of matches. When `truncated` is true, rerun with a larger limit or a narrower query.
- If `wiki_page.py` reports `truncated: true`, continue the page with `--offset` set to the previous `offset + returned_chars`.
- `--with-backlinks` reports `backlinks_total`; `backlinks` is capped by `--backlink-limit`, and `backlinks_truncated` marks the cap.
- Chinese text has no whitespace word boundaries, so a query matches the exact contiguous phrase.
  Pages sharing only two-character bigrams with the query surface with `match_reasons: ["partial"]`
  and a low score; treat those as leads, not matches.
- If script results are ambiguous, use titles, tags, type, confidence, and snippets to choose the next page.

## Answer Shape

Answer from the retrieved pages first. Preserve important terms and `[[wikilinks]]` when they carry relationship meaning. Mention source page slugs when useful for traceability.

Search snippets come from the page body; frontmatter metadata is returned separately in the result object.
