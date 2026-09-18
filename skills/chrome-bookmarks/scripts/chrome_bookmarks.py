#!/usr/bin/env python3
"""Inspect, emit, diff, and copy Chrome bookmark files; never write while Chrome runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Callable
from datetime import date
from pathlib import Path

ROOT_ORDER = ("bookmark_bar", "other", "synced")
ROOT_LABELS = {"bookmark_bar": "书签栏", "other": "其他书签", "synced": "移动设备书签"}
CHROME_EPOCH_DELTA = 11_644_473_600
BROWSER_COMMS = {
    "chrome",
    "google-chrome",
    "google-chrome-stable",
    "google-chrome-beta",
    "google-chrome-unstable",
    "chromium",
    "chromium-browser",
    "google chrome",
    "google chrome helper",
    "google chrome helper (renderer)",
    "google chrome helper (gpu)",
    "google chrome helper (plugin)",
    "chromium helper",
}


def default_user_data() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library/Application Support/Google/Chrome"
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA")
        return (Path(local) if local else home / "AppData/Local") / "Google/Chrome/User Data"
    return home / ".config/google-chrome"


def default_archive_dir(profile: str) -> Path:
    return Path.home() / "ChromeBookmarksArchive" / f"{date.today().isoformat()}_{profile}"


def _pgrep_verdict(result: subprocess.CompletedProcess[str]) -> bool | None:
    if result.returncode == 0:
        return bool(result.stdout.strip())
    if result.returncode == 1:
        return False
    return None


def _is_browser_comm(line: str) -> bool:
    raw = line.strip()
    if not raw:
        return False
    lower = raw.lower()
    if "chrome_crashpad_handler" in lower:
        return "google chrome.app" in lower or "chromium.app" in lower
    name = Path(raw).name.lower()
    if name in BROWSER_COMMS or lower in BROWSER_COMMS:
        return True
    return lower.startswith("google chrome") or lower.startswith("chromium")


def _ps_verdict(result: subprocess.CompletedProcess[str]) -> bool | None:
    if result.returncode != 0:
        return None
    # Only the browser itself and its helpers count: other Electron apps ship a
    # chrome_crashpad_handler too and must not block a writeback.
    return any(_is_browser_comm(line) for line in result.stdout.splitlines())


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
            (["pgrep", "-x", "google-chrome"], _pgrep_verdict),
            (["pgrep", "-x", "google-chrome-stable"], _pgrep_verdict),
            (["pgrep", "-x", "chromium"], _pgrep_verdict),
            (["pgrep", "-x", "chromium-browser"], _pgrep_verdict),
            (["pgrep", "-x", "chrome"], _pgrep_verdict),
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
    print(f"archive_default={default_archive_dir(profile)}")
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
    bar = roots.get("bookmark_bar")
    print("top_level_folders=" + (", ".join(top_level_folders(bar if isinstance(bar, dict) else {})) or "(none)"))
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
                    message = (
                        f"{key} ({ROOT_LABELS[key]}) drops from {before} to 0 bookmarks"
                    )
                    if not args.allow_empty_roots:
                        print(
                            f"refuse write: {message}; "
                            "re-run with --allow-empty-roots after the user confirms",
                            file=sys.stderr,
                        )
                        return 3
                    warnings.append(f"{message}; --allow-empty-roots was passed")
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


def collect_leaves(node: dict, path: list[str], found: list[tuple[str, str, str]]) -> None:
    for child in node.get("children") or []:
        if child.get("type") == "folder":
            collect_leaves(child, path + [str(child.get("name", ""))], found)
        else:
            found.append(("/".join(path), str(child.get("name", "")), str(child.get("url", ""))))


def cmd_diff(args: argparse.Namespace) -> int:
    old_path = Path(args.old).expanduser()
    new_path = Path(args.new).expanduser()
    for path in (old_path, new_path):
        if not path.is_file():
            print(f"missing file: {path}", file=sys.stderr)
            return 1
    old_bar = root_nodes(load_bookmarks(old_path)).get("bookmark_bar") or {}
    new_bar = root_nodes(load_bookmarks(new_path)).get("bookmark_bar") or {}
    old_leaves: list[tuple[str, str, str]] = []
    new_leaves: list[tuple[str, str, str]] = []
    collect_leaves(old_bar, [], old_leaves)
    collect_leaves(new_bar, [], new_leaves)
    stats = leaf_stats(old_leaves, new_leaves)
    print(f"old_urls={stats['old_urls']} new_urls={stats['new_urls']}")
    print(
        f"kept={stats['kept']} added={stats['added']} removed={stats['removed']} "
        f"moved={stats['moved']} renamed={stats['renamed']}"
    )
    old_top = top_level_folders(old_bar)
    new_top = top_level_folders(new_bar)
    print("old_top_level_folders=" + (", ".join(old_top) or "(none)"))
    print("new_top_level_folders=" + (", ".join(new_top) or "(none)"))
    print(f"top_level_change={'changed' if set(old_top) != set(new_top) else 'same'}")
    for url in stats["removed_urls"]:
        print(f"  removed  {url}")
    for url in stats["added_urls"]:
        print(f"  added    {url}")
    for url, old_path, new_path in stats["moved_rows"]:
        print(f"  moved    {url}: {old_path} -> {new_path}")
    return 0


def leaf_stats(
    old_leaves: list[tuple[str, str, str]], new_leaves: list[tuple[str, str, str]]
) -> dict:
    old_by_url = {url: (path, name) for path, name, url in old_leaves}
    new_by_url = {url: (path, name) for path, name, url in new_leaves}
    added_urls = sorted(set(new_by_url) - set(old_by_url))
    removed_urls = sorted(set(old_by_url) - set(new_by_url))
    moved = renamed = 0
    moved_rows: list[tuple[str, str, str]] = []
    for url, (path, name) in sorted(new_by_url.items()):
        if url not in old_by_url:
            continue
        old_place, old_name = old_by_url[url]
        if path != old_place:
            moved += 1
            moved_rows.append((url, old_place, path))
        if name != old_name:
            renamed += 1
    return {
        "old_urls": len(old_leaves),
        "new_urls": len(new_leaves),
        "kept": len(new_leaves) - len(added_urls),
        "added": len(added_urls),
        "removed": len(removed_urls),
        "moved": moved,
        "renamed": renamed,
        "added_urls": added_urls,
        "removed_urls": removed_urls,
        "moved_rows": moved_rows,
    }


def chrome_now() -> str:
    return str(int((time.time() + CHROME_EPOCH_DELTA) * 1_000_000))


def max_id_in(node: dict) -> int:
    best = 0
    try:
        best = int(str(node.get("id") or "0"))
    except ValueError:
        best = 0
    for child in node.get("children") or []:
        if isinstance(child, dict):
            best = max(best, max_id_in(child))
    return best


def index_urls(node: dict, found: dict[str, dict]) -> None:
    if node.get("type") == "url":
        url = str(node.get("url") or "")
        if url and url not in found:
            found[url] = node
        return
    for child in node.get("children") or []:
        if isinstance(child, dict):
            index_urls(child, found)


def index_folders(node: dict, path: tuple[str, ...], found: dict[tuple[str, ...], dict]) -> None:
    if node.get("type") == "folder":
        found[path] = node
    for child in node.get("children") or []:
        if isinstance(child, dict) and child.get("type") == "folder":
            index_folders(child, path + (str(child.get("name") or ""),), found)


def parse_folder_path(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(part).strip() for part in raw if str(part).strip()]
    return [part for part in str(raw).split("/") if part.strip()]


def copy_url_node(source: dict | None, name: str, url: str, next_id: Callable[[], str], now: str) -> dict:
    if source:
        node = {key: value for key, value in source.items() if key != "children"}
        node["type"] = "url"
        node["name"] = name
        node["url"] = url
        if not node.get("id"):
            node["id"] = next_id()
        if not node.get("guid"):
            node["guid"] = uuid.uuid4().hex
        if not node.get("date_added"):
            node["date_added"] = now
        return node
    return {
        "date_added": now,
        "guid": uuid.uuid4().hex,
        "id": next_id(),
        "name": name,
        "type": "url",
        "url": url,
    }


def ensure_folder(
    children: list[dict],
    name: str,
    next_id: Callable[[], str],
    now: str,
    original: dict | None,
) -> dict:
    for child in children:
        if child.get("type") == "folder" and child.get("name") == name:
            return child
    folder = {
        "children": [],
        "date_added": (original or {}).get("date_added") or now,
        "date_modified": now,
        "guid": (original or {}).get("guid") or uuid.uuid4().hex,
        "id": str((original or {}).get("id") or next_id()),
        "name": name,
        "type": "folder",
    }
    children.append(folder)
    return folder


def empty_root(node: dict, now: str) -> dict:
    emptied = dict(node)
    emptied["children"] = []
    emptied["date_modified"] = now
    emptied["type"] = "folder"
    return emptied


def load_plan(path: Path) -> dict:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"plan not readable as JSON: {path} ({exc})") from exc
    if not isinstance(plan, dict):
        raise SystemExit(f"plan is not a JSON object: {path}")
    items = plan.get("items")
    if not isinstance(items, list):
        raise SystemExit(f"plan missing items list: {path}")
    return plan


def cmd_emit(args: argparse.Namespace) -> int:
    src = Path(args.src).expanduser()
    plan_path = Path(args.plan).expanduser()
    out = Path(args.out).expanduser()
    if not src.is_file():
        print(f"source not found: {src}", file=sys.stderr)
        return 1
    original = load_bookmarks(src)
    roots = root_nodes(original)
    bar = roots.get("bookmark_bar")
    if not isinstance(bar, dict):
        print(
            f"refuse emit: {src} is not a Chrome Bookmarks document (missing roots.bookmark_bar)",
            file=sys.stderr,
        )
        return 1
    plan = load_plan(plan_path)
    now = chrome_now()
    next_number = 0
    for node in roots.values():
        if isinstance(node, dict):
            next_number = max(next_number, max_id_in(node))

    def next_id() -> str:
        nonlocal next_number
        next_number += 1
        return str(next_number)

    originals: dict[str, dict] = {}
    for node in roots.values():
        if isinstance(node, dict):
            index_urls(node, originals)
    original_folders: dict[tuple[str, ...], dict] = {}
    index_folders(bar, (), original_folders)

    items = plan.get("items") or []
    seen: set[str] = set()
    new_bar = dict(bar)
    new_children: list[dict] = []
    new_bar["children"] = new_children
    new_bar["date_modified"] = now
    warnings: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            print(f"refuse emit: items[{index}] is not an object", file=sys.stderr)
            return 1
        url = str(item.get("url") or "").strip()
        name = str(item.get("name") or "").strip()
        if not url:
            print(f"refuse emit: items[{index}] missing url", file=sys.stderr)
            return 1
        if url in seen:
            print(f"refuse emit: duplicate url {url}", file=sys.stderr)
            return 1
        seen.add(url)
        if not name:
            name = str((originals.get(url) or {}).get("name") or url)
        folder_path = parse_folder_path(item.get("path"))
        if len(folder_path) > 3:
            warnings.append(f"path deeper than 3 levels: {'/'.join(folder_path)}")
        parent = new_children
        walked: list[str] = []
        for folder_name in folder_path:
            walked.append(folder_name)
            folder = ensure_folder(
                parent,
                folder_name,
                next_id,
                now,
                original_folders.get(tuple(walked)),
            )
            parent = folder["children"]
        parent.append(copy_url_node(originals.get(url), name, url, next_id, now))
        if not folder_path:
            warnings.append(f"loose URL on bookmark bar: {url}")

    top_level = plan.get("top_level")
    if isinstance(top_level, list):
        names = [str(name) for name in top_level if str(name).strip()]
        for name in names:
            ensure_folder(new_children, name, next_id, now, original_folders.get((name,)))
        by_name = {
            str(child.get("name")): child
            for child in new_children
            if child.get("type") == "folder"
        }
        extras = [
            child
            for child in new_children
            if child.get("type") != "folder" or str(child.get("name")) not in names
        ]
        new_bar["children"] = [by_name[name] for name in names if name in by_name] + extras

    prepared = json.loads(json.dumps(original))
    prepared_roots = root_nodes(prepared)
    prepared_roots["bookmark_bar"] = new_bar
    if plan.get("empty_other") and isinstance(prepared_roots.get("other"), dict):
        prepared_roots["other"] = empty_root(prepared_roots["other"], now)
    if plan.get("empty_synced") and isinstance(prepared_roots.get("synced"), dict):
        prepared_roots["synced"] = empty_root(prepared_roots["synced"], now)

    out.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(prepared, ensure_ascii=False, indent=3) + "\n").encode("utf-8")
    atomic_write(out, payload)
    out.chmod(0o600)

    old_leaves: list[tuple[str, str, str]] = []
    new_leaves: list[tuple[str, str, str]] = []
    collect_leaves(bar, [], old_leaves)
    collect_leaves(new_bar, [], new_leaves)
    stats = leaf_stats(old_leaves, new_leaves)
    digest = hashlib.sha256(payload).hexdigest()
    manifest = {
        "scheme": plan.get("scheme") or "",
        "top_level": top_level_folders(new_bar),
        "kept": stats["kept"],
        "moved": stats["moved"],
        "removed": stats["removed"],
        "added": stats["added"],
        "prepared": out.name,
        "prepared_sha256": digest,
        "source": str(src),
    }
    manifest_path = out.parent / "manifest.json"
    atomic_write(
        manifest_path,
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    print(f"wrote {out}")
    print(f"manifest={manifest_path}")
    print(
        f"kept={stats['kept']} added={stats['added']} removed={stats['removed']} "
        f"moved={stats['moved']} renamed={stats['renamed']}"
    )
    print("top_level_folders=" + (", ".join(top_level_folders(new_bar)) or "(none)"))
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
        description="Inspect, emit, diff, or copy Chrome bookmark files after Chrome quits."
    )
    add_common_args(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect", help="Print profile, running state, and folder counts.")
    add_common_args(inspect, subcommand=True)
    inspect.set_defaults(func=cmd_inspect)

    emit = sub.add_parser("emit", help="Build a prepared Bookmarks JSON from a classification plan.")
    emit.add_argument("--src", required=True, help="Original Bookmarks JSON (raw archive or live copy).")
    emit.add_argument("--plan", required=True, help="Classification plan JSON.")
    emit.add_argument("--out", required=True, help="Prepared Bookmarks JSON to write.")
    add_common_args(emit, subcommand=True)
    emit.set_defaults(func=cmd_emit)

    diff = sub.add_parser("diff", help="Compare a live Bookmarks file with a prepared tree.")
    diff.add_argument("--old", required=True, help="Current Bookmarks JSON (live or a backup).")
    diff.add_argument("--new", required=True, help="Prepared Bookmarks JSON.")
    add_common_args(diff, subcommand=True)
    diff.set_defaults(func=cmd_diff)

    write = sub.add_parser("write", help="Copy prepared JSON onto the live profile.")
    write.add_argument("--src", required=True, help="Prepared Bookmarks JSON path.")
    write.add_argument(
        "--allow-empty-roots",
        action="store_true",
        help="Allow writeback when other or synced would drop to 0 bookmarks.",
    )
    add_common_args(write, subcommand=True)
    write.set_defaults(func=cmd_write)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
