---
name: chrome-bookmarks
description: Organize, dedupe, back up, or restore Chrome bookmarks (整理书签, 去冗余).
---

# Chrome Bookmarks

Classify, dedupe, and write Chrome bookmarks. The folder scheme belongs to the user: reuse the one they already have, or build one from their bookmarks with the default pattern.

## Modes

- **Inspect**: report profile, folder tree, and counts. Do not write.
- **Organize**: classify into a plan and emit a prepared Bookmarks JSON in the archive. Do not touch the live profile. Chrome may stay open.
- **Writeback**: copy the prepared JSON onto the live profile after Chrome has fully quit.
- **Restore**: copy a rollback file onto the live profile after a bad write or a sync overwrite.

Default to Organize, then stop and wait for writeback confirmation. Do Inspect when the user only asks what is there.

## Contract

- Resolve the profile from `Local State` → `profile.last_used`. Do not guess `Default`.
- Use [scripts/chrome_bookmarks.py](scripts/chrome_bookmarks.py) for `inspect`, `emit`, `diff`, and `write`. The agent classifies; `emit` assigns `id` / `guid` / timestamps, copies every original top-level key, and replaces only `roots.bookmark_bar`.
- Follow [references/workflow.md](references/workflow.md) for the mode steps. User scheme wins; read taxonomy and cleanup only when organizing without one.
- Flatten all three roots (`bookmark_bar`, `other`, `synced`). Do not empty `other` or `synced` unless the user confirms.
- When the target top-level set matches the current one, put "top-level unchanged, internal moves only" in the first line of the report and ask whether that is intended.

## Safety Boundary

- Never replace `Bookmarks` while Chrome is running. Do not kill Chrome; ask the user to quit.
- Keep archives, prepared trees, raw backups, and machine-specific paths outside this skill package and its repository.
- Do not delete work documents, government or service pages, or user-named items unless the user names them.
- Do not empty `other` or `synced` in the prepared tree, or pass `--allow-empty-roots`, unless the user confirmed those roots may go to 0.
- Bookmark sync will merge or restore the cloud copy after sign-in. State this risk every time you write.
- Never weaken the running-process guard, or edit the script around it, to get a writeback through. Verify the real process state and report it; never loosen the guard. `--assume-quit` only covers a probe that cannot answer at all.

## Output

- Inspect: profile, last-used name, per-root URL counts (书签栏 / 其他书签 / 移动设备), folder counts, default archive path.
- Organize: archive and manifest paths, emit / diff counts, top-level list marked 新增 / 删除 / 未变. Stop here unless the user asked to write.
- Writeback: destination, `Bookmarks.bak`, top-level folders, any `warning:` line, how to restore (raw archive first). Remind the user to verify in Chrome before relying on sync.
- Restore: which source (`Bookmarks.raw` / `Bookmarks.bak` / prepared) and why, then the writeback output.

## References

Read each one only when its trigger applies.

| Read | When |
| --- | --- |
| [references/workflow.md](references/workflow.md) | Any mode: profile, archive, and inspect / organize / writeback / restore steps |
| [references/taxonomy.md](references/taxonomy.md) | Organize, or the user asks how folders should be named |
| [references/cleanup-rules.md](references/cleanup-rules.md) | Organize or archive cleanup |
| [references/schema.md](references/schema.md) | Before writing a plan or a Bookmarks document |
| [references/writeback.md](references/writeback.md) | Before any live-profile write |
