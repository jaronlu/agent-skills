from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path(os.environ.get("LLM_WIKI_ROOT", "~/llm-wiki")).expanduser()
CONFIG_NAME = "llm-wiki.json"
LEGACY_CONFIG_NAME = ".llm-wiki.json"
DEFAULT_FORMAL_GLOBS = (
    "domains/**/*.md",
    "entities/**/*.md",
    "workshop/*/README.md",
    "_meta/topic-map.md",
    "index.md",
    "SCHEMA.md",
    "AGENTS.md",
)
DEFAULT_RAW_GLOBS = ("raw/**/*", "workshop/*/raw/**/*")
DEFAULT_IGNORED_PARTS = frozenset({".git", ".obsidian", ".claude"})


class WikiConfigError(ValueError):
    pass


@dataclass(frozen=True)
class WikiLayout:
    formal: tuple[str, ...]
    raw: tuple[str, ...]
    ignored_parts: frozenset[str]
    path: Path | None = None


class UnsupportedContentError(ValueError):
    pass


def resolve_root(root: str | None) -> Path:
    candidate = Path(root).expanduser() if root else DEFAULT_ROOT
    return candidate.resolve()


def resolve_layout(root: Path, config: str | None = None) -> WikiLayout:
    """Load an optional per-wiki layout, retaining the historical defaults.

    Precedence (highest first):
    1. ``--config`` CLI argument
    2. ``LLM_WIKI_CONFIG`` environment variable
    3. ``<root>/llm-wiki.json``
    4. ``<root>/.llm-wiki.json`` (legacy filename)
    5. Built-in defaults
    """
    if config:
        config_path = Path(config).expanduser()
        if not config_path.is_absolute():
            config_path = root / config_path
    else:
        configured = os.environ.get("LLM_WIKI_CONFIG")
        config_path = (
            Path(configured).expanduser() if configured else root / CONFIG_NAME
        )
        if configured and not config_path.is_absolute():
            config_path = root / config_path
        if not configured and not config_path.is_file():
            legacy_path = root / LEGACY_CONFIG_NAME
            if legacy_path.is_file():
                config_path = legacy_path

    if not config_path.is_file():
        if config or os.environ.get("LLM_WIKI_CONFIG"):
            raise WikiConfigError(f"wiki config not found: {config_path}")
        return WikiLayout(
            DEFAULT_FORMAL_GLOBS, DEFAULT_RAW_GLOBS, DEFAULT_IGNORED_PARTS
        )

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WikiConfigError(f"invalid wiki config: {config_path}") from exc
    if not isinstance(data, dict):
        raise WikiConfigError("wiki config must be a JSON object")

    formal = _config_patterns(data, "formal", DEFAULT_FORMAL_GLOBS)
    raw = _config_patterns(data, "raw", DEFAULT_RAW_GLOBS)
    ignored = data.get("ignored_parts", list(DEFAULT_IGNORED_PARTS))
    if not isinstance(ignored, list) or not all(
        isinstance(item, str) and item for item in ignored
    ):
        raise WikiConfigError(
            "wiki config 'ignored_parts' must be a list of non-empty strings"
        )
    return WikiLayout(formal, raw, frozenset(ignored), config_path.resolve())


def _config_patterns(
    data: dict[str, Any], key: str, default: tuple[str, ...]
) -> tuple[str, ...]:
    value = data.get(key, list(default))
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise WikiConfigError(
            f"wiki config '{key}' must be a list of non-empty strings"
        )
    for pattern in value:
        path = Path(pattern)
        if path.is_absolute() or ".." in path.parts:
            raise WikiConfigError(
                f"wiki config '{key}' contains path outside root: {pattern}"
            )
    return tuple(value)


def ensure_inside(root: Path, path: Path) -> Path:
    root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes wiki root: {path}") from exc
    return resolved


def read_text(path: Path) -> str:
    """Read UTF-8 or recognizably UTF-16 text and reject binary content."""
    data = path.read_bytes()

    if data.startswith(b"\xef\xbb\xbf"):
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            pass

    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            decoded = data.decode("utf-16")
        except UnicodeDecodeError:
            pass
        else:
            if _looks_like_text(decoded):
                return decoded

    # BOM-less UTF-16 Markdown is accepted only when null-byte placement makes
    # the byte order unambiguous. Trying both codecs blindly makes almost any
    # even-length binary blob look like valid Unicode.
    if b"\x00" in data:
        if len(data) % 2 != 0:
            raise UnsupportedContentError(f"unsupported non-text content: {path}")
        pair_count = len(data) // 2
        even_nulls = data[0::2].count(0)
        odd_nulls = data[1::2].count(0)
        minimum_nulls = max(1, (pair_count * 3 + 9) // 10)
        maximum_other_nulls = pair_count // 10
        encoding = None
        if odd_nulls >= minimum_nulls and even_nulls <= maximum_other_nulls:
            encoding = "utf-16-le"
        elif even_nulls >= minimum_nulls and odd_nulls <= maximum_other_nulls:
            encoding = "utf-16-be"
        if encoding:
            try:
                decoded = data.decode(encoding)
            except UnicodeDecodeError:
                pass
            else:
                if _looks_like_text(decoded):
                    return decoded
        raise UnsupportedContentError(f"unsupported non-text content: {path}")

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass

    raise UnsupportedContentError(f"unsupported non-text content: {path}")


def _looks_like_text(value: str) -> bool:
    return "\x00" not in value and not any(
        ord(character) < 32 and character not in "\t\n\r" for character in value
    )


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Extract a minimal YAML frontmatter block from Markdown text.

    Only handles flat key-value pairs, ``- `` list items, and inline ``[a, b]`` lists.
    Nested mappings, block scalars, anchors, and YAML tags are not supported.
    Frontmatter values must not contain a bare ``---`` on a line by itself.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return parse_yaml_subset(lines[1:index]), "\n".join(lines[index + 1 :])
    return {}, text


def parse_yaml_subset(lines: list[str]) -> dict[str, Any]:
    """Parse a minimal subset of YAML: flat key-value pairs, ``- `` lists, inline lists.

    Does not support: nested mappings, block scalars (``|`` / ``>``), YAML anchors,
    tags, or multi-line quoted strings. Frontmatter that uses these features will be
    parsed silently incorrectly or skipped.
    """
    data: dict[str, Any] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            index += 1
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value:
            data[key] = parse_value(raw_value)
            index += 1
            continue

        items: list[str] = []
        lookahead = index + 1
        while lookahead < len(lines):
            item = lines[lookahead]
            stripped_item = item.strip()
            if (
                item
                and not item.startswith((" ", "\t"))
                and not stripped_item.startswith("- ")
            ):
                break
            if stripped_item.startswith("- "):
                items.append(stripped_item[2:].strip().strip('"').strip("'"))
            lookahead += 1
        data[key] = items
        index = lookahead
    return data


def parse_value(value: str) -> Any:
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in split_inline_list(inner)]
    return value.strip('"').strip("'")


