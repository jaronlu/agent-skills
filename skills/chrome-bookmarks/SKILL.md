---
name: chrome-bookmarks
description: Organize, dedupe, and write back Chrome bookmarks with the user's own folder scheme. Use when the user asks to 整理书签, 去冗余, back up Chrome bookmarks, or restore bookmarks after a sync overwrite.
---

# Chrome Bookmarks

Classify, dedupe, and write Chrome bookmarks. The folder scheme belongs to the user: reuse the one they already have, or build one from their bookmarks with the default pattern.

## Modes

- **Inspect**: report profile, folder tree, and counts. Do not write.
- **Organize**: produce a new Bookmarks JSON (and optional HTML) without touching the live profile.
- **Writeback**: copy the prepared JSON onto the live profile after Chrome has fully quit.
- **Restore**: put a rollback copy back after a bad write or a sync overwrite.

Default to Organize, then stop and wait for writeback confirmation. Do Inspect when the user only asks what is there.

## Procedure

1. Resolve the Chrome user-data profile from `Local State` → `profile.last_used`. Do not guess `Default` when another directory is last used. Defaults: macOS `~/Library/Application Support/Google/Chrome/<Profile>`, Windows `%LOCALAPPDATA%\Google\Chrome\User Data\<Profile>`, Linux `~/.config/google-chrome/<Profile>`. Pass `--user-data` when Chrome lives elsewhere, including Chromium.
2. Abort writeback if any `Google Chrome` process is running. Closing the window is not enough; require a full quit (`Cmd+Q` on macOS). Only the browser itself and its own helpers count: other Electron apps ship a `chrome_crashpad_handler` too, so a bare match on `chrome` is a false positive. When a verdict looks wrong, re-check with `pgrep -fl "Google Chrome"` and report what you found — never loosen the guard in the script to make a write pass. If the process check is unavailable, the script refuses to write unless `--assume-quit` is passed, and that needs the user's explicit confirmation.
3. Read `Bookmarks` as JSON. Keep a copy of the raw file in the archive directory the user already uses (`<date>_<profile>` per run) when organizing for the first time in a session; on a later session read the newest `manifest.json` there first. Do not invent a second backup if the user already has one. Write the manifest next to the prepared tree — scheme name, new top-level list, kept/moved/removed counts, prepared-file hash — so the accepted scheme is reused instead of re-derived. Keep archives and prepared trees outside this skill package and its repository.
4. Flatten every URL from all three roots (`bookmark_bar`, `other`, `synced`) with its folder path. Ask for, or reuse, the user's own scheme — from this conversation, a file they name, the newest manifest in their archive, or an earlier plan. When there is none, start from [references/taxonomy.md](references/taxonomy.md), follow its decision order when a bookmark could fit two folders, and adapt it to the bookmarks you actually see instead of creating categories they have no items for. Hold the structural rules there: folders stay within three levels, leaves are named `<company>·<slug>`, and a domain only earns its own folder at four or more entries. If `other` or `synced` still holds bookmarks, list them separately: writeback empties both, so the user must confirm.
   Before presenting the plan, diff the target top-level set against the one the user has now: when the two are identical, put "top-level unchanged, internal moves only" in the first line of the report and ask whether that is intended. A re-organized bar that looks the same reads as no work done.
5. Apply [references/cleanup-rules.md](references/cleanup-rules.md): drop duplicate and tracking variants of what is kept elsewhere, low-value pages, console and session URLs; keep official sites, repository roots, and work documents. Its limits are defaults — use the user's numbers when they give any.
6. Emit the new tree to the archive directory first, as a complete copy of the original document with only `roots.bookmark_bar` replaced: keep `other`, `synced`, and every top-level key the original had (`checksum`, `version`, and `sync_metadata` when present — Chrome adds and drops that one on its own, so never assume a fixed key list). Folder and url nodes need `id`, `guid`, and Chrome-epoch timestamps; follow [references/schema.md](references/schema.md). Report folder counts. Do not write the live profile yet.
7. Writeback only after the user says Chrome has quit, and only by following [references/writeback.md](references/writeback.md). Report the script's `warning:` lines, then re-read the file and confirm counts by structure — Chrome rewrites `id`s and `checksum` the next time it saves, so a different hash is expected.

Use [scripts/chrome_bookmarks.py](scripts/chrome_bookmarks.py) for inspect and for the final copy. Classification may be done by the agent using the references; the script must still be used to refuse writeback when Chrome is running.

## Safety Boundary

- Never replace `Bookmarks` while Chrome is running.
- Never write bookmark data, prepared trees, raw backups, or machine-specific paths into this skill package or its repository.
- Do not delete work documents, government or service pages, or user-named items unless the user names them.
- Bookmark sync will merge or restore the cloud copy after sign-in. Writeback after the user has emptied bookmarks (local and, if needed, cloud) or after they accept a merge. State this risk every time you write.
- Do not kill Chrome. Ask the user to quit.
- Never weaken the running-process guard, or edit the script around it, to get a writeback through. Verify the real process state and report it; `--assume-quit` only covers a probe that cannot answer at all.

## Output

- Inspect: profile directory, last-used name, per-root URL counts (书签栏 / 其他书签 / 移动设备), folder counts.
- Organize: archive and manifest paths, kept / moved / removed counts, and the new top-level list marked 新增 / 删除 / 未变 against the tree the user has.
- Writeback: destination path, rollback copy (`Bookmarks.bak`) and its hash, top-level folder list, any `warning:` line, and how to restore. Remind the user to verify in Chrome before relying on sync.

## References

Read each one only when its trigger applies.

| Read | When |
| --- | --- |
| [references/taxonomy.md](references/taxonomy.md) | Organize, or the user asks how folders should be named |
| [references/cleanup-rules.md](references/cleanup-rules.md) | Organize or archive cleanup |
| [references/writeback.md](references/writeback.md) | Before any live-profile write |
| [references/schema.md](references/schema.md) | Before writing or editing a Bookmarks document |
