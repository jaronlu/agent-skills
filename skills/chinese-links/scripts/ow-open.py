#!/usr/bin/env python3
"""Decode percent-encoded paths from OpenWorker file cards and locate the real file.

Accepted input:
  1. An encoded relative path, possibly with subdirectories,
     e.g. 2026.11.10%E5%8D%8E.../%E9%99%86....pdf
  2. An encoded file name, e.g. %E5%8D%8E...review_20....md
  3. A full URL or an absolute path

Search roots: ~/OpenWorker and the current directory (the current directory is
skipped when it is the home directory or /). --root can be given multiple times.
By default only the resolved path is printed. --open launches the file with the
default app. When several files match, all are listed and none is selected.
"""

import argparse
import os
import subprocess
import sys
import unicodedata
import urllib.parse

SKIP_DIRS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'Library', '.obsidian', '.workbuddy'}

# Only these document types may be opened with --open. Anything else is refused,
# so a name match cannot launch a script, installer, or app bundle.
SAFE_OPEN_EXT = {
    '.pdf', '.md', '.txt', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
    '.csv', '.json', '.rtf', '.pages', '.numbers', '.key', '.png', '.jpg', '.jpeg',
    '.gif', '.webp', '.svg',
}


def decode_token(token):
    """Decode the encoded string from a card. Decodes at most twice, since cards may be double-encoded."""
    out = token
    for _ in range(2):
        if '%' not in out:
            break
        try:
            nxt = urllib.parse.unquote(out, errors='strict')
        except UnicodeDecodeError:
            break
        if nxt == out:
            break
        out = nxt
    return out


def clean(token):
    """Extract the path from pasted input, without decoding it. Strips the query and
    fragment only for file:// and http(s):// URLs. A bare file name keeps ? and #,
    since they may be part of the name."""
    s = token.strip().strip('"\'')
    if s.startswith(('file://', 'http://', 'https://')):
        for sep in ('#', '?'):
            if sep in s:
                s = s.split(sep, 1)[0]
    if s.startswith('file://'):
        s = s[len('file://'):]
    out = s.rstrip('/')
    if out in ('', '/'):
        return ''
    return out


def candidates(raw):
    """Return the raw string first, then its decoded form. A name that really
    contains '%' is found as typed. Encoded card links are found after decoding."""
    out = []
    for c in (raw, decode_token(raw).rstrip('/')):
        if c and c not in out:
            out.append(c)
    return out


def norm_parts(rel):
    """Normalize each path component to NFC, so NFD names from macOS match."""
    return tuple(unicodedata.normalize('NFC', p) for p in rel.split('/') if p)


def is_ascii(s):
    return all(32 <= ord(c) < 127 for c in s)


def walk_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        # Do not descend into hidden dirs, known junk dirs, or app bundles.
        dirnames[:] = [d for d in dirnames
                       if not d.startswith('.') and d not in SKIP_DIRS
                       and not d.endswith(('.app', '.bundle'))]
        for fn in filenames:
            if fn.startswith('.'):
                continue
            yield os.path.join(dirpath, fn)


def search(roots, target_rel):
    """Check the absolute or direct path first, then match by path suffix.
    Returns (exact hits, near-match hints)."""
    if os.path.isabs(target_rel):
        # Absolute paths are checked directly only, with no suffix search, to avoid matching a same-named file by mistake.
        return ([target_rel], []) if os.path.isfile(target_rel) else ([], [])

    # Refuse '.' and '..' so a relative target cannot climb out of a search root.
    if any(p in ('.', '..') for p in target_rel.split('/')):
        return [], []

    want = norm_parts(target_rel)
    exact, loose = [], []
    for root in roots:
        if not os.path.isdir(root):
            continue
        direct = os.path.join(root, *want)
        if os.path.isfile(direct):
            exact.append(os.path.abspath(direct))
            continue
        for p in walk_files(root):
            rel = norm_parts(os.path.relpath(p, root))
            if rel == want or rel[-len(want):] == want:
                exact.append(os.path.abspath(p))
            elif not is_ascii(want[-1]) and \
                    os.path.splitext(want[-1])[0] in unicodedata.normalize('NFC', os.path.basename(p)):
                loose.append(os.path.abspath(p))
    return exact, loose[:5]


def main():
    ap = argparse.ArgumentParser(description='Decode OpenWorker card links and locate the real file')
    ap.add_argument('token', nargs='?', help='Encoded string, relative path, URL, or file name from a card')
    ap.add_argument('--open', action='store_true', help='Open the located file with the default app')
    ap.add_argument('--root', action='append', default=None,
                    help='Search root, repeatable; default ~/OpenWorker and the current directory')
    ap.add_argument('--list', action='store_true', help='List all non-ASCII file names under the search roots')
    ap.add_argument('--session', help='Search only the given session uuid under ~/OpenWorker')
    args = ap.parse_args()

    if args.root:
        roots = args.root
    else:
        roots = [os.path.expanduser('~/OpenWorker')]
        # Skip the current directory as a search root when running from HOME or /, to avoid walking the whole disk.
        cwd = os.path.realpath(os.getcwd())
        if cwd not in (os.path.realpath(os.path.expanduser('~')), os.path.sep):
            roots.append(cwd)
    roots = [os.path.abspath(r) for r in roots]
    missing = [r for r in roots if not os.path.isdir(r)]
    for r in missing:
        print(f'Search root does not exist, skipped: {r}', file=sys.stderr)
    roots = [r for r in roots if r not in missing]
    if not roots:
        return 1

    if args.session:
        roots = [os.path.join(r, args.session) for r in roots
                 if os.path.isdir(os.path.join(r, args.session))]
        if not roots:
            print(f'Session not found: {args.session}', file=sys.stderr)
            return 1

    if args.list:
        items = [(p, os.path.getmtime(p)) for r in roots for p in walk_files(r)
                 if not is_ascii(os.path.basename(p))]
        if not items:
            print('No non-ASCII file names found')
            return 0
        items.sort(key=lambda x: x[1], reverse=True)
        for p, _ in items[:30]:
            print(p)
        if len(items) > 30:
            print(f'... {len(items)} total, showing the 30 most recent')
        return 0

    if not args.token:
        ap.print_help()
        return 2

    target = clean(args.token)
    if not target:
        print('No path could be parsed from the input', file=sys.stderr)
        return 1

    hits, loose = [], []
    targets = candidates(target)
    for t in targets:
        hits, loose = search(roots, t)
        if hits:
            break
    if not hits:
        print(f'Not found: {targets[-1]}', file=sys.stderr)
        if loose:
            print('Similar non-ASCII file names:', file=sys.stderr)
            for p in loose:
                print(f'  {p}', file=sys.stderr)
        return 1

    hits = sorted(set(hits))
    if len(hits) > 1:
        print(f'{len(hits)} matches, all listed, none selected:')
        for p in hits:
            print(p)
        if args.open:
            print('Not opening with multiple matches; narrow the search with --root.', file=sys.stderr)
            return 1
        return 0

    print(hits[0])
    if args.open:
        ext = os.path.splitext(hits[0])[1].lower()
        if ext not in SAFE_OPEN_EXT:
            print(f'Refusing to open {ext or "a file with no extension"}: not on the document allowlist. '
                  'Open it by hand if you trust it.', file=sys.stderr)
            return 1
        return subprocess.run(['open', hits[0]]).returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