def split_inline_list(value: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    quote: str | None = None
    for char in value:
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
        if char == "," and quote is None:
            items.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        items.append("".join(current).strip())
    return items


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def page_slug(root: Path, path: Path) -> str:
    relative = rel(root, path)
    return relative[:-3] if relative.endswith(".md") else relative


def _layout_pages(
    root: Path, patterns: tuple[str, ...], layout: WikiLayout
) -> list[Path]:
    pages: set[Path] = set()
    for pattern in patterns:
        try:
            pages.update(root.glob(pattern))
        except ValueError as exc:
            raise WikiConfigError(f"invalid wiki glob pattern: {pattern}") from exc
    safe_pages: list[Path] = []
    for path in pages:
        if not path.is_file() or any(
            part in layout.ignored_parts for part in path.parts
        ):
            continue
        try:
            safe_pages.append(ensure_inside(root, path))
        except ValueError:
            # A configured glob may match a symlink outside the wiki; retrieval must not follow it.
            continue
    return sorted(set(safe_pages))


def formal_pages(root: Path, layout: WikiLayout | None = None) -> list[Path]:
    layout = layout or resolve_layout(root)
    return _layout_pages(root, layout.formal, layout)


def raw_pages(root: Path, layout: WikiLayout | None = None) -> list[Path]:
    layout = layout or resolve_layout(root)
    return _layout_pages(root, layout.raw, layout)


def iter_scope(root: Path, scope: str, layout: WikiLayout | None = None) -> list[Path]:
    layout = layout or resolve_layout(root)
    if scope == "formal":
        return formal_pages(root, layout)
    if scope == "raw":
        return raw_pages(root, layout)
    if scope == "all":
        return sorted(set(formal_pages(root, layout) + raw_pages(root, layout)))
    raise ValueError(f"unknown scope: {scope}")


def wikilinks(text: str) -> list[str]:
    """Return unique wikilink targets in first-seen order.

    Repeated links to the same target are relationship noise in page output
    and backlink matching, so keep only the first occurrence.
    """
    targets: list[str] = []
    for raw in re.findall(r"\[\[([^\]]+)\]\]", text):
        target = raw.split("|", 1)[0].split("#", 1)[0].strip()
        if target and target not in targets:
            targets.append(target)
    return targets


def compact_page(root: Path, path: Path, text: str | None = None) -> dict[str, Any]:
    text = read_text(path) if text is None else text
    frontmatter, body = parse_frontmatter(text)
    title = frontmatter.get("title") or first_heading(body) or path.stem
    return {
        "path": rel(root, path),
        "slug": page_slug(root, path),
        "title": title,
        "type": frontmatter.get("type"),
        "tags": frontmatter.get("tags", []),
        "sources": frontmatter.get("sources", []),
        "confidence": frontmatter.get("confidence"),
        "contested": frontmatter.get("contested", False),
        "contradictions": frontmatter.get("contradictions", []),
    }


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def snippet(text: str, query: str, *, width: int = 220) -> str:
    collapsed = re.sub(r"\s+", " ", text).strip()
    if not collapsed:
        return ""
    if not query:
        return collapsed[:width]
    location = collapsed.lower().find(query.lower())
    if location < 0:
        for token in tokens(query):
            location = collapsed.lower().find(token)
            if location >= 0:
                break
    if location < 0:
        for bigram in cjk_bigrams(query):
            location = collapsed.lower().find(bigram)
            if location >= 0:
                break
    if location < 0:
        return collapsed[:width]
    start = max(0, location - width // 3)
    end = min(len(collapsed), start + width)
    prefix = "..." if start else ""
    suffix = "..." if end < len(collapsed) else ""
    return f"{prefix}{collapsed[start:end]}{suffix}"


def tokens(value: str) -> list[str]:
    return [token for token in re.split(r"[^\w\u4e00-\u9fff]+", value.lower()) if token]


def cjk_bigrams(value: str) -> list[str]:
    """Return two-character bigrams for each CJK run.

    Chinese has no whitespace word boundaries, so `tokens` keeps a whole
    phrase as one token. Bigrams let callers award partial credit when a
    query is only a phrasing variant of the page text.
    """
    runs = re.findall(r"[\u4e00-\u9fff]+", value)
    return [run[index:index + 2] for run in runs for index in range(len(run) - 1)]


def dump_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))
