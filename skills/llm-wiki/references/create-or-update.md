# Create Or Update

Use this reference for any operation that may change wiki content or propose a wiki change.

## Required Reads

Resolve the wiki root as described in `SKILL.md`'s "Wiki Root" section, then read the current governance files from that root before proposing or applying any change to formal pages, raw sources, governance files, or generated metadata:

1. `<wiki-root>/SCHEMA.md`
2. `<wiki-root>/AGENTS.md`
3. `<wiki-root>/index.md` only for affected sections
4. `<wiki-root>/log.md` only enough to match recent entry style and avoid duplicate work

For pure retrieval, these reads are not required.

## Candidate First

Default to producing candidates for review instead of writing immediately:

- formal page create/update candidate
- `index.md` candidate
- `log.md` entry candidate
- `_meta/topic-map.md` candidate when a JD or interview source changes preparation routes

Apply changes only when the user asks for real edits or the task clearly authorizes maintenance.

## Answer Backfill

After answering from wiki content, consider backfill only when the answer produced a reusable synthesis, comparison, or workflow with sufficient sources:

1. Follow the wiki's `AGENTS.md` backfill policy when it defines one.
2. Prefer updating an existing canonical page that can carry the content.
3. Propose the target page, the content to persist, and its sources; do not write without user confirmation unless the user already asked to archive or write.
4. Skip one-off answers and any conclusion whose evidence is too weak for formal knowledge.

## Timeliness

- Do not write knowledge that is already outdated and has no continuing reference value into formal pages.
- Version evolution or deprecation that still has historical value must be marked as historical or as a counter-example following the wiki's `SCHEMA.md`, with the official replacement and the basis for that replacement.
- Verify time-sensitive claims against current sources before writing; when the wiki's `SCHEMA.md` or `AGENTS.md` defines stricter handling, follow it.

## Page Decision

Before creating a page:

1. Search existing formal pages with `wiki_search.py`.
2. Decide whether the topic will be independently recalled.
3. Update an existing page when the source only strengthens an existing concept.
4. Create a new page only for a top-level area, a concept/entity supported by multiple sources, or a query that users will ask directly.

Do not create pages for passing mentions, isolated details, or unstable ideas.

## Update Rules

- Preserve existing `[[wikilinks]]`, tags, sources, terminology, and important relationships.
- Bump `updated` on changed formal pages.
- Add new tags to `SCHEMA.md` taxonomy before using them.
- Add new, deleted, or renamed formal pages to `index.md`.
- Record formal page changes and semantic raw source changes in `log.md`.
- Keep `log.md` within the wiki retention policy.
- Do not resolve contradictions by overwriting evidence; record contested state instead.

## Raw Source Rules

`raw/` and `workshop/*/raw/` are evidence-preserving source areas. Existing raw source edits must remain traceable. Prefer adding a new version or explicit note over silent replacement when facts, conclusions, prompts, API details, or design decisions change.

Raw-only changes do not update `index.md` unless formal pages also changed.

## Source Map Closure

When a raw source changes or a formal page's `sources` field changes:

1. From the resolved wiki root, run `python3 scripts/wiki_lint.py`.
2. Review every formal page affected by a changed source digest.
3. Update affected formal pages when the evidence change makes them stale.
4. From the resolved wiki root, run `python3 scripts/generate_source_map.py`; use `--accept-reviewed` only after the required review.
5. From the resolved wiki root, run `python3 scripts/wiki_lint.py --strict` as the terminal validation.

Include the source-map update in the candidate or apply sequence when it changes `_meta/source-map.json`.
