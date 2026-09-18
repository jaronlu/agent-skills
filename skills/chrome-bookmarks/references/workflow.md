# Workflow

Use `scripts/chrome_bookmarks.py` for `inspect`, `emit`, `diff`, and `write`. Classification is done by the agent; `emit` assigns `id` / `guid` / timestamps, copies every original top-level key, and replaces only `roots.bookmark_bar`.

## Profile

Resolve the Chrome user-data profile from `Local State` → `profile.last_used`. If that key is missing, stop and pass `--profile`. Do not guess `Default`.

Defaults:

- macOS `~/Library/Application Support/Google/Chrome/<Profile>`
- Windows `%LOCALAPPDATA%\Google\Chrome\User Data\<Profile>`
- Linux `~/.config/google-chrome/<Profile>`

Pass `--user-data` when Chrome lives elsewhere, including Chromium. `inspect` prints `archive_default`.

## Archive

Keep archives and prepared trees outside this skill package and its repository.

Use the directory the user already uses. If they have none, use `~/ChromeBookmarksArchive/<YYYY-MM-DD>_<profile>/`. Same calendar day and profile reuse that folder; do not create a parallel archive location.

`Bookmarks.raw` is the pre-organize rollback for that folder. Copy the live `Bookmarks` file to it only when `Bookmarks.raw` does not exist; never overwrite it.

Organize from the live `Bookmarks` file. After a later writeback, live has moved on — still do not overwrite `Bookmarks.raw`. On a later session read the newest `manifest.json` in that tree first for the accepted scheme.

## Inspect

Run `inspect` and report what it prints. Stop.

## Organize

Chrome may stay running. Do not write the live profile.

1. Read the live `Bookmarks` file as JSON and archive it as above (`Bookmarks.raw` only if missing).
2. Flatten every URL from all three roots (`bookmark_bar`, `other`, `synced`) with its folder path. Ask for, or reuse, the user's own scheme — from this conversation, a file they name, the newest manifest in their archive, or an earlier plan. When there is none, start from [taxonomy.md](taxonomy.md), follow its decision order, and adapt it to the bookmarks you actually see instead of creating categories they have no items for. Apply taxonomy bookmark names (`<area>·<slug>`) even when the user supplied a folder scheme, unless they gave their own naming rule. Put `bookmark_bar` items into the plan. If `other` or `synced` still holds bookmarks, list them separately in the report; do not empty those roots unless the user confirms moving or dropping them.
3. Before presenting the plan, diff the target top-level set against the one the user has now. When the two are identical, put "top-level unchanged, internal moves only" in the first line of the report and ask whether that is intended. A re-organized bar that looks the same reads as no work done.
4. Always apply [cleanup-rules.md](cleanup-rules.md), including when the user supplied a scheme. Its limits are defaults — use the user's numbers when they give any.
5. Write a plan JSON next to the raw copy (fields in [schema.md](schema.md)). Run `emit --src <live Bookmarks> --plan <plan.json> --out <prepared.json>`, then `diff --old <live Bookmarks> --new <prepared.json>`. Report bar counts and the `other`/`synced` lines; then the new top-level list. Stop and wait for writeback confirmation.

## Writeback

Only after the user says Chrome has quit, follow [writeback.md](writeback.md). If `other` or `synced` would drop to 0, the script refuses before writing. Ask the user; only then re-run with `--allow-empty-roots`. Report the script's `warning:` lines, then re-read the file and confirm counts by structure — Chrome rewrites `id`s and `checksum` the next time it saves, so a different hash is expected.

## Restore

Quit Chrome fully, then `write` the chosen file. Prefer the organize-step `Bookmarks.raw` in the archive. `Bookmarks.bak` is the pre-write tree only until Chrome launches and saves again. The prepared JSON is the organized tree — use it to re-apply organize, not to undo it. Do not hand-merge two trees.
