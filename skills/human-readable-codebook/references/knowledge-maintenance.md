# Knowledge Maintenance

Read this file before executing Phase 8 (knowledge maintenance) in SKILL.md, or whenever an existing knowledge book must be updated after source changes.

## Phase 8 — Knowledge maintenance

When source code changes:

1. Identify changed files and symbols, for example from `git diff --name-only` and the changed hunks.
2. Identify chapters referencing them, using OpenWiki claim evidence as the mapping.
3. Identify affected concepts and execution scenarios. A concept is affected when a changed symbol appears in its evidence. A scenario is affected when a changed symbol appears in one of its traced steps.
4. Identify downstream knowledge dependencies, using the conceptual dependencies from Phase 4.
5. Classify each affected item as:
   - Unaffected
   - Needs review
   - Requires update
   - Invalidated

   Use these criteria:
   - Unaffected: the item cites no changed file or symbol, and its dependencies did not change.
   - Needs review: the item cites a changed file, but the changed lines do not alter any name, condition, sequence, or data shape the item describes.
   - Requires update: the described behavior, sequence, or data flow changed, and the new behavior can be verified.
   - Invalidated: the described mechanism no longer exists, or its replacement cannot be verified.
6. Update affected content when the Phase 7 checks can verify the new behavior.
7. Revalidate updated references, diagrams, and execution flows with the Phase 7 checks.

Rules:

- Treat the summary page as affected whenever a chapter it summarizes changes its system model, a core mechanism, a key call chain, or the running example. Update it in the same run and reuse the affected chapter's Claim evidence. When chapters are added or removed, revisit its mechanism list and step sequence.
- Do not regenerate the entire book when the changed files map to only the chapters that cite them. Regenerate everything only when a changed concept is a conceptual prerequisite of most chapters.
- Do not claim incremental consistency unless the relevant dependencies have been checked.
- Use OpenWiki claim evidence as the source-to-chapter mapping and the reported claim states (`stale`, `unresolved`) as the impact signal; do not maintain a parallel mapping. If a chapter has no claim covering the changed path, treat that as an evidence gap, disclose it, and fall back to searching the chapter text for the changed paths and symbols.
