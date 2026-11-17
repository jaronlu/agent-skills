---
name: chinese-links
description: Resolve OpenWorker file-card links whose Chinese file names fail to open, by decoding percent-encoded paths and locating the real file on disk. Use when an OpenWorker file card does not open, fails to download, or a file with a Chinese name will not open (中文名文件打不开, 点不开, 下载失败).
metadata:
  version: "1.2"
---

# OpenWorker Chinese Links

## Symptoms and diagnosis

Card links are URL-encoded, for example `%E5%8D%8E%E6%9E%97...`. Decoding them gives the path of the real file on this machine.

Known: the server reads Chinese file names correctly, and the related requests return 200. The failure is in the client's card-opening step. Whether the cause is decoding or rendering is not yet verified. To check, click "Open" once in the App, then inspect the new entries in the server log.

## Locating a file

```bash
python3 <skill-dir>/scripts/ow-open.py '<encoded relative path or file name>'
python3 <skill-dir>/scripts/ow-open.py '<file name>' --open
python3 <skill-dir>/scripts/ow-open.py --list
```

- Accepts encoded paths (which may include subdirectories), bare file names, absolute paths, and `file://` URLs.
- By default searches `~/OpenWorker` and the current directory. The current directory is skipped when the command runs from the home directory or `/`. `--root` sets the search roots explicitly.
- Decodes up to twice to handle double encoding.
- Matches by path suffix. When several files match, lists all of them and selects none.
- Prints the path by default. `--open` opens the file with the default app, but only for document types on the allowlist (`.pdf`, `.md`, `.txt`, Office formats, `.csv`, `.json`, common image formats, and similar). Other types are refused with exit code 1, and the user must open them by hand. The allowlist is `SAFE_OPEN_EXT` in `scripts/ow-open.py`.
- Refuses `.` and `..` in the target, so a lookup cannot leave a search root.
- macOS only: `--open` calls the `open` command.

Replace `<skill-dir>` with this skill's install path.

## Boundaries

- Do not modify OpenWorker's configuration, database, or APIs, and do not infer how it generates links.
- Do not rename a user's existing files without permission. When a rename is needed, give the `mv` command and ask the user to confirm.
- Server endpoints require authentication and are not a troubleshooting method.
