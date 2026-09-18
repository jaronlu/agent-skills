# Writeback

Chrome files: `<user-data>/<Profile>/Bookmarks` and `Bookmarks.bak`. The script defaults to the macOS, Windows, or Linux user-data directory of the platform it runs on; pass `--user-data` for other installs such as Chromium or a portable profile.

## Preconditions

1. No Chrome process is alive. The script probes `pgrep`/`ps` on POSIX and `tasklist` on Windows; a leftover Helper/crashpad process still counts as running. When every probe is unavailable it refuses to write, and `--assume-quit` only unblocks that case after the user confirms Chrome is quit.
   A sandboxed run often cannot list processes; re-run the check with the permissions it needs instead of treating "cannot tell" as "quit".
2. The prepared JSON exists, was shown to the user (counts + top-level folders), and is a complete Chrome Bookmarks document: keep `version`, `checksum`, `sync_metadata` and all three `roots`, and replace only the contents of `roots.bookmark_bar`. The script refuses a file without `roots.bookmark_bar`.
3. The user asked to write, or said Chrome has quit after an organize step.

If any precondition fails, stop. Do not write.

## Copy

```bash
python3 scripts/chrome_bookmarks.py write --src <prepared.json> --user-data "$HOME/Library/Application Support/Google/Chrome"
```

`--user-data` and `--profile` work before or after the subcommand. The script refuses to run while Chrome is alive, then:

- keeps the current file as `Bookmarks.bak`, so the previous tree survives as a rollback copy;
- replaces `Bookmarks` atomically (temp file + `os.replace`) and sets mode `600`;
- reads the file back and reports the bar URL count plus the top-level folders;
- prints `warning:` lines for a root that would drop to 0 bookmarks, loose URLs on the bookmark bar, or an existing file it could not compare against.

Stop and ask the user when a warning says 其他书签 or 移动设备书签 drops to 0: that write deletes bookmarks the plan may not have covered. The archive copy from the organize step is the second rollback source.

## Sync

Signed-in bookmark sync treats the cloud copy as a peer:

- If the cloud still has the old tree, the next launch **merges or restores** it. Local writeback is not enough.
- The durable fix is: user deletes bookmarks while signed in (cloud becomes empty) → quit Chrome → writeback → open Chrome and confirm the new tree → leave sync on so this tree uploads.
- Temporarily turning bookmark sync off is optional and only for the write window. Do not tell the user to keep sync off.

After writeback, tell the user to look at the bookmark bar before doing anything else. If old folders reappear, the cloud was not empty.

## Never

- Edit Preferences or wipe `Sync Data` to force an upload.
- `kill` Chrome.
- Write a partial tree that drops `归档/工作` without an explicit request.
