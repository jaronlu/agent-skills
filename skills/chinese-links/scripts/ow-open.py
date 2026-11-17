#!/usr/bin/env python3
"""把 OpenWorker 卡片里的百分号编码路径解码、定位到真实文件。

支持三类粘贴内容：
  1. 编码后的相对路径（可含子目录），如 2026.11.10%E5%8D%8E.../%E9%99%86....pdf
  2. 编码后的文件名，如 %E5%8D%8E...review_20....md
  3. 完整 URL / 绝对路径

搜索根：默认 ~/OpenWorker 与当前目录（当前目录为家目录或 / 时不加入）；--root 可多次指定。
默认只解析并打印路径，加 --open 才真正打开；精确命中多个时全部列出、不自动选中。
"""

import argparse
import os
import subprocess
import sys
import unicodedata
import urllib.parse

SKIP_DIRS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'Library', '.obsidian', '.workbuddy'}


def decode_token(token):
    """解码卡片里的编码串。最多解两次：卡片可能是双重编码。"""
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
    """从粘贴内容里取出路径。只对 file:// 和 http(s):// 去掉 query、fragment；
    裸文件名里的 ? 和 # 原样保留，因为它们可能是文件名的一部分。"""
    s = token.strip().strip('"\'')
    if s.startswith(('file://', 'http://', 'https://')):
        for sep in ('#', '?'):
            if sep in s:
                s = s.split(sep, 1)[0]
    if s.startswith('file://'):
        s = s[len('file://'):]
    out = decode_token(s).rstrip('/')
    # 单个 '/' 之外的绝对路径保留，交给 search 直接判断
    if out in ('', '/'):
        return ''
    return out


def norm_parts(rel):
    """归一化到 NFC 分量元组，兼容 macOS 的 NFD 分解。"""
    return tuple(unicodedata.normalize('NFC', p) for p in rel.split('/') if p)


def is_ascii(s):
    return all(32 <= ord(c) < 127 for c in s)


def walk_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in SKIP_DIRS]
        for fn in filenames:
            if fn.startswith('.'):
                continue
            yield os.path.join(dirpath, fn)


def search(roots, target_rel):
    """先查绝对/直接路径，再按路径后缀匹配。返回 (精确命中, 相近提示)。"""
    if os.path.isabs(target_rel):
        # 绝对路径只做直接判断，不做后缀搜索，避免误命中同名文件
        return ([target_rel], []) if os.path.isfile(target_rel) else ([], [])

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
    ap = argparse.ArgumentParser(description='解码 OpenWorker 卡片链接并定位真实文件')
    ap.add_argument('token', nargs='?', help='卡片里粘贴的编码串、相对路径、URL 或文件名')
    ap.add_argument('--open', action='store_true', help='定位后真的用默认程序打开')
    ap.add_argument('--root', action='append', default=None,
                    help='搜索根，可多次指定；默认 ~/OpenWorker 与当前目录')
    ap.add_argument('--list', action='store_true', help='列出各搜索根下所有非 ASCII 文件名')
    ap.add_argument('--session', help='只在 ~/OpenWorker 的指定会话 uuid 里找')
    args = ap.parse_args()

    if args.root:
        roots = args.root
    else:
        roots = [os.path.expanduser('~/OpenWorker')]
        # 在家目录或文件系统根下运行时不把当前目录作为搜索根，避免全盘遍历
        cwd = os.path.realpath(os.getcwd())
        if cwd not in (os.path.realpath(os.path.expanduser('~')), os.path.sep):
            roots.append(cwd)
    roots = [os.path.abspath(r) for r in roots]
    missing = [r for r in roots if not os.path.isdir(r)]
    for r in missing:
        print(f'搜索根不存在，已跳过：{r}', file=sys.stderr)
    roots = [r for r in roots if r not in missing]
    if not roots:
        return 1

    if args.session:
        roots = [os.path.join(r, args.session) for r in roots
                 if os.path.isdir(os.path.join(r, args.session))]
        if not roots:
            print(f'会话不存在：{args.session}', file=sys.stderr)
            return 1

    if args.list:
        items = [(p, os.path.getmtime(p)) for r in roots for p in walk_files(r)
                 if not is_ascii(os.path.basename(p))]
        if not items:
            print('没有非 ASCII 文件名')
            return 0
        items.sort(key=lambda x: x[1], reverse=True)
        for p, _ in items[:30]:
            print(p)
        if len(items) > 30:
            print(f'... 共 {len(items)} 个，只列最近 30 个')
        return 0

    if not args.token:
        ap.print_help()
        return 2

    target = clean(args.token)
    if not target:
        print('没有解析出路径', file=sys.stderr)
        return 1

    hits, loose = search(roots, target)
    if not hits:
        print(f'未找到：{target}', file=sys.stderr)
        if loose:
            print('名字相近的非 ASCII 文件：', file=sys.stderr)
            for p in loose:
                print(f'  {p}', file=sys.stderr)
        return 1

    hits = sorted(set(hits))
    if len(hits) > 1:
        print(f'命中 {len(hits)} 个，全部列出，未自动选择：')
        for p in hits:
            print(p)
        if args.open:
            print('命中多个时不打开；请用 --root 缩小范围。', file=sys.stderr)
            return 1
        return 0

    print(hits[0])
    if args.open:
        return subprocess.run(['open', hits[0]]).returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
