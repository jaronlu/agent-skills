#!/usr/bin/env python3
"""Detect and fix Chinese punctuation and typography issues in UTF-8 text.

The default mode is a dry run: findings and a unified diff are printed and
nothing is written. Pass ``--apply`` to rewrite files atomically after the user
confirms the proposed diff.

Exit codes:
    0  no findings, or every fix was applied and nothing needs review
    1  findings remain (dry run), or review/skipped items remain after apply
    2  usage, I/O, or encoding error
"""

from __future__ import annotations

import argparse
import difflib
import html
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

CJK_RANGES = "\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
CJK_RE = re.compile(f"[{CJK_RANGES}]")
ASCII_ALNUM_RE = re.compile(r"[A-Za-z0-9]")

FULLWIDTH_MAP = {",": "，", ".": "。", ";": "；", ":": "：", "?": "？", "!": "！"}
CLOSING_PUNCT = "，。；：、？！）】》」』"
OPENING_PUNCT = "（【《「『"
QUOTE_OPEN = "“‘"
QUOTE_CLOSE = "”’"
CLOSE_TO_OPEN = {"”": "“", "’": "‘"}
OPEN_TO_CLOSE = {"“": "”", "‘": "’"}
BRACKET_PAIRS = {"（": "）", "【": "】", "《": "》", "〈": "〉", "「": "」", "『": "』"}
BRACKET_CLOSERS = set(BRACKET_PAIRS.values())

ZERO_WIDTH_FIX = {"\u200b": "零宽空格", "\ufeff": "BOM / 零宽不换行符"}
INVISIBLE_REVIEW = {
    "\u200c": "零宽非连接符（部分文字系统中有意义）",
    "\u200d": "零宽连接符（emoji 序列中有意义）",
    "\u2060": "词连接符",
    "\u00ad": "软连字符",
    "\u00a0": "不间断空格",
}
INVISIBLE_CHARS = set(ZERO_WIDTH_FIX) | set(INVISIBLE_REVIEW)

MOJIBAKE_MARKERS = (
    "\ufffd",
    "锟斤拷",
    "烫烫烫",
    "屯屯屯",
    "Ã",
    "Â",
    "â€",
    "ï¼",
    "ã€",
    "å¤",
    "æ–",
    "æ‰",
    "çš„",
)

ENTITY_RE = re.compile(r"&(?:#[0-9]{1,6}|#[xX][0-9A-Fa-f]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});")
URL_RE = re.compile(r"(?:https?|ftp|file)://[^\s<>\"'“”‘’]+")
INLINE_CODE_RE = re.compile(r"(?<!`)(`+)(?!`)([^\n]+?)(?<!`)\1(?!`)")
FENCE_OPEN_RE = re.compile(r"^(\`{3,}|~{3,})")

REPEAT_FULLWIDTH_RE = re.compile(r"([，。；：、？！])\1+")
REPEAT_ASCII_RE = re.compile(r"([,;:?!])\1+")
ELLIPSIS_RE = re.compile(r"(?<!\.)\.\.\.(?!\.)")
SPACE_BEFORE_CLOSE_RE = re.compile(
    rf"(?<=[{CJK_RANGES}“”‘’）】》」』])[ \t]+(?=[{CLOSING_PUNCT}])"
)
SPACE_AFTER_OPEN_RE = re.compile(
    rf"(?<=[{OPENING_PUNCT}])[ \t]+(?=[{CJK_RANGES}])"
)

DEFAULT_SUFFIXES = {".md", ".markdown", ".mdx", ".txt", ".rst", ".csv", ".tsv"}
MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdx"}
HTML_SUFFIXES = {".html", ".htm", ".xml"}

PROFILE_RANK = {"minimal": 1, "standard": 2, "strict": 3}
PRIORITY_ZERO_WIDTH = 1
PRIORITY_QUOTE = 2
PRIORITY_PUNCTUATION = 3
PRIORITY_SPACE = 4
PRIORITY_INSERT = 5


