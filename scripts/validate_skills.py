#!/usr/bin/env python3
"""Validate the repository's skill packages against the Agent Skills spec."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

try:
    from scripts.manage_skill_links import ConfigError, load_config
except ModuleNotFoundError:  # Running as a script with scripts/ on sys.path.
    from manage_skill_links import ConfigError, load_config


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
CONFIG_PATH = ROOT / "config" / "skill-links.toml"
CATALOG_FILES = ("README.md", "README_zh-CN.md")
REQUIRED_SKILL_FIELDS = {"name", "description"}
OPTIONAL_SKILL_FIELDS = {"license", "compatibility", "allowed-tools", "metadata"}
REQUIRED_OPENAI_INTERFACE_FIELDS = {"display_name", "short_description", "default_prompt"}
OPTIONAL_OPENAI_INTERFACE_FIELDS = {"icon_small", "icon_large", "brand_color"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$")
QUOTED_FIELD_RE = re.compile(r'^\s{2}([a-z_]+):\s+"(.*)"\s*$')
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")

SVG_NS = "{http://www.w3.org/2000/svg}"
DIAGRAM_WIDTH = 680
DIAGRAM_INNER_MARGIN = 8
TEXT_DESCENT_EM = 0.4
ASCII_EM = 0.55
CJK_START = 0x2E80
SKILL_LINE_LIMIT = 500
FLOW_SUFFIX = "-flow.svg"
REPO_DIAGRAMS = {"repository-overview.svg"}
RESOURCE_DIRS = ("references", "scripts", "assets")
PLACEHOLDER_CHARS = frozenset("<>${}*?")


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}, ["missing opening YAML frontmatter delimiter"]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, ["missing closing YAML frontmatter delimiter"]

    fields: dict[str, str] = {}
    current: str | None = None
    for line in lines[1:end]:
        match = FIELD_RE.match(line)
        if match:
            current = match.group(1)
            if current in fields:
                errors.append(f"duplicate frontmatter field: {current}")
            raw_value = (match.group(2) or "").strip()
            if raw_value and raw_value not in {"|", "|-", ">", ">-"}:
                if not (
                    (raw_value.startswith('"') and raw_value.endswith('"'))
                    or (raw_value.startswith("'") and raw_value.endswith("'"))
                ) and ": " in raw_value:
                    errors.append(
                        f"plain scalar contains an unquoted colon: {raw_value!r}"
                    )
                fields[current] = raw_value.strip('"\'')
            else:
                fields[current] = ""
            continue
        if current and (line.startswith("  ") or not line.strip()):
            value = line.strip()
            if value and value not in {"|", "|-", ">", ">-"}:
                fields[current] = f"{fields[current]} {value}".strip()
            continue
        errors.append(f"unsupported frontmatter line: {line!r}")

    body = "\n".join(lines[end + 1 :])
    if "[TODO" in text or re.search(r"\bTODO:\s*(?:Complete|Replace|Add content)", text):
        errors.append("contains scaffold TODO content")
    if not body.strip():
        errors.append("SKILL.md body is empty")
    return fields, errors


def parse_openai_yaml(path: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "interface:":
        errors.append("must start with 'interface:'")
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        match = QUOTED_FIELD_RE.match(line)
        if not match:
            errors.append(f"unsupported or unquoted field: {line!r}")
            continue
        field = match.group(1)
        if field in fields:
            errors.append(f"duplicate interface field: {field}")
        fields[field] = match.group(2)
    return fields, errors


def validate_skill_resources(skill_dir: Path, text: str) -> list[str]:
    """Check resource paths resolve and that every packaged resource is referenced."""
    relative = skill_dir.relative_to(ROOT)
    errors: list[str] = []

    for token in BACKTICK_RE.findall(text):
        value = token.strip()
        if not value.startswith(tuple(f"{dirname}/" for dirname in RESOURCE_DIRS)):
            continue
        if any(char.isspace() for char in value):
            continue
        if any(char in PLACEHOLDER_CHARS for char in value):
            continue
        if not (skill_dir / value).exists():
            errors.append(f"{relative}: referenced resource does not exist: {value}")

    for dirname in RESOURCE_DIRS:
        directory = skill_dir / dirname
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_dir() or path.name in {".DS_Store"} or path.suffix == ".pyc":
                continue
            if "__pycache__" in path.parts:
                continue
            resource = path.relative_to(skill_dir).as_posix()
            if resource not in text:
                errors.append(
                    f"{relative}: packaged resource is not referenced from SKILL.md: {resource}"
                )
    return errors


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    relative = skill_dir.relative_to(ROOT)
    name = skill_dir.name

    if not NAME_RE.fullmatch(name) or len(name) > 64:
        errors.append(f"{relative}: invalid directory name")

    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        errors.append(f"{relative}: missing SKILL.md")
    else:
        text = skill_file.read_text(encoding="utf-8")
        if len(text.splitlines()) > SKILL_LINE_LIMIT:
            errors.append(
                f"{skill_file.relative_to(ROOT)}: exceeds {SKILL_LINE_LIMIT} lines"
            )
        fields, frontmatter_errors = parse_frontmatter(skill_file)
        errors.extend(f"{skill_file.relative_to(ROOT)}: {error}" for error in frontmatter_errors)
        field_names = set(fields)
        missing = REQUIRED_SKILL_FIELDS - field_names
        unexpected = field_names - REQUIRED_SKILL_FIELDS - OPTIONAL_SKILL_FIELDS
        if missing:
            errors.append(
                f"{skill_file.relative_to(ROOT)}: missing required frontmatter fields {sorted(missing)}"
            )
        if unexpected:
            errors.append(
                f"{skill_file.relative_to(ROOT)}: unsupported frontmatter fields {sorted(unexpected)}"
            )
        if fields.get("name") != name:
            errors.append(f"{skill_file.relative_to(ROOT)}: name must match directory {name!r}")
        if not fields.get("description", "").strip():
            errors.append(f"{skill_file.relative_to(ROOT)}: description is empty")
        elif len(fields["description"]) > 1024:
            errors.append(f"{skill_file.relative_to(ROOT)}: description exceeds 1024 characters")
        if len(fields.get("compatibility", "")) > 500:
            errors.append(f"{skill_file.relative_to(ROOT)}: compatibility exceeds 500 characters")
        errors.extend(validate_skill_resources(skill_dir, text))

    openai_file = skill_dir / "agents" / "openai.yaml"
    if openai_file.is_file():
        fields, yaml_errors = parse_openai_yaml(openai_file)
        errors.extend(f"{openai_file.relative_to(ROOT)}: {error}" for error in yaml_errors)
        field_names = set(fields)
        missing = REQUIRED_OPENAI_INTERFACE_FIELDS - field_names
        unexpected = field_names - REQUIRED_OPENAI_INTERFACE_FIELDS - OPTIONAL_OPENAI_INTERFACE_FIELDS
        empty = sorted(
            field
            for field in REQUIRED_OPENAI_INTERFACE_FIELDS & field_names
            if not fields.get(field, "").strip()
        )
        if missing:
            errors.append(
                f"{openai_file.relative_to(ROOT)}: missing required interface fields {sorted(missing)}"
            )
        if empty:
            errors.append(
                f"{openai_file.relative_to(ROOT)}: empty required interface fields {empty}"
            )
        if unexpected:
            errors.append(
                f"{openai_file.relative_to(ROOT)}: unsupported interface fields {sorted(unexpected)}"
            )
        short_description = fields.get("short_description", "")
        if short_description and not 25 <= len(short_description) <= 64:
            errors.append(
                f"{openai_file.relative_to(ROOT)}: short_description must be 25-64 characters"
            )
        if f"${name}" not in fields.get("default_prompt", ""):
            errors.append(
                f"{openai_file.relative_to(ROOT)}: default_prompt must mention ${name}"
            )

    for path in skill_dir.rglob("*"):
        if path.name == ".DS_Store" or path.name == "__pycache__" or path.suffix == ".pyc":
            errors.append(f"{path.relative_to(ROOT)}: generated file is not allowed")

    return errors


def validate_catalog(skill_names: set[str], diagram_names: set[str]) -> list[str]:
    errors: list[str] = []
    for catalog_name in CATALOG_FILES:
        catalog_path = ROOT / catalog_name
        if not catalog_path.is_file():
            errors.append(f"missing catalog file: {catalog_name}")
            continue
        text = catalog_path.read_text(encoding="utf-8")
        for skill_name in sorted(skill_names):
            expected = f"skills/{skill_name}/SKILL.md"
            if expected not in text:
                errors.append(f"{catalog_name}: missing catalog entry for {skill_name}")
        for diagram_name in sorted(diagram_names):
            expected = f"assets/{diagram_name}"
            if expected not in text:
                errors.append(f"{catalog_name}: missing diagram entry for {diagram_name}")
    return errors


def validate_markdown_links() -> list[str]:
    errors: list[str] = []
    external_docs = (ROOT / "docs").is_symlink()
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = match.group(1).strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            if external_docs and path.parent == ROOT and Path(target).parts[:1] == ("docs",):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(
                    f"{path.relative_to(ROOT)}: broken local link {match.group(1)!r}"
                )
    return errors


def classify_root_diagram(filename: str, skill_names: set[str]) -> tuple[str, str | None]:
    """Return (kind, skill) for a root asset name: repo, flow, topic-flow or unknown."""
    if filename in REPO_DIAGRAMS:
        return "repo", None
    for skill_name in sorted(skill_names, key=len, reverse=True):
        if filename == f"{skill_name}{FLOW_SUFFIX}":
            return "flow", skill_name
        prefix = f"{skill_name}-"
        if filename.startswith(prefix) and filename.endswith(FLOW_SUFFIX):
            topic = filename[len(prefix) : -len(FLOW_SUFFIX)]
            if topic and NAME_RE.fullmatch(topic):
                return "topic-flow", skill_name
    return "unknown", None


def validate_root_diagrams(skill_names: set[str]) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    assets_dir = ROOT / "assets"
    if not assets_dir.is_dir():
        return ["missing diagram directory: assets/"], set()
    diagram_paths = sorted(assets_dir.glob("*.svg"))
    diagram_names = {path.name for path in diagram_paths}
    for name in sorted(diagram_names):
        kind, _skill = classify_root_diagram(name, skill_names)
        if kind == "unknown":
            errors.append(
                f"assets/{name}: unrecognized root diagram; expected "
                f"<skill>{FLOW_SUFFIX} or <skill>-<topic>{FLOW_SUFFIX}"
            )
    for skill_name in sorted(skill_names):
        expected = f"{skill_name}{FLOW_SUFFIX}"
        if expected not in diagram_names:
            errors.append(f"assets/{expected}: missing required skill diagram")
    return errors, diagram_names


def parse_svg(path: Path) -> tuple[ElementTree.Element | None, str | None]:
    try:
        return ElementTree.parse(path).getroot(), None
    except ElementTree.ParseError as exc:
        return None, f"malformed SVG: {exc}"


def estimate_text_width(text: str, font_size: float) -> float:
    """Estimate rendered width: CJK is a full em, ASCII about 0.55 em.

    This mirrors the RULES.md text-safety boundary, which exists because SVG does
    not wrap text and silently clips anything that leaves its box.
    """
    return sum(
        (1.0 if ord(char) > CJK_START else ASCII_EM) * font_size for char in text
    )


def attributed_box(
    boxes: list[tuple[float, float, float, float]],
    start: float,
    end: float,
    baseline: float,
) -> tuple[float, float, float, float] | None:
    """Pick the tightest box a text line belongs to.

    Attribution needs overlap rather than containment: text that is wider than
    its box must still be charged against that box instead of escaping the check.
    """
    candidates = []
    for box in boxes:
        left, top, width, height = box
        if not top <= baseline <= top + height:
            continue
        if end < left or start > left + width:
            continue
        candidates.append(box)
    if not candidates:
        return None
    return min(candidates, key=lambda box: box[2] * box[3])


def validate_diagram(
    path: Path, root: ElementTree.Element | None = None
) -> list[str]:
    """Check that no diagram text leaves its own box or the canvas."""
    relative = path.relative_to(ROOT)
    if root is None:
        root, error = parse_svg(path)
        if error is not None:
            return [f"{relative}: {error}"]

    canvas_width = float(root.get("width", DIAGRAM_WIDTH))
    height = float(root.get("height", 0))
    boxes: list[tuple[float, float, float, float]] = []
    for element in root.iter(SVG_NS + "rect"):
        x = float(element.get("x", 0))
        y = float(element.get("y", 0))
        width = float(element.get("width", 0))
        box_height = float(element.get("height", 0))
        if x == 0 and y == 0 and width >= canvas_width:
            continue  # background plate, not a content box
        boxes.append((x, y, width, box_height))

    errors: list[str] = []
    for element in root.iter(SVG_NS + "text"):
        baseline = float(element.get("y", 0))
        font_size = float(element.get("font-size", 12))
        anchor = element.get("text-anchor", "start")
        content = "".join(element.itertext())
        width = estimate_text_width(content, font_size)
        x = float(element.get("x", 0))
        if anchor == "middle":
            start = x - width / 2
        elif anchor == "end":
            start = x - width
        else:
            start = x
        end = start + width
        label = content[:40]

        box = attributed_box(boxes, start, end, baseline)
        if box is None:
            if end > canvas_width - 40 or baseline + TEXT_DESCENT_EM * font_size > height:
                errors.append(f"{relative}: text leaves the canvas: {label!r}")
            continue

        bottom_overflow = (baseline + TEXT_DESCENT_EM * font_size) - (box[1] + box[3])
        right_overflow = end - (box[0] + box[2] - DIAGRAM_INNER_MARGIN)
        if bottom_overflow > 0 or right_overflow > 0:
            errors.append(
                f"{relative}: text overflows its box by "
                f"{max(bottom_overflow, right_overflow):.1f}px: {label!r}"
            )
    return errors


def validate_flow_spec(path: Path, root: ElementTree.Element) -> list[str]:
    """Enforce the RULES.md canvas and accessibility contract for skill diagrams."""
    relative = path.relative_to(ROOT)
    errors: list[str] = []
    height = root.get("height", "")
    if root.get("width") != str(DIAGRAM_WIDTH):
        errors.append(f"{relative}: flow diagram width must be {DIAGRAM_WIDTH}")
    if not height:
        errors.append(f"{relative}: flow diagram is missing a numeric height")
    else:
        try:
            float(height)
        except ValueError:
            errors.append(f"{relative}: flow diagram height must be numeric")
        view_box = (root.get("viewBox") or "").split()
        if view_box != ["0", "0", str(DIAGRAM_WIDTH), height]:
            errors.append(
                f"{relative}: flow diagram viewBox must be '0 0 {DIAGRAM_WIDTH} {height}'"
            )
    if root.get("role") != "img":
        errors.append(f"{relative}: flow diagram root must have role=\"img\"")
    title_element = root.find(SVG_NS + "title")
    desc_element = root.find(SVG_NS + "desc")
    title = "".join(title_element.itertext()) if title_element is not None else ""
    desc = "".join(desc_element.itertext()) if desc_element is not None else ""
    if not title.strip():
        errors.append(f"{relative}: flow diagram is missing a non-empty <title>")
    if not desc.strip():
        errors.append(f"{relative}: flow diagram is missing a non-empty <desc>")
    if not any(element.get("font-family") for element in root.iter()):
        errors.append(f"{relative}: flow diagram is missing font-family")
    return errors


def validate_diagrams(skill_names: set[str]) -> list[str]:
    errors: list[str] = []
    for path in sorted((ROOT / "assets").glob("*.svg")):
        root, error = parse_svg(path)
        if error is not None:
            errors.append(f"{path.relative_to(ROOT)}: {error}")
            continue
        errors.extend(validate_diagram(path, root))
        kind, _skill = classify_root_diagram(path.name, skill_names)
        if kind in {"flow", "topic-flow"}:
            errors.extend(validate_flow_spec(path, root))

    for path in sorted((ROOT / "skills").glob("*/assets/**/*.svg")):
        relative = path.relative_to(ROOT)
        _root, error = parse_svg(path)
        if error is not None:
            errors.append(f"{relative}: {error}")
        if path.name.endswith(FLOW_SUFFIX):
            errors.append(
                f"{relative}: skill diagrams belong in repository assets/, not the skill package"
            )
    return errors


def validate_distribution(skill_names: set[str]) -> list[str]:
    """Check that every distribution target accounts for every skill."""
    if not CONFIG_PATH.is_file():
        return [f"missing distribution config: {CONFIG_PATH.relative_to(ROOT)}"]
    try:
        config = load_config(CONFIG_PATH)
    except ConfigError as exc:
        return [f"{CONFIG_PATH.relative_to(ROOT)}: {exc}"]

    errors: list[str] = []
    target_names = {target.name for target in config.targets}
    if "agents" not in target_names:
        errors.append(
            f"{CONFIG_PATH.relative_to(ROOT)}: missing required [targets.agents]"
        )

    for target in config.targets:
        prefix = f"{CONFIG_PATH.relative_to(ROOT)}: targets.{target.name}"
        covered = set(target.skills) | set(target.excluded)
        unknown = covered - skill_names
        missing = skill_names - covered
        if unknown:
            errors.append(f"{prefix} references unknown skills: {sorted(unknown)}")
        if missing:
            errors.append(f"{prefix} does not install or exclude: {sorted(missing)}")
    return errors


def main() -> int:
    errors: list[str] = []
    if not SKILLS_DIR.is_dir():
        print("ERROR: skills directory not found", file=sys.stderr)
        return 1

    skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())
    if not skill_dirs:
        errors.append("skills directory contains no skill packages")

    names: set[str] = set()
    for skill_dir in skill_dirs:
        if skill_dir.name in names:
            errors.append(f"duplicate skill directory: {skill_dir.name}")
        names.add(skill_dir.name)
        errors.extend(validate_skill(skill_dir))

    diagram_errors, diagram_names = validate_root_diagrams(names)
    errors.extend(diagram_errors)
    errors.extend(validate_catalog(names, diagram_names))
    errors.extend(validate_markdown_links())
    errors.extend(validate_diagrams(names))
    errors.extend(validate_distribution(names))

    if errors:
        print(f"Skill validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(skill_dirs)} skill package(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
