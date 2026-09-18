# Writeback

Chrome files: `<user-data>/<Profile>/Bookmarks` and `Bookmarks.bak`. The script defaults to the macOS, Windows, or Linux user-data directory of the platform it runs on; pass `--user-data` for other installs such as Chromium or a portable profile.

## Preconditions

1. No Chrome process is alive. The script probes `pgrep`/`ps` on POSIX and `tasklist` on Windows; a leftover Helper or crashpad process belongs to Chrome and still counts as running. On Linux the process name is often `chrome` or `google-chrome`, not the macOS string `Google Chrome`. When every probe is unavailable it refuses to write, and `--assume-quit` only unblocks that case after the user confirms Chrome is quit.
   The `ps` fallback matches the browser by exact command name (`chrome`, `google-chrome`, `Google Chrome`, `Chromium`, and their helpers). Other Electron apps ship their own `chrome_crashpad_handler`, and that must not block a writeback: when a verdict looks like a false positive, re-check with `pgrep -fl "Google Chrome"` on macOS or `pgrep -x chrome` / `pgrep -x google-chrome` on Linux, report the finding to the user, and never edit the guard to make the write pass.
   A sandboxed run often cannot list processes; re-run the check with the permissions it needs instead of treating "cannot tell" as "quit".
2. The prepared JSON exists, was shown to the user (counts + top-level folders), and is a complete Chrome Bookmarks document: keep `other`, `synced`, and every top-level key the original had, and replace only the contents of `roots.bookmark_bar`. Do not assume a fixed key list — Chrome adds `sync_metadata` when sync metadata exists and drops it again on its own. The script refuses a file without `roots.bookmark_bar`.
3. The user asked to write, or said Chrome has quit after an organize step.

If any precondition fails, stop. Do not write.

## Copy

```bash
python3 scripts/chrome_bookmarks.py write --src <prepared.json> --user-data "$HOME/Library/Application Support/Google/Chrome"
```

`--user-data` and `--profile` work before or after the subcommand. The script refuses to run while Chrome is alive, then:

- refuses **before writing** if `other` or `synced` would drop from a non-zero count to 0, unless `--allow-empty-roots` is passed after the user confirms those roots may go empty;
- keeps the current file as `Bookmarks.bak`, so the previous tree survives as a rollback copy;
- replaces `Bookmarks` atomically (temp file + `os.replace`) and sets mode `600`;
- reads the file back and reports the bar URL count plus the top-level folders;
- prints `warning:` lines for loose URLs on the bookmark bar, an existing file it could not compare against, or empty roots that were explicitly allowed.

Stop and ask the user when the script refuses because 其他书签 or 移动设备书签 would drop to 0. Do not pass `--allow-empty-roots` until they confirm.

## Rollback

Three files are not interchangeable:

- `Bookmarks.raw` in the archive directory is the tree from before organize. Prefer it to undo a writeback.
- `Bookmarks.bak` is the live tree from immediately before this write. Chrome overwrites it the next time it saves, so it is only safe until Chrome launches and writes bookmarks again.
- The prepared JSON is the organized tree. Use it to re-apply organize, not to undo it.

Restore: quit Chrome fully → `write --src` the chosen file (mode `600` is set by the script) → start Chrome and confirm the bar. Do not hand-merge two trees; pick one.

`Bookmarks.bak` and the live file stop matching the prepared copy byte for byte once Chrome saves again: it rewrites `id`s and `checksum`. Compare structure and counts, not hashes.

## Sync

Signed-in bookmark sync treats the cloud copy as a peer:

- If the cloud still has the old tree, the next launch **merges or restores** it. Local writeback is not enough.
- The durable fix is: user deletes bookmarks while signed in (cloud becomes empty) → quit Chrome → writeback → open Chrome and confirm the new tree → leave sync on so this tree uploads.
- Temporarily turning bookmark sync off is optional and only for the write window. Do not tell the user to keep sync off.

After writeback, tell the user to look at the bookmark bar before doing anything else. If old folders reappear, the cloud was not empty.

## Never

- Edit Preferences or wipe `Sync Data` to force an upload.
- `kill` Chrome.
- Empty `other` or `synced`, or pass `--allow-empty-roots`, without an explicit request.
- Drop a content folder the user did not name (see taxonomy).