@dataclass
class Finding:
    rule: str
    severity: str
    offset: int
    message: str
    edit: tuple[int, int, str] | None = None
    priority: int = 99


@dataclass
class FileResult:
    label: str
    path: Path | None
    findings: list[Finding] = field(default_factory=list)
    original: str = ""
    fixed: str = ""
    diff: str = ""
    skipped: str = ""
    wrote: bool = False


@dataclass
class Summary:
    fix: int = 0
    review: int = 0
    skipped: int = 0
    files_scanned: int = 0
    files_changed: int = 0


def line_col(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    last_newline = text.rfind("\n", 0, offset)
    return line, offset - last_newline


def profile_allows(profile: str, needed: str) -> bool:
    return PROFILE_RANK[profile] >= PROFILE_RANK[needed]


def is_cjk(char: str) -> bool:
    return bool(CJK_RE.match(char))


def prev_nonspace(text: str, index: int) -> tuple[int, str] | None:
    """Return the nearest non-blank character before ``index``, or ``None``."""
    for pos in range(index - 1, -1, -1):
        if text[pos] not in " \t":
            return pos, text[pos]
    return None


def next_nonspace(text: str, index: int) -> tuple[int, str] | None:
    """Return the nearest non-blank character after ``index``, or ``None``."""
    for pos in range(index + 1, len(text)):
        if text[pos] not in " \t":
            return pos, text[pos]
    return None


def near_cjk(text: str, index: int, radius: int = 2) -> bool:
    start = max(0, index - radius)
    end = min(len(text), index + radius + 1)
    return any(is_cjk(text[pos]) for pos in range(start, end) if pos != index)


def mask_range(mask: bytearray, start: int, end: int) -> None:
    if end > start:
        mask[start:end] = b"\x01" * (end - start)


def build_mask(text: str, markdown: bool) -> bytearray:
    """Mark regions that rules must not edit: URLs, code, and frontmatter."""
    mask = bytearray(len(text))
    for match in URL_RE.finditer(text):
        mask_range(mask, match.start(), match.end())
    if not markdown:
        return mask

    # A leading BOM must not hide the frontmatter: ZW001 removes it in the same
    # pass, and edits inside frontmatter would otherwise skip the protection.
    frontmatter = re.match(r"\ufeff?---[ \t]*\r?\n", text)
    if frontmatter:
        closing = re.search(r"^---[ \t]*$", text[frontmatter.end() :], re.MULTILINE)
        if closing:
            start = 1 if text.startswith("\ufeff") else 0
            mask_range(mask, start, frontmatter.end() + closing.end())

    offset = 0
    fence: tuple[str, int] | None = None
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if fence:
            mask_range(mask, offset, offset + len(line))
            marker, length = fence
            if re.fullmatch(rf"{re.escape(marker)}{{{length},}}[ \t]*\r?\n?", stripped):
                fence = None
        else:
            opener = FENCE_OPEN_RE.match(stripped)
            if opener:
                marker = opener.group(1)
                fence = (marker[0], len(marker))
                mask_range(mask, offset, offset + len(line))
        offset += len(line)

    for match in INLINE_CODE_RE.finditer(text):
        mask_range(mask, match.start(), match.end())
    return mask


def add_finding(
    findings: list[Finding],
    mask: bytearray,
    rule: str,
    severity: str,
    start: int,
    end: int,
    message: str,
    replacement: str | None = None,
    priority: int = 99,
) -> None:
    if any(mask[pos] for pos in range(start, end)):
        return
    edit = None
    if replacement is not None:
        edit = (start, end, replacement)
    findings.append(Finding(rule, severity, start, message, edit, priority))


def check_zero_width(text: str, mask: bytearray, findings: list[Finding]) -> None:
    for index, char in enumerate(text):
        if mask[index]:
            continue
        if char in ZERO_WIDTH_FIX:
            add_finding(
                findings,
                mask,
                "ZW001",
                "fix",
                index,
                index + 1,
                f"删除{ZERO_WIDTH_FIX[char]}",
                "",
                PRIORITY_ZERO_WIDTH,
            )
        elif char in INVISIBLE_REVIEW:
            add_finding(
                findings,
                mask,
                "ZW002",
                "review",
                index,
                index + 1,
                f"发现{INVISIBLE_REVIEW[char]}，确认是否有意保留",
            )


def is_measurement_mark(text: str, index: int) -> bool:
    """A quote right after a digit that ends the line is a unit mark, not a quote."""
    if index == 0 or not text[index - 1].isdigit():
        return False
    nxt = text[index + 1 : index + 2]
    return not nxt or nxt in " \t\r\n"


def quote_closes_previous(text: str, opener_pos: int, index: int) -> bool:
    """Decide whether an opening quote is really a mis-typed closing quote.

    Flipping only makes sense when the quote follows content in the same
    paragraph. A paragraph break, a line start, or a colon normally introduces a
    new quotation, so the earlier opener is the unclosed one and the text stays
    untouched for review.
    """
    if re.search(r"\n[ \t]*\r?\n", text[opener_pos + 1 : index]):
        return False
    previous = prev_nonspace(text, index)
    if previous is None or previous[1] in "\r\n：:":
        return False
    return True


def check_quotes(text: str, mask: bytearray, findings: list[Finding]) -> None:
    """Pair curly quotes with a stack and repair unambiguous direction errors."""
    stacks: dict[str, list[int]] = {"“": [], "‘": []}
    for index, char in enumerate(text):
        if mask[index]:
            continue
        if char in QUOTE_OPEN:
            opener = char
            if not stacks[opener] and is_measurement_mark(text, index):
                continue  # Likely an inch mark, not a quotation.
            if stacks[opener]:
                top = stacks[opener][-1]
                if index > top + 1 and quote_closes_previous(text, top, index):
                    add_finding(
                        findings,
                        mask,
                        "QT001",
                        "fix",
                        index,
                        index + 1,
                        f"引号方向：此处应为闭引号 {OPEN_TO_CLOSE[opener]}",
                        OPEN_TO_CLOSE[opener],
                        PRIORITY_QUOTE,
                    )
                    stacks[opener].pop()
                else:
                    message = (
                        "同型引号连续出现，无法安全判断方向"
                        if index <= top + 1
                        else "前一个开引号未闭合，此处又出现开引号，无法安全判断方向"
                    )
                    add_finding(
                        findings,
                        mask,
                        "QT002",
                        "review",
                        index,
                        index + 1,
                        message,
                    )
                    stacks[opener].append(index)
            else:
                stacks[opener].append(index)
            continue

        if char in QUOTE_CLOSE:
            opener = CLOSE_TO_OPEN[char]
            other = "‘" if opener == "“" else "“"
            if not stacks[opener] and is_measurement_mark(text, index):
                continue  # Likely an inch mark, not a quotation.
            if stacks[opener]:
                if stacks[other] and stacks[other][-1] > stacks[opener][-1]:
                    add_finding(
                        findings,
                        mask,
                        "QT003",
                        "review",
                        index,
                        index + 1,
                        "引号嵌套顺序交叉，未自动修改",
                    )
                    stacks[opener].pop()
                else:
                    stacks[opener].pop()
                continue

            previous = prev_nonspace(text, index)
            following = next_nonspace(text, index)
            at_boundary = (
                previous is None
                or previous[1] in "\r\n"
                or previous[1] in OPENING_PUNCT
            )
            if at_boundary and following is not None and is_cjk(following[1]):
                add_finding(
                    findings,
                    mask,
                    "QT001",
                    "fix",
                    index,
                    index + 1,
                    f"引号方向：此处应为开引号 {opener}",
                    opener,
                    PRIORITY_QUOTE,
                )
                stacks[opener].append(index)
            elif near_cjk(text, index):
                add_finding(
                    findings,
                    mask,
                    "QT002",
                    "review",
                    index,
                    index + 1,
                    "孤立闭引号，缺少可配对的开始引号",
                )

    for opener, positions in stacks.items():
        for position in positions:
            add_finding(
                findings,
                mask,
                "QT002",
                "review",
                position,
                position + 1,
                f"开始引号 {opener} 未闭合，未自动补全",
            )


def check_brackets(text: str, mask: bytearray, findings: list[Finding]) -> None:
    stack: list[tuple[str, int]] = []
    for index, char in enumerate(text):
        if mask[index]:
            continue
        if char in BRACKET_PAIRS:
            stack.append((char, index))
            continue
        if char not in BRACKET_CLOSERS:
            continue
        if not stack:
            add_finding(
                findings, mask, "BR001", "review", index, index + 1, f"多余的闭括号 {char}"
            )
            continue
        opener, opener_pos = stack[-1]
        if BRACKET_PAIRS[opener] == char:
            stack.pop()
            continue
        match_index = None
        for candidate in range(len(stack) - 1, -1, -1):
            if BRACKET_PAIRS[stack[candidate][0]] == char:
                match_index = candidate
                break
        if match_index is None:
            add_finding(
                findings,
                mask,
                "BR001",
                "review",
                index,
                index + 1,
                f"闭括号 {char} 与最近的 {opener} 不匹配",
            )
            continue
        line, column = line_col(text, opener_pos)
        add_finding(
            findings,
            mask,
            "BR002",
            "review",
            index,
            index + 1,
            f"括号交叉：第 {line} 行第 {column} 列的 {stack[match_index][0]} 跨过内层括号闭合",
        )
        del stack[match_index:]

    for opener, position in stack:
        add_finding(
            findings,
            mask,
            "BR003",
            "review",
            position,
            position + 1,
            f"开括号 {opener} 未闭合，未自动补全",
        )


def check_fullwidth_punctuation(
    text: str, mask: bytearray, findings: list[Finding], profile: str
) -> None:
    for index, char in enumerate(text):
        if mask[index] or char not in FULLWIDTH_MAP:
            continue
        previous = prev_nonspace(text, index)
        if previous is None or not is_cjk(previous[1]):
            continue
        if char == ".":
            nxt = text[index + 1 : index + 2]
            if nxt == "." or (nxt and ASCII_ALNUM_RE.match(nxt)):
                continue
        if char in ",;:?!" and (
            (index + 1 < len(text) and text[index + 1] == char)
            or (index > 0 and text[index - 1] == char)
        ):
            continue  # Repeated ASCII punctuation is handled by PU002.
        severity = "fix" if profile_allows(profile, "standard") else "review"
        replacement = FULLWIDTH_MAP[char] if severity == "fix" else None
        add_finding(
            findings,
            mask,
            "FW001",
            severity,
            index,
            index + 1,
            f"中文语境中的半角标点 {char} 建议改为 {FULLWIDTH_MAP[char]}",
            replacement,
            PRIORITY_PUNCTUATION,
        )


def check_repeated_punctuation(
    text: str, mask: bytearray, findings: list[Finding], profile: str
) -> None:
    for match in REPEAT_FULLWIDTH_RE.finditer(text):
        if any(mask[pos] for pos in range(match.start(), match.end())):
            continue
        char = match.group(1)
        severity = "fix" if profile_allows(profile, "standard") else "review"
        add_finding(
            findings,
            mask,
            "PU001",
            severity,
            match.start(),
            match.end(),
            f"重复标点 {match.group(0)} 建议合并为 {char}",
            char if severity == "fix" else None,
            PRIORITY_PUNCTUATION,
        )

    for match in REPEAT_ASCII_RE.finditer(text):
        if any(mask[pos] for pos in range(match.start(), match.end())):
            continue
        previous = prev_nonspace(text, match.start())
        if previous is None or not is_cjk(previous[1]):
            continue
        target = FULLWIDTH_MAP[match.group(1)]
        severity = "fix" if profile_allows(profile, "standard") else "review"
        add_finding(
            findings,
            mask,
            "PU002",
            severity,
            match.start(),
            match.end(),
            f"中文语境中的重复半角标点 {match.group(0)} 建议合并为 {target}",
            target if severity == "fix" else None,
            PRIORITY_PUNCTUATION,
        )


def check_ellipsis(
    text: str, mask: bytearray, findings: list[Finding], profile: str
) -> None:
    for match in ELLIPSIS_RE.finditer(text):
        if any(mask[pos] for pos in range(match.start(), match.end())):
            continue
        previous = prev_nonspace(text, match.start())
        if previous is None or not is_cjk(previous[1]):
            continue
        severity = "fix" if profile_allows(profile, "standard") else "review"
        add_finding(
            findings,
            mask,
            "PU003",
            severity,
            match.start(),
            match.end(),
            "中文省略号建议使用 ……（两个 U+2026）",
            "……" if severity == "fix" else None,
            PRIORITY_PUNCTUATION,
        )


def check_spaces(
    text: str, mask: bytearray, findings: list[Finding], profile: str
) -> None:
    for pattern, message in (
        (SPACE_BEFORE_CLOSE_RE, "删除中文标点前的多余空格"),
        (SPACE_AFTER_OPEN_RE, "删除开标点后的多余空格"),
    ):
        for match in pattern.finditer(text):
            start, end = match.span()
            context_start = max(0, start - 1)
            if any(mask[pos] for pos in range(context_start, end)):
                continue
            severity = "fix" if profile_allows(profile, "standard") else "review"
            add_finding(
                findings,
                mask,
                "SP001",
                severity,
                start,
                end,
                message,
                "" if severity == "fix" else None,
                PRIORITY_SPACE,
            )

    for index in range(len(text) - 1):
        if mask[index] or mask[index + 1]:
            continue
        left, right = text[index], text[index + 1]
        pair = (is_cjk(left) and ASCII_ALNUM_RE.match(right)) or (
            ASCII_ALNUM_RE.match(left) and is_cjk(right)
        )
        if not pair:
            continue
        severity = "fix" if profile_allows(profile, "strict") else "review"
        add_finding(
            findings,
            mask,
            "SP002",
            severity,
            index + 1,
            index + 1,
            "中文与拉丁字母/数字之间建议加一个空格",
            " " if severity == "fix" else None,
            PRIORITY_INSERT,
        )


def check_entities(
    text: str,
    mask: bytearray,
    findings: list[Finding],
    profile: str,
    fix_entities: bool,
    html_like: bool,
) -> None:
    for match in ENTITY_RE.finditer(text):
        if any(mask[pos] for pos in range(match.start(), match.end())):
            continue
        decoded = html.unescape(match.group(0))
        if decoded == match.group(0):
            continue
        if any(char in INVISIBLE_CHARS for char in decoded):
            add_finding(
                findings,
                mask,
                "EN001",
                "review",
                match.start(),
                match.end(),
                f"HTML 实体残留 {match.group(0)} → {decoded!r}；解码后是不可见字符，需人工确认",
            )
            continue
        auto = (fix_entities or profile_allows(profile, "strict")) and not html_like
        severity = "fix" if auto else "review"
        if html_like:
            note = "HTML/XML 中需按上下文处理"
        elif auto:
            note = "将解码为字面字符"
        else:
            note = "请确认是否应保留字面实体"
        add_finding(
            findings,
            mask,
            "EN001",
            severity,
            match.start(),
            match.end(),
            f"HTML 实体残留 {match.group(0)} → {decoded}；{note}",
            decoded if severity == "fix" else None,
            PRIORITY_PUNCTUATION,
        )


def check_mojibake(text: str, mask: bytearray, findings: list[Finding]) -> None:
    offset = 0
    for line in text.splitlines(keepends=True):
        for marker in MOJIBAKE_MARKERS:
            index = line.find(marker)
            if index < 0:
                continue
            absolute = offset + index
            if any(mask[pos] for pos in range(absolute, absolute + len(marker))):
                continue
            add_finding(
                findings,
                mask,
                "MO001",
                "review",
                absolute,
                absolute + len(marker),
                f"疑似乱码（{marker}）：确认原始编码后转换，不自动还原",
            )
            break
        offset += len(line)


def analyze(
    text: str,
    profile: str,
    *,
    markdown: bool,
    fix_entities: bool,
    html_like: bool,
) -> tuple[list[Finding], str]:
    mask = build_mask(text, markdown)
    findings: list[Finding] = []
    check_zero_width(text, mask, findings)
    check_quotes(text, mask, findings)
    check_brackets(text, mask, findings)
    check_fullwidth_punctuation(text, mask, findings, profile)
    check_repeated_punctuation(text, mask, findings, profile)
    check_ellipsis(text, mask, findings, profile)
    check_spaces(text, mask, findings, profile)
    check_entities(text, mask, findings, profile, fix_entities, html_like)
    check_mojibake(text, mask, findings)

    edits: list[tuple[tuple[int, int, str], Finding]] = []
    for finding in findings:
        edit = finding.edit
        if finding.severity == "fix" and edit is not None:
            edits.append((edit, finding))
    edits.sort(
        key=lambda item: (item[0][0], -(item[0][1] - item[0][0]), item[1].priority)
    )

    selected: list[tuple[tuple[int, int, str], Finding]] = []
    last_end = -1
    for edit, finding in edits:
        start, end, _ = edit
        if start < last_end:
            finding.severity = "review"
            finding.edit = None
            finding.message += "（与更高优先级修复重叠，未自动改）"
            continue
        selected.append((edit, finding))
        last_end = end

    pieces: list[str] = []
    cursor = 0
    for (start, end, replacement), _ in sorted(selected, key=lambda item: item[0][0]):
        pieces.append(text[cursor:start])
        pieces.append(replacement)
        cursor = end
    pieces.append(text[cursor:])
    fixed = "".join(pieces)
    findings.sort(key=lambda finding: (finding.offset, finding.rule))
    return findings, fixed


def unified_diff(original: str, fixed: str, label: str) -> str:
    if original == fixed:
        return ""
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=label,
            tofile=f"{label} (fixed)",
        )
    )


