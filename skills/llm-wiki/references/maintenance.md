# Maintenance

Use this reference for health checks, linting, index repair, broken-link checks, source-map drift, and periodic wiki cleanup.

## Required Reads

Resolve the wiki root using `SKILL.md`. Before proposing or applying maintenance changes to formal pages, raw sources, governance files, or generated metadata, read:

1. `<wiki-root>/SCHEMA.md`
2. `<wiki-root>/AGENTS.md`
3. Affected sections of `<wiki-root>/index.md`
4. Enough of `<wiki-root>/log.md` to follow retention and entry conventions

Read-only health checks (`wiki_validate.py` and `wiki_lint.py` without `--fix`) may run before these files are loaded. Do not decide or apply a repair without the required reads.

## Read-Only Checks

Run the local wrapper first:

```bash
python3 "$SKILL_DIR/scripts/wiki_validate.py" --json
```

The wrapper aborts `wiki_lint.py` after 30 seconds by default. On a large wiki it reports only
`error: timeout` with no other output. Raise the limit with `--timeout 120` before concluding the
wiki is broken; if it still times out, run `python3 scripts/wiki_lint.py` from the wiki root
directly.

The wrapper covers `wiki_lint.py` only. Also run any additional health checks the wiki's
`AGENTS.md` documents, such as pipeline, backlog, or test commands; the wrapper cannot discover
them.

For deeper read-only checks, run from the resolved wiki root:

```bash
python3 scripts/wiki_lint.py
python3 scripts/wiki_lint.py --strict
```

## Source Map Update

`generate_source_map.py` writes `_meta/source-map.json`; it is not a read-only check. Run it only after the user authorizes applying the maintenance change or approves a candidate that includes the generated metadata update.

When regeneration is authorized, close the source map from the resolved wiki root in this order:

1. Run `python3 scripts/wiki_lint.py`.
2. Review every formal page affected by a changed source digest.
3. Update affected formal pages when the evidence change makes them stale.
4. Run `python3 scripts/generate_source_map.py`; use `--accept-reviewed` only after that review.
5. Run `python3 scripts/wiki_lint.py --strict` as the terminal validation.

`create-or-update.md` states the same closure for write tasks; this reference is sufficient on its own.

## Maintenance Priorities

Check in this order:

1. Broken `[[wikilinks]]`.
2. Missing, duplicate, or stale `index.md` entries.
3. Invalid frontmatter, tags, sources, page types, confidence, or contested metadata.
4. Source-map drift for raw sources.
5. `confidence: low` pages that need evidence.
6. `contested: true` pages that may now be resolvable.
7. Orphan pages and duplicate concepts.
8. Oversized `concept` or `comparison` pages that may contain multiple independently recalled topics.

## Reporting

Report findings as root causes with the smallest safe fix. For write operations, produce candidates unless the user has authorized applying maintenance changes.
