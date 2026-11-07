# Knowledge Maintenance

Read this file before executing Phase 8 (knowledge maintenance) in SKILL.md, or whenever an existing knowledge book must be updated after source changes.

## Phase 8 — Knowledge maintenance

Run order: `openwiki_begin(mode: "update")` → impact analysis below → `openwiki_submit_plan` for the affected pages and required deletions → Phase 6/7 page loop → `openwiki_finish`.

When source code changes:

1. Identify changed files and symbols from the changed paths `openwiki_begin` reports, and note `claimIssuePages` as pages that already need Claim attention. When `changedPathsTruncated` is set, complete the list with `git diff --name-only <baseGitHead>..HEAD` (not on a `fullReview` window), `git diff --name-only HEAD`, and `git ls-files --others --exclude-standard`, leaving out `openwiki/` and `.openwikiignore` paths.
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
6. Submit a plan for the affected pages. When pages are added, deleted, moved, or materially regrouped, also plan `openwiki/quickstart.md` so its routing map stays correct; never delete `quickstart.md`. Put page deletions in the plan's `deletePages` and remove inbound links to the deleted pages. If impact analysis finds no page edits or deletions, submit `pages: []` and proceed to `openwiki_finish`; do not invent pages to fill the plan.
7. Update affected content when the Phase 7 checks can verify the new behavior.
8. Revalidate updated references, diagrams, and execution flows with the Phase 7 checks. When a mechanism changes, update the diagram asset under `openwiki/assets/` in place and keep the page reference pointing at the same file only when every page linking it needs the change. If only one page's diagram changes, write a new asset, retarget that page, and delete the old asset when no other page links it. Do not leave an outdated asset behind or inline a replacement into the page.

Rules:

- Treat the summary page as affected whenever a chapter it summarizes changes its system model, a core mechanism, a key call chain, or the running example. Update it in the same run and restate the affected chapter's Claims with that chapter's evidence. When chapters are added or removed, revisit its mechanism list and step sequence.
- Treat the overview as affected when the project purpose, boundaries, or component map changes.
- Treat the glossary as affected when a term is added, removed, or redefined.
- Treat the quickstart as affected when pages are added, removed, or moved, or when any route it names changes.
- Treat the open-questions page as affected when a listed question is resolved by the change, or when the change creates a new unverified area.
- Do not regenerate the entire book when the changed files map to only the chapters that cite them. Regenerate everything only when a changed concept is a conceptual prerequisite of most chapters.
- Do not leave orphaned assets. When a page or section is removed, or an item is classified Invalidated, delete the SVG assets that only it referenced and remove the links to them. Keep an asset that another page still links.
- Resolve every `stale` or `unresolved` Claim deliberately: confirm it with `confirmedClaimIds` after rechecking, revise it under the same `id` in `claims`, or retract it with `retractedClaimIds`. Never retract a Claim merely because it is stale.
- Use `deferUnplannedClaimIssues` only for a deliberately focused update. Disclose that the completed run stays interrupted until the deferred Claim debt is reconciled; never use it on `init`.
- Do not claim incremental consistency unless the relevant dependencies have been checked.
- Use OpenWiki claim evidence as the source-to-chapter mapping and the reported claim states (`stale`, `unresolved`) as the impact signal; do not maintain a parallel mapping. If a chapter has no claim covering the changed path, treat that as an evidence gap, disclose it, and fall back to searching the chapter text for the changed paths and symbols.