def decode_file(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        raise ValueError("UTF-16 file; convert to UTF-8 first")
    if b"\x00" in data:
        raise ValueError("binary or NUL-containing file")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"not UTF-8 (invalid byte at {exc.start})") from exc


def write_text(path: Path, text: str) -> None:
    status = path.stat()
    handle, temporary = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, status.st_mode)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def process_text(
    text: str,
    label: str,
    profile: str,
    *,
    markdown: bool,
    fix_entities: bool,
    html_like: bool,
) -> FileResult:
    findings, fixed = analyze(
        text, profile, markdown=markdown, fix_entities=fix_entities, html_like=html_like
    )
    return FileResult(
        label=label,
        path=None,
        findings=findings,
        original=text,
        fixed=fixed,
        diff=unified_diff(text, fixed, label),
    )


def collect_paths(raw_paths: list[str], extensions: set[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in raw_paths:
        path = Path(raw)
        if not path.exists():
            raise ValueError(f"path not found: {raw}")
        if path.is_dir():
            for candidate in sorted(path.rglob("*")):
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                if any(part.startswith(".") for part in candidate.relative_to(path).parts):
                    continue
                if candidate.suffix.lower() in extensions:
                    paths.append(candidate)
        else:
            paths.append(path)
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def render_text(
    results: list[FileResult],
    summary: Summary,
    profile: str,
    apply: bool,
    max_issues: int,
) -> str:
    mode = "apply" if apply else "dry-run"
    lines = [f"chinese-text-fixer · profile={profile} · {mode}", ""]
    for result in results:
        if result.skipped:
            lines.append(f"{result.label}: skipped — {result.skipped}")
            continue
        if not result.findings:
            continue
        for finding in result.findings[:max_issues]:
            line, column = line_col(result.original, finding.offset)
            lines.append(f"{result.label}:{line}:{column}  [{finding.rule} {finding.severity}] {finding.message}")
        hidden = len(result.findings) - max_issues
        if hidden > 0:
            lines.append(f"{result.label}: ... {hidden} more finding(s) not shown")
        if result.diff:
            lines.append("")
            lines.append(result.diff.rstrip("\n"))
        lines.append("")
    if len(results) > 1 or any(result.findings or result.skipped for result in results):
        lines.append(
            f"summary: {summary.fix} fix, {summary.review} review, "
            f"{summary.skipped} skipped file(s); "
            f"{summary.files_changed} of {summary.files_scanned} file(s) with fixes"
        )
    else:
        lines.append(f"summary: clean; {summary.files_scanned} file(s) scanned")
    return "\n".join(lines).rstrip("\n") + "\n"


def build_json(
    results: list[FileResult],
    summary: Summary,
    profile: str,
    apply: bool,
    max_issues: int,
) -> str:
    files: list[dict[str, object]] = []
    payload = {
        "tool": "chinese-text-fixer",
        "profile": profile,
        "apply": apply,
        "summary": summary.__dict__,
        "files": files,
    }
    for result in results:
        issues = []
        for finding in result.findings[:max_issues]:
            line, column = line_col(result.original, finding.offset)
            issues.append(
                {
                    "rule": finding.rule,
                    "severity": finding.severity,
                    "line": line,
                    "column": column,
                    "message": finding.message,
                }
            )
        files.append(
            {
                "path": result.label,
                "skipped": result.skipped or None,
                "changed": result.original != result.fixed,
                "wrote": result.wrote,
                "issues": issues,
                "issue_count": len(result.findings),
                "diff": result.diff,
            }
        )
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fix_text.py",
        description="Detect and fix Chinese punctuation and typography issues in UTF-8 text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 fix_text.py draft.md                 # dry run: findings + diff\n"
            "  python3 fix_text.py draft.md --apply         # write after confirmation\n"
            "  python3 fix_text.py --text \"“数据怎么流转“\"  # check inline text\n"
            "  printf '%s' \"$TEXT\" | python3 fix_text.py - # check stdin\n"
            "  python3 fix_text.py docs/ --ext .md --format json\n"
        ),
    )
    parser.add_argument("paths", nargs="*", help="Files or directories; use - for stdin")
    parser.add_argument("--text", help="Inline text to analyze instead of files")
    parser.add_argument("--apply", action="store_true", help="Write fixes atomically (files only)")
    parser.add_argument(
        "--profile",
        choices=("minimal", "standard", "strict"),
        default="standard",
        help="How much to auto-fix: minimal, standard (default), or strict",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--fixed",
        action="store_true",
        help="Print only the corrected text (single input, no --apply)",
    )
    parser.add_argument(
        "--fix-entities",
        action="store_true",
        help="Decode HTML entities in non-HTML input (default: report only)",
    )
    parser.add_argument(
        "--ext",
        action="append",
        default=[],
        help=f"Extra suffix for directory scans, e.g. --ext .srt (default: {', '.join(sorted(DEFAULT_SUFFIXES))})",
    )
    parser.add_argument(
        "--no-skip-code",
        action="store_true",
        help="Also edit Markdown code fences, inline code, and frontmatter",
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=200,
        help="Maximum findings printed per file (default: 200)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    inputs = list(args.paths)
    if args.text is not None and inputs:
        parser.error("use either --text or paths, not both")
    if args.text is None and not inputs:
        parser.error("provide a file, a directory, --text, or - for stdin")
    if args.apply and (args.text is not None or "-" in inputs):
        parser.error("--apply only works with file paths")
    if args.fixed and args.apply:
        parser.error("--fixed cannot be combined with --apply")
    if args.fixed and args.format == "json":
        parser.error("--fixed prints plain text; drop --format json")
    if args.max_issues < 0:
        parser.error("--max-issues must be non-negative")

    extensions = set(DEFAULT_SUFFIXES)
    for suffix in args.ext:
        extensions.add(suffix if suffix.startswith(".") else f".{suffix}")

    results: list[FileResult] = []
    summary = Summary()
    error = False
    try:
        if args.text is not None:
            summary.files_scanned += 1
            results.append(
                process_text(
                    args.text,
                    "<text>",
                    args.profile,
                    markdown=not args.no_skip_code,
                    fix_entities=args.fix_entities,
                    html_like=False,
                )
            )
        elif inputs == ["-"]:
            summary.files_scanned += 1
            data = sys.stdin.buffer.read()
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(f"stdin is not UTF-8 (invalid byte at {exc.start})") from exc
            results.append(
                process_text(
                    text,
                    "<stdin>",
                    args.profile,
                    markdown=not args.no_skip_code,
                    fix_entities=args.fix_entities,
                    html_like=False,
                )
            )
        else:
            for path in collect_paths(inputs, extensions):
                summary.files_scanned += 1
                if path.is_symlink():
                    summary.skipped += 1
                    results.append(
                        FileResult(
                            label=str(path),
                            path=path,
                            skipped="symbolic link; edit the target file directly",
                        )
                    )
                    continue
                try:
                    text = decode_file(path)
                except (OSError, ValueError) as exc:
                    summary.skipped += 1
                    results.append(
                        FileResult(label=str(path), path=path, skipped=str(exc))
                    )
                    continue
                suffix = path.suffix.lower()
                result = process_text(
                    text,
                    str(path),
                    args.profile,
                    markdown=suffix in MARKDOWN_SUFFIXES and not args.no_skip_code,
                    fix_entities=args.fix_entities,
                    html_like=suffix in HTML_SUFFIXES,
                )
                result.path = path
                if result.original != result.fixed:
                    if args.apply:
                        try:
                            write_text(path, result.fixed)
                        except OSError as exc:
                            print(f"error: cannot write {path}: {exc}", file=sys.stderr)
                            error = True
                            continue
                        result.wrote = True
                results.append(result)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not results:
        print(
            "error: no files matched; check the path or the --ext suffixes",
            file=sys.stderr,
        )
        return 2

    for result in results:
        summary.fix += sum(1 for finding in result.findings if finding.severity == "fix")
        summary.review += sum(1 for finding in result.findings if finding.severity == "review")
        if result.original != result.fixed:
            summary.files_changed += 1

    if args.fixed:
        if len(results) != 1:
            print("error: --fixed requires exactly one input", file=sys.stderr)
            return 2
        if results[0].skipped:
            print(f"error: {results[0].label} skipped: {results[0].skipped}", file=sys.stderr)
            return 2
        sys.stdout.write(results[0].fixed)
        return 1 if any(f.severity == "review" for f in results[0].findings) or results[0].skipped else 0

    if args.format == "json":
        sys.stdout.write(build_json(results, summary, args.profile, args.apply, args.max_issues))
    else:
        sys.stdout.write(render_text(results, summary, args.profile, args.apply, args.max_issues))

    if error:
        return 2
    if args.apply:
        return 1 if summary.review or summary.skipped else 0
    return 1 if summary.fix or summary.review or summary.skipped else 0


if __name__ == "__main__":
    raise SystemExit(main())
