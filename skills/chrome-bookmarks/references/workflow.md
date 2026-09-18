# Workflow

Use `scripts/chrome_bookmarks.py` for `inspect`, `emit`, `diff`, and `write`. Classification is done by the agent; `emit` assigns `id` / `guid` / timestamps, copies every original top-level key, and replaces only `roots.bookmark_bar`.

## Profile

Resolve the Chrome user-data profile from `Local State` → `profile.last_used`. Do not guess `Default` when another directory is last used.

Defaults:

- macOS `~/Library/Application Support/Google/Chrome/<Profile>`
- Windows `%LOCALAPPDATA%\Google\Chrome\User Data\<Profile>`
- Linux `~/.config/google-chrome/<Profile>`

Pass `--user-data` when Chrome lives elsewhere, including Chromium. `inspect` prints `archive_default`.

## Archive

Keep archives and prepared trees outside this skill package and its repository.

Use the directory the user already uses. If they have none, use `~/ChromeBookmarksArchive/<YYYY-MM-DD>_<profile>/`. Copy the raw file there once per session as `Bookmarks.raw`. On a later session read the newest `manifest.json` in that tree first. Do not invent a second backup if the user already has one.

## Inspect

Run `inspect` and report what it prints. Stop.

## Organize

Chrome may stay running. Do not write the live profile.

1. Read `Bookmarks` as JSON and archive it as above.
2. Flatten every URL from all three roots (`bookmark_bar`, `other`, `synced`) with its folder path. Ask for, or reuse, the user's own scheme — from this conversation, a file they name, the newest manifest in their archive, or an earlier plan. When there is none, start from [taxonomy.md](taxonomy.md), follow its decision order, and adapt it to the bookmarks you actually see instead of creating categories they have no items for. Put `bookmark_bar` items into the plan. If `other` or `synced` still holds bookmarks, list them separately in the report; do not empty those roots unless the user confirms moving or dropping them.
3. Before presenting the plan, diff the target top-level set against the one the user has now. When the two are identical, put "top-level unchanged, internal moves only" in the first line of the report and ask whether that is intended. A re-organized bar that looks the same reads as no work done.
4. Apply [cleanup-rules.md](cleanup-rules.md). Its limits are defaults — use the user's numbers when they give any.
5. Write a plan JSON next to the raw copy (fields in [schema.md](schema.md)). Run `emit --src <Bookmarks.raw> --plan <plan.json> --out <prepared.json>`, then `diff --old <Bookmarks.raw> --new <prepared.json>`. Report those counts and the new top-level list. Stop and wait for writeback confirmation.

## Writeback

Only after the user says Chrome has quit, follow [writeback.md](writeback.md). If `other` or `synced` would drop to 0, the script refuses before writing. Ask the user; only then re-run with `--allow-empty-roots`. Report the script's `warning:` lines, then re-read the file and confirm counts by structure — Chrome rewrites `id`s and `checksum` the next time it saves, so a different hash is expected.

## Restore

Quit Chrome fully, then `write` the chosen file. Prefer the organize-step `Bookmarks.raw` in the archive. `Bookmarks.bak` is the pre-write tree only until Chrome launches and saves again. The prepared JSON is the organized tree — use it to re-apply organize, not to undo it. Do not hand-merge two trees.
