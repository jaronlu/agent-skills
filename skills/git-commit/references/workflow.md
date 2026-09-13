# Commit Workflow

Read whenever a message must be written from a diff, in either mode, and always in commit mode. The contract, evidence rule, scope decision, safety boundary, question policy, and output contract stay in `SKILL.md`; this file only sequences the work.

## 1. Gather evidence

1. Read `git status --short`, then apply the commit scope decision from `SKILL.md`. Do not re-derive it from file counts.
2. Inspect the selected scope: start with `git diff --cached --stat` and `git diff --cached`, then the relevant working-tree diff and untracked paths when the selected scope includes them.
3. When the staged diff is empty and a message is still needed:
   - Inspect `git diff --stat` and `git diff` for unstaged tracked changes.
   - Identify untracked paths from `git status --short`. For relevant, safe-to-read text files, inspect names and contents; summarize directories or binary files without attempting to read them.
   - State in the response that the message is based on unstaged and/or untracked changes.
4. In commit mode this empty-index branch applies only when the selected scope is staged-only; when the scope includes unstaged or untracked changes, continue with them instead of stopping.
5. Stop when no relevant changes exist.

Porcelain columns, including the shapes that are easiest to misread:

- ` M file` — unstaged only
- `M  file` — staged only
- `MM file` — both staged and unstaged
- `A  file` — staged new file
- `AM file` — staged new file, edited again afterwards
- ` D file` — deleted in the worktree, not staged
- `D  file` — deletion staged
- `R  old -> new` — rename staged
- `?? file` — untracked only

Read the two columns literally before reaching for any of these; they are illustrations, not a closed list.

## 2. Discover repository rules

Use low-output discovery before writing any message:

- Find dedicated rule sources with `git ls-files`: commitlint config, hooks, `lefthook`, `.gitmessage`, and explicit commit or release configuration.
- Also check paths that `git status --short` reports as untracked, so a rule file that has not been added yet is not missed.
- Search broad tracked candidates such as `package.json`, `.github/**`, contribution guides, `AGENTS.md`, and development guides for commit-related keywords before treating them as candidates.
- Check `.git/hooks/commit-msg` separately when it exists.
- When the working directory sits inside a larger repository, check the parent directories for the same rule sources.
- Read [repository-rules.md](repository-rules.md) only when a dedicated source exists or a broad candidate contains a commit-related match.

## 3. Screen the selected changes

Check for conflict markers, sensitive data, generated noise, binary-only changes, unrelated intents, and breaking behavior. When a selected change is clearly unsuitable, pause and ask before touching the index, naming the path and reason. The safety boundary in `SKILL.md` applies here without restatement.

## 4. Partition and draft

1. Partition the selected changes by primary intent before writing messages. Each atomic group must be independently understandable and must not mix unrelated fixes, features, documentation, tests, or housekeeping. A single logical change may span multiple files; do not split such a change merely by file.
2. Derive one message per atomic group from that group's diff. Do not invent changes or scopes, and do not reuse a scope from the repository's history when no path in the group touches that module.
3. Apply the message contract, then compatible repository rules and explicit user instructions. Read [default-rules.md](default-rules.md) for type, scope, subject, or body decisions left open.
4. If the selected changes cannot be partitioned into coherent atomic groups, ask how to handle the conflicting groups instead of producing a mixed fallback message. When a group boundary is clear, create separate atomic commits; ask only when the correct treatment is materially uncertain.
5. In message mode, return the best message directly, or one message per clearly separable group when the evidence contains multiple intents.
6. In commit mode, read [commit-execution.md](commit-execution.md), stage only the selected changes as needed, create the atomic commits non-interactively, and verify every result.
