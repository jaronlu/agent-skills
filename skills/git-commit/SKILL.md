---
name: git-commit
description: Draft repository-aware Conventional Commit messages or create atomic Git commits from staged or selected working-tree changes.
---

# Git Commit

## Message format

Subject: `type(scope): subject`. Types: `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `style`, `chore`.

- Scope is required when the repo has a module, package, or area for the change. It must match an existing name: a top-level directory, or a name in a package manifest (`package.json` `name`, `go.mod` module path last segment, `Cargo.toml` `[package] name`). If no existing name fits, stop and report; never invent one.
- Imperative mood, no trailing period, 50 characters or fewer when practical.
- Body only for why or impact, except the `&` form: its body always lists one `- scope: desc` line per scope, in the same order as the `&` list.
- Breaking change: `!` before `:` or a `BREAKING CHANGE:` footer.
- Default language is English. Switch only if the user writes in another language, and use one language for the whole run.
- Leave identifiers, file names, API names, and type names untranslated.
- No `Co-Authored-By:`, `Signed-off-by:`, or AI attribution unless required. User instructions (CLAUDE.md, the user's own message) and runtime attribution rules take precedence over this default. If they conflict, say so in the report.

## One intent across scopes

Use the `&` form only when the change is one intent that cannot be reverted per scope:

- one intent: a caller and its implementation change together, or a shared interface and all of its consumers
- independent: each scope's change works and can be reverted alone

```text
feat(common&share&tool): add shared retry
- common: add retry helper
- share: route calls through it
- tool: drop local retry
```

If the scopes are independent, make one commit per scope. Identical text in two packages is not a reason to join them; judge by dependency.

## Discover commit rules first

Before writing any message, in both modes, check for enforceable rules:

- `commitlint.config.*`, `.commitlintrc*`, or a `commitlint` key in `package.json`
- `.husky/`, `lefthook.yml`, `.pre-commit-config.yaml`, `.gitlint`, `.githooks/`, `core.hooksPath`
- `CONTRIBUTING.md` and `.github/` commit guidance

If commitlint is configured and installed locally, validate the draft with `npx --no-install commitlint --edit <msg-file>`. Do not install packages to run it. If a rule forbids the required format (for example, a scope-enum that excludes `&`, or a rule against splitting), stop and report the rule and the conflict. Do not silently change the format.

## Modes

**Message mode**: draft a message without changing Git state. Use only the staged diff as evidence. If nothing is staged, use unstaged and untracked changes as evidence, and say which set was used.

**Commit mode**: create one or more atomic commits.

Read `git status --porcelain=v1` before touching the index. `X` is the staged state, `Y` is the unstaged state, and `??` means untracked.

Selection:

- Only staged paths: commit them (option A is automatic).
- Nothing staged, only unstaged or untracked: select all in-scope changes automatically.
- Staged and also unstaged or untracked: ask exactly one A/B question.

A/B question:

- **A**: staged only.
- **B**: all in-scope changes, atomic.

In B, untracked files are included only when they sit inside an existing scope directory and do not look like scratch or secrets (names such as `notes*`, `*.txt` drafts, `*.log`, `*.tmp`, `.env*`, `*secret*`). The question must list every path that B would add, and every path B would leave out, so the user can choose. Never stage an untracked file that matches those patterns without an explicit user choice.

## Safety

- Never stage changes outside the selected scope.
- Never include unrelated user changes. If one file mixes unrelated intents, pause and ask.
- Never expose secret values. Never commit suspected secret content.
- Commit on the current branch by default, even when it is the default branch. Do not create or switch branches unless the user explicitly asks.
- Do not push, amend, rebase, bypass hooks, use `--no-verify`, or change signing unless the user explicitly asks.
- Quote every `-m` argument.

## Stop conditions

| Condition | Action | Report |
| --- | --- | --- |
| `MERGE_HEAD`, `REBASE_HEAD`, or `CHERRY_PICK_HEAD` exists | Stop, change nothing | Which state is in progress and that the user must finish or abort it |
| Suspected secret in the selected set | Stop, do not commit | File path and key name only, never the value |
| Mixed unrelated intents in one file | Stop, ask | The file and the two intents |
| Enforceable rule conflicts with the format | Stop | The rule file, the rule, and the conflicting format |
| No existing scope matches | Stop | The candidate names checked |
| Hook or commitlint rejects the message | Stop, do not bypass | The hook output, first failing rule |

## Commit

1. Record the staged path set for the group: `git diff --cached --name-only -z`.
2. Commit non-interactively: `git commit -m "<subject>" -m "<body>"`. For the `&` form, always pass the body; otherwise pass it only when the body rule requires it.
3. Read the committed paths: `git show --name-only --format= HEAD -z`.
4. Confirm they match the recorded set. If they differ, report the mismatch and stop before the next group.
5. Report the hash and subject.
