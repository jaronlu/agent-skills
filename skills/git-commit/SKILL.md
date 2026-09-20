---
name: git-commit
description: Draft repository-aware Conventional Commit messages or create atomic Git commits from staged or selected working-tree changes.
---

# Git Commit

## Contract

Subject: `type(scope): subject`. Types: `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `style`, `chore`. Scope is required and must name a module, package, or area that already exists; never invent one. One intent across modules: join with `&`, then one `- scope: desc` line per scope:

```text
feat(common&share&tool): add shared retry
- common: add retry helper
- share: route calls through it
- tool: drop local retry
```

No owner: `type: subject`. Imperative, no trailing period, ≤50 when practical. Body only for why or impact. Mark every confirmed breaking change with `!` before `:` or a `BREAKING CHANGE:` footer; either form is valid, and both may be used. One commit, one intent. If the per-scope lines describe independent changes, split them into separate commits. If no intent dominates, split. Default to English. Switch only if the user writes in another language. Use one language for every message in a run, and never mix languages inside a subject, inside a body, or between the commits of one run. Leave identifiers, file names, API names, and type names untranslated. No `Co-Authored-By:`, `Signed-off-by:`, or AI attribution unless required. Discover enforceable commit rules before writing any message, in both modes. Check commitlint, hooks, and commit policy, including untracked. If an enforceable repository rule requires an incompatible message format, stop and report the conflict. Do not silently fall back or use history.

## Modes

**Message mode**: draft a message without changing Git state; use only the staged diff as message evidence; leave unstaged and untracked changes out. If staged is empty, use unstaged/untracked.

**Commit mode**: create one or more atomic commits.

Before touching the index, read `git status --short` porcelain. `X` is the index/staged state and `Y` is the working-tree/unstaged state; the `?` in `??` means untracked, not staged. Do not infer staging boundaries from the number of edited files.

Ask exactly one A/B question only when at least one path has an actual staged/index status and at least one path has an actual unstaged/worktree status or is untracked: **A** staged only; **B** all changes, atomic. If no path is staged and other changes exist, select all automatically; do not ask A/B for multiple unstaged files. If something is staged and nothing else changed, select staged.

## Safety

Never stage changes outside the selected scope. **B** or auto-all authorizes staging in-scope untracked files. Never include unrelated user changes. When a file mixes unrelated intents, pause and ask. Never expose secret values; never commit suspected secret content. Do not create or switch branches, push, amend, rebase, bypass hooks, or change signing unless explicitly requested. Do not amend, bypass hooks, disable signing, or use `--no-verify`. Stop if `MERGE_HEAD`, `REBASE_HEAD`, `CHERRY_PICK_HEAD` is present. Quote every `-m` argument.

## Commit

Record that group's staged path set. Commit non-interactively. Read the committed path set. Confirm committed paths match the recorded staged set. Report hash and subject.
