#!/usr/bin/env python3
"""Inspect Chrome bookmark files and copy a prepared JSON only when Chrome is quit."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_ORDER = ("bookmark_bar", "other", "synced")
ROOT_LABELS = {"bookmark_bar": "书签栏", "other": "其他书签", "synced": "移动设备书签"}


def default_user_data() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library/Application Support/Google/Chrome"
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA")
        return (Path(local) if local else home / "AppData/Local") / "Google/Chrome/User Data"
    return home / ".config/google-chrome"


def _pgrep_verdict(result: subprocess.CompletedProcess[str]) -> bool | None:
    if result.returncode == 0:
        return bool(result.stdout.strip())
    if result.returncode == 1:
        return False
    return None


def _ps_verdict(result: subprocess.CompletedProcess[str]) -> bool | None:
    if result.returncode != 0:
        return None
    return any("chrome" in line.lower() for line in result.stdout.splitlines())


def _tasklist_verdict(result: subprocess.CompletedProcess[str]) -> bool | None:
    if result.returncode != 0:
        return None
    return "chrome.exe" in result.stdout.lower()


def chrome_running() -> bool | None:
    """True/False when the platform can answer, None when it cannot be detected."""
    if sys.platform == "win32":
        probes = [(["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/NH"], _tasklist_verdict)]
    else:
        probes = [
            (["pgrep", "-f", "Google Chrome"], _pgrep_verdict),
            (["ps", "-A", "-o", "comm="], _ps_verdict),
        ]
    answered = False
    for command, interpret in probes:
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True)
        except OSError:
            continue
        verdict = interpret(result)
        if verdict is None:
            continue
        answered = True
        if verdict:
            return True
    return False if answered else None


def last_used_profile(user_data: Path) -> str:
    local_state = user_data / "Local State"
    if not local_state.is_file():
        raise SystemExit(f"Local State not found: {local_state}")
    data = json.loads(local_state.read_text(encoding="utf-8"))
    name = data.get("profile", {}).get("last_used") or "Default"
    return str(name)


def count_urls(node: dict) -> int:
    if node.get("type") == "url":
        return 1
    return sum(count_urls(child) for child in node.get("children") or [])


def load_bookmarks(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"not readable as JSON: {path} ({exc})") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"not a JSON object: {path}")
    return data


def root_nodes(data: dict) -> dict:
    roots = data.get("roots")
    return roots if isinstance(roots, dict) else {}


def top_level_folders(node: dict) -> list[str]:
    return [
        str(child.get("name", ""))
        for child in node.get("children") or []
        if child.get("type") == "folder"
    ]


def atomic_write(path: Path, data: bytes) -> None:
    handle, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f"{path.name}.", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def folder_lines(node: dict, prefix: str, lines: list[str]) -> None:
    for child in node.get("children") or []:
        if child.get("type") != "folder":
            continue
        path = f"{prefix}{child.get('name', '')}"
        lines.append(f"{count_urls(child):5d}  {path}")
        folder_lines(child, path + " / ", lines)


def cmd_inspect(args: argparse.Namespace) -> int:
    user_data = Path(args.user_data).expanduser() if args.user_data else default_user_data()
    profile = args.profile or last_used_profile(user_data)
    bookmarks = user_data / profile / "Bookmarks"
    running = chrome_running()
    print(f"chrome_running={'unknown' if running is None else running}")
    print(f"user_data={user_data}")
    print(f"profile={profile}")
    print(f"bookmarks={bookmarks}")
    if not bookmarks.is_file():
        print("missing Bookmarks file", file=sys.stderr)
        return 1
    roots = root_nodes(load_bookmarks(bookmarks))
    total = 0
    for key in ROOT_ORDER:
        node = roots.get(key)
        if node is None:
            continue
        count = count_urls(node)
        total += count
        print(f"root {key} ({ROOT_LABELS[key]}): urls={count}")
    print(f"urls_total={total}")
    print("folders:")
    printed = False
    for key in ROOT_ORDER:
        node = roots.get(key)
        if node is None:
            continue
        lines: list[str] = []
        folder_lines(node, f"{ROOT_LABELS[key]} / ", lines)
        if lines:
            printed = True
            print(f"[{key}]")
            print("\n".join(lines))
    if not printed:
        print("  (no folders)")
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    warnings: list[str] = []
    running = chrome_running()
    if running is None and not args.assume_quit:
        print(
            "refuse write: cannot tell whether Google Chrome is running here; "
            "quit Chrome and re-run with --assume-quit",
            file=sys.stderr,
        )
        return 2
    if running:
        print("refuse write: Google Chrome is still running", file=sys.stderr)
        return 2
    if running is None:
        warnings.append("Chrome process check unavailable; --assume-quit was passed")
    src = Path(args.src).expanduser()
    if not src.is_file():
        print(f"source not found: {src}", file=sys.stderr)
        return 1
    prepared = load_bookmarks(src)
    new_roots = root_nodes(prepared)
    if not isinstance(new_roots.get("bookmark_bar"), dict):
        print(
            f"refuse write: {src} is not a Chrome Bookmarks document (missing roots.bookmark_bar)",
            file=sys.stderr,
        )
        return 1
    user_data = Path(args.user_data).expanduser() if args.user_data else default_user_data()
    profile = args.profile or last_used_profile(user_data)
    dest_dir = user_data / profile
    dest = dest_dir / "Bookmarks"
    bak = dest_dir / "Bookmarks.bak"
    if dest.is_file():
        try:
            current = root_nodes(load_bookmarks(dest))
        except SystemExit as exc:
            warnings.append(f"existing Bookmarks not compared ({exc})")
        else:
            for key in ("other", "synced"):
                before = count_urls(current.get(key) or {})
                after = count_urls(new_roots.get(key) or {})
                if before and not after:
                    warnings.append(
                        f"{key} ({ROOT_LABELS[key]}) drops from {before} to 0 bookmarks; "
                        "confirm with the user before relying on this writeback"
                    )
    loose = sum(1 for child in new_roots["bookmark_bar"].get("children") or [] if child.get("type") == "url")
    if loose:
        warnings.append(f"书签栏 has {loose} loose URL(s); the taxonomy keeps folders only")
    dest_dir.mkdir(parents=True, exist_ok=True)
    if dest.is_file():
        shutil.copyfile(dest, bak)
        bak.chmod(0o600)
        print(f"kept previous tree as {bak}")
    atomic_write(dest, src.read_bytes())
    dest.chmod(0o600)
    print(f"wrote {dest}")
    written = root_nodes(load_bookmarks(dest))
    bar = written.get("bookmark_bar") or {}
    print(f"verified {dest}: bar_urls={count_urls(bar)}")
    print("top_level_folders=" + (", ".join(top_level_folders(bar)) or "(none)"))
    for message in warnings:
        print(f"warning: {message}")
    return 0


def add_common_args(parser: argparse.ArgumentParser, *, subcommand: bool = False) -> None:
    # A subparser default would overwrite the value parsed before the subcommand,
    # so subcommand-level copies only record an explicitly passed flag.
    parser.add_argument(
        "--user-data",
        default=argparse.SUPPRESS if subcommand else None,
        help=f"Chrome user-data directory (default: {default_user_data()}).",
    )
    parser.add_argument(
        "--profile",
        default=argparse.SUPPRESS if subcommand else None,
        help="Profile directory name. Default: Local State last_used.",
    )
    parser.add_argument(
        "--assume-quit",
        action="store_true",
        default=argparse.SUPPRESS if subcommand else False,
        help="Write even when the Chrome process check is unavailable on this platform.",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Chrome bookmarks or copy a prepared JSON after Chrome quits."
    )
    add_common_args(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect", help="Print profile, running state, and folder counts.")
    add_common_args(inspect, subcommand=True)
    inspect.set_defaults(func=cmd_inspect)

    write = sub.add_parser("write", help="Copy prepared JSON onto the live profile.")
    write.add_argument("--src", required=True, help="Prepared Bookmarks JSON path.")
    add_common_args(write, subcommand=True)
    write.set_defaults(func=cmd_write)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
