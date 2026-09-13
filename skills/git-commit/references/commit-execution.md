# Commit Execution

Read this file only in commit mode.

## Scope and atomicity

Before changing the index:

1. Use the scope selected by the main skill. Determine it from Git's porcelain `XY` status columns, not from an edit summary: `X` means staged/index, `Y` means unstaged/worktree, a space means no change in that column, and `??` means untracked rather than staged. **A** means staged-only; **B** means staged, unstaged, and untracked changes; an empty index with other changes means all changes.
2. Record the baseline with `git status --short`, `git diff --cached --name-status`, `git diff --name-status`, and the untracked path list.
3. Partition the selected diff into logical groups. Keep one logical change together across files, and use separate commits for unrelated intents. A joined scope such as `feat(common&share&tool): ...` is a single group only when the intent behind it is single; when the per-scope lines describe independent changes, they are separate groups. This rule applies to every selected scope, including staged-only A and all-change B.
4. For each group, stage only that group's paths or hunks. Use path- or hunk-level staging when a file contains multiple groups; never use a blanket staging command that pulls in out-of-scope changes.
5. If the index already contains more than the next group, use index-only operations such as `git reset -p` or `git reset -- <path>` to unstage the other selected groups before staging the next one. Do not use commands that discard working-tree content.

## Preconditions

1. Confirm that the current index contains exactly the next atomic group.
2. Record that group's staged path set with `git diff --cached --name-only` and confirm it matches the selected scope and group.
3. If a selected change has unresolved conflicts or is otherwise clearly unsuitable for committing, pause and ask the user whether to exclude it, handle it separately, or stop. For suspected secrets, ask only whether to exclude them, remediate and re-inspect them, or stop; never commit suspected secret content, even in a separate commit. Do not reveal secret values, silently omit the group, or commit it before the user decides.
4. Preserve all out-of-scope changes and all in-scope groups not yet being committed.
5. Run relevant pre-commit verification when the repository or user requires it. If verification cannot run, report that before committing when the risk is material.

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
