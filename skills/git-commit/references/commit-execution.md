# Commit Execution

Read this file only in commit mode.

## Scope and atomicity

Before changing the index:

1. Use the scope selected by the main skill, read from Git's porcelain `XY` columns as `SKILL.md` defines them and never from an edit summary. **A** means staged-only; **B** means staged, unstaged, and untracked changes; an empty index with other changes means all changes.
2. Record the baseline with `git status --short`, `git diff --cached --name-status`, `git diff --name-status`, and the untracked path list.
3. Partition the selected diff into logical groups. Keep one logical change together across files and use separate commits for unrelated intents; the contract in `SKILL.md` decides when a joined scope counts as a single group. Atomicity applies to every selected scope, including staged-only A and all-change B.
4. For each group, stage only that group's paths or hunks; never use a blanket staging command that pulls in out-of-scope changes. Path-level staging covers most groups.
5. When a file holds more than one group, or the index already holds more than the next group, use patch-based index operations instead of an interactive picker: `git diff -- <path> | git apply --cached` stages one group, and `git apply --cached --reverse` on the same patch unstages it. `git add -p` and `git reset -p` block a non-interactive run and are not a substitute. `git reset -- <path>` unstages a whole path when the group boundary is the file itself. Do not use commands that discard working-tree content.

## Preconditions

1. Confirm the working directory is inside a Git repository, and that no other Git operation is in progress: no `MERGE_HEAD`, `REBASE_HEAD`, `CHERRY_PICK_HEAD`, `REVERT_HEAD`, or `BISECT_LOG`. A commit during a merge, rebase, or cherry-pick ends an operation the user did not ask to finish, so stop and report instead. An unborn `HEAD` is valid; the first commit simply has no parent to compare against.
2. Confirm that the current index contains exactly the next atomic group.
3. Record that group's staged path set with `git diff --cached --name-only` and confirm it matches the selected scope and group.
4. If a selected change is unresolved or otherwise unsuitable, stop and ask. The safety boundary in `SKILL.md` governs, including what may happen to suspected secrets.
5. Preserve all out-of-scope changes and all in-scope groups not yet being committed.
6. Run relevant pre-commit verification when the repository or user requires it. If verification cannot run, report that before committing when the risk is material.

## Commit

- Use a non-interactive `git commit` command for each atomic group.
- Pass a single-line message with `git commit -m <subject>`.
- For a body, pass the subject and body as separate `-m` arguments.
- Quote every `-m` argument. A joined scope contains `&` and a breaking-change subject contains `!`; both are shell metacharacters, and an unquoted `&` backgrounds the command instead of committing the message.
- Do not amend, bypass hooks, disable signing, or use `--no-verify` unless the user explicitly requests it.
- If hooks modify files or reject the commit, inspect the new status and report the exact result. Do not retry blindly.

## Verification

After each success:

1. Read the new commit subject and summary with `git show --stat --oneline --decorate --no-renames HEAD` or an equivalent read-only command.
2. Read the committed path set with `git diff-tree --no-commit-id --name-only -r HEAD`.
3. Confirm that the subject matches the generated message and the committed paths match the recorded staged set.
4. Confirm that no out-of-scope changes were included and that remaining selected groups are still present.
5. Report the short commit hash and subject. After the final commit, report the final status and any intentionally preserved changes.

If `git commit` fails, do not claim success. Report the failure and the minimum next action.
