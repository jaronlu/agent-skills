---
name: git-commit
description: Draft repository-aware Conventional Commit messages or create atomic Git commits from staged or selected working-tree changes.
---

# Git Commit

Generate an accurate Conventional Commits message from the actual diff. Create the commit when the user asks to commit; otherwise return the message only.

## Message Contract

- Every generated subject MUST use `type(scope): subject`.
- Type is required. Choose the smallest accurate one: `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `style`, `chore`. [default-rules.md](references/default-rules.md) defines each one.
- Scope is required and must name a module, package, or area that already exists in the repository; never invent one.
  - One intent across several modules: join the real scopes with `&`, e.g. `feat(common&share&tool): add shared retry policy`.
  - A repository-wide change owned by no module is the only exemption: fall back to `type: subject`.
- Subject: English imperative, no trailing period, ≤50 characters when practical.
- Body: add one only when the why, impact, migration, or caveat matters, wrapped at about 72 characters. For a joined scope, give one line per scope.
- Mark every confirmed breaking change with `!` before `:` or a `BREAKING CHANGE:` footer; either form is valid, and both may be used.
- One commit carries one intent. Tests and docs for that intent belong in the same commit; never mix in unrelated fixes, features, or housekeeping. A joined scope is not a permit to combine intents: if the per-scope lines describe independent changes, split them into separate commits.
- Use one language for every message in a run, and never mix languages inside a subject, inside a body, or between the commits of one run. Leave identifiers, file names, API names, and type names untranslated.
- Do not add `Co-Authored-By:`, `Signed-off-by:`, or AI attribution unless the user or repository requires it. If a tool appends one, remove it before committing.
- Let enforceable repository rules refine allowed types, scopes, ticket identifiers, length, casing, and trailers.
- If an enforceable repository rule requires an incompatible message format, stop and report the conflict. Do not silently fall back to a non-Conventional subject.

## Operation Modes

- **Message mode**: draft a message without changing Git state.
- **Commit mode**: create one or more atomic commits from the selected working-tree changes and verify them. Atomicity is mandatory for every scope choice, including A, B, and automatic all-change selection.

## Commit Scope Decision

Mandatory in commit mode, before the index is touched; message mode skips it.

Start from `git status --short` and interpret its two porcelain columns literally: `X` is the index/staged state and `Y` is the working-tree/unstaged state; the `?` in `??` means untracked, not staged. Do not infer staging boundaries from the number of edited files, an app's edit card, or `git diff --stat` alone.

- Ask exactly one A/B question only when at least one path has an actual staged/index status and at least one path has an actual unstaged/worktree status or is untracked. A second edited file alone is not evidence of both scopes:
  - **A. Only commit staged changes** — leave all unstaged and untracked changes untouched.
  - **B. Commit all changes** — include staged, unstaged, and untracked changes, grouping them into atomic commits.
- If no path is actually staged and tracked or untracked changes exist, select all of them automatically and keep the commits atomic. Do not stop merely because the index is empty, and do not ask A/B for multiple unstaged files.
- If something is actually staged and nothing else changed, select the staged changes.

## Message Evidence

- In message mode, use only the staged diff as message evidence; leave unstaged and untracked changes out of the message.
- When the staged diff is empty, follow [references/workflow.md](references/workflow.md) for the unstaged and untracked fallback.
- Stop when no relevant changes exist.

## Decision Priority

1. The mandatory message contract above
2. Compatible enforceable repository rules
3. Compatible explicit user instructions
4. Default type, scope, subject, and body rules

Do not use repository history to choose the message format.

## References

Read each one only when its trigger applies; each stands alone, and none of them restates this contract.

| Read | When |
| --- | --- |
| [references/workflow.md](references/workflow.md) | Commit mode, or message mode whose staged diff is empty |
| [references/default-rules.md](references/default-rules.md) | The contract leaves a type, scope, subject, or body decision open |
| [references/repository-rules.md](references/repository-rules.md) | Repository rule discovery found a commitlint config, hook, or commit-related policy |
| [references/commit-execution.md](references/commit-execution.md) | Commit mode, before staging or creating any commit |

## Question Policy

Default to one-shot execution or output. Besides the mandatory scope question above, ask before committing only when a selected change is clearly unsuitable or its atomic-group treatment is materially uncertain. Otherwise ask only when the answer would materially change the type, required scope, or breaking-change status.

## Safety Boundary

- Never stage changes outside the selected scope. In commit mode, selecting **B** or automatically selecting all changes when the index is empty authorizes staging those in-scope changes, including untracked files, as needed to create atomic commits.
- Atomicity is mandatory even when the selected scope contains one file or was already staged: do not combine unrelated intents into one commit.
- When splitting into multiple commits, leave each not-yet-committed in-scope group in the working tree or index and preserve all out-of-scope changes exactly.
- Never include unrelated user changes to make a commit look complete.
- Never expose secret values while reporting a sensitive-data finding.
- For unresolved conflicts or other clearly unsuitable changes, pause and ask whether to exclude the change, handle it separately, or stop. For suspected secrets, ask only whether to exclude them, remediate and re-inspect them, or stop; never commit suspected secret content, even in a separate commit. Do not proceed until the user decides; do not reveal secret values.
- Do not create or switch branches, push, amend, rebase, bypass hooks, or change signing behavior unless the user explicitly requests that separate operation.

## Output

- Message mode: return one best subject per atomic group; when there are multiple groups, return one clearly labeled message per group. All returned messages share one language. Add a body only when the why, impact, migration, or caveat matters.
- Commit mode: report every created commit's short hash and subject after verification, then report the final status and preserved changes.
- If blocked: state the exact blocker, ask how it should be handled, and do not commit until the decision is clear.
- If a split is needed: identify the atomic groups and their messages before committing them.
