from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


def slug(text: str) -> str:
    """Convert text to lowercase slug suitable for section marker IDs."""
    s = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "_", s).strip("_")


@dataclass(frozen=True)
class CommentConfig:
    prefix: str
    suffix: str = ""


@dataclass
class Section:
    id: str
    content: str
    start_line: int
    end_line: int


@dataclass
class SectionChanges:
    modified: list[str]
    missing: list[str]


EXTENSION_COMMENT_MAP: dict[str, CommentConfig] = {
    # Hash comments
    ".py": CommentConfig("#"),
    ".yaml": CommentConfig("#"),
    ".yml": CommentConfig("#"),
    ".toml": CommentConfig("#"),
    ".sh": CommentConfig("#"),
    ".bash": CommentConfig("#"),
    ".zsh": CommentConfig("#"),
    ".r": CommentConfig("#"),
    ".R": CommentConfig("#"),
    # HTML-style comments
    ".md": CommentConfig("<!--", " -->"),
    ".mdc": CommentConfig("<!--", " -->"),
    ".html": CommentConfig("<!--", " -->"),
    ".xml": CommentConfig("<!--", " -->"),
    ".svg": CommentConfig("<!--", " -->"),
    # C-style line comments
    ".js": CommentConfig("//"),
    ".ts": CommentConfig("//"),
    ".jsx": CommentConfig("//"),
    ".tsx": CommentConfig("//"),
    ".go": CommentConfig("//"),
    ".c": CommentConfig("//"),
    ".cpp": CommentConfig("//"),
    ".h": CommentConfig("//"),
    ".java": CommentConfig("//"),
    ".kt": CommentConfig("//"),
    ".swift": CommentConfig("//"),
    ".rs": CommentConfig("//"),
    ".scala": CommentConfig("//"),
    ".groovy": CommentConfig("//"),
    # C-style block comments (single line)
    ".css": CommentConfig("/*", " */"),
    ".scss": CommentConfig("/*", " */"),
    ".less": CommentConfig("/*", " */"),
    # SQL
    ".sql": CommentConfig("--"),
    # Lua
    ".lua": CommentConfig("--"),
}

FILENAME_COMMENT_MAP: dict[str, CommentConfig] = {
    "justfile": CommentConfig("#"),
    "Makefile": CommentConfig("#"),
    "Dockerfile": CommentConfig("#"),
    ".gitignore": CommentConfig("#"),
    ".dockerignore": CommentConfig("#"),
    ".env": CommentConfig("#"),
    ".editorconfig": CommentConfig("#"),
    "uv.lock": CommentConfig("#"),
    "CODEOWNERS": CommentConfig("#"),
    "LICENSE": CommentConfig("#"),
}


def get_comment_config(path: Path | str, override: CommentConfig | None = None) -> CommentConfig:
    if override:
        return override
    p = Path(path) if isinstance(path, str) else path
    if config := EXTENSION_COMMENT_MAP.get(p.suffix):
        return config
    if config := FILENAME_COMMENT_MAP.get(p.name):
        return config
    raise ValueError(f"No comment config for: {p.name} (extension={p.suffix!r})")


def _build_start_pattern(tool_name: str, config: CommentConfig) -> re.Pattern[str]:
    return re.compile(
        rf"^{re.escape(config.prefix)}\s*===\s*DO_NOT_EDIT:\s*"
        rf"{re.escape(tool_name)}\s+(?P<id>[\w-]+)\s*==={re.escape(config.suffix)}$",
        re.MULTILINE,
    )


def _build_end_pattern(tool_name: str, config: CommentConfig) -> re.Pattern[str]:
    return re.compile(
        rf"^{re.escape(config.prefix)}\s*===\s*OK_EDIT:\s*"
        rf"{re.escape(tool_name)}\s+(?P<end_id>[\w-]+)\s*==={re.escape(config.suffix)}$",
        re.MULTILINE,
    )


def _start_marker(tool_name: str, section_id: str, config: CommentConfig) -> str:
    return f"{config.prefix} === DO_NOT_EDIT: {tool_name} {section_id} ==={config.suffix}"


def _end_marker(tool_name: str, section_id: str, config: CommentConfig) -> str:
    return f"{config.prefix} === OK_EDIT: {tool_name} {section_id} ==={config.suffix}"


def parse_sections(
    content: str,
    tool_name: str,
    config: CommentConfig,
    filename: str = "",
) -> list[Section]:
    start_pattern = _build_start_pattern(tool_name, config)
    end_pattern = _build_end_pattern(tool_name, config)
    lines = content.split("\n")
    sections: list[Section] = []
    current_id: str | None = None
    current_start: int = -1
    content_lines: list[str] = []
    file_suffix = f" in {filename}" if filename else ""

    for i, line in enumerate(lines):
        if start_match := start_pattern.match(line):
            if current_id is not None:
                raise ValueError(
                    f"Nested section at line {i}: found '{start_match.group('id')}' inside '{current_id}'{file_suffix}"
                )
            current_id = start_match.group("id")
            current_start = i
            content_lines = []
        elif end_match := end_pattern.match(line):
            if current_id is None:
                continue  # standalone OK_EDIT is valid, ignored
            end_id = end_match.group("end_id")
            if end_id != current_id:
                raise ValueError(
                    f"Mismatched section end at line {i}: expected '{current_id}', got '{end_id}'{file_suffix}"
                )
            sections.append(
                Section(
                    id=current_id,
                    content="\n".join(content_lines),
                    start_line=current_start,
                    end_line=i,
                )
            )
            current_id = None
            current_start = -1
            content_lines = []
        elif current_id is not None:
            content_lines.append(line)

    if current_id is not None:
        raise ValueError(f"Unclosed section '{current_id}' starting at line {current_start}{file_suffix}")

    return sections


def has_sections(content: str, tool_name: str, config: CommentConfig) -> bool:
    return bool(_build_start_pattern(tool_name, config).search(content))


def extract_sections(
    content: str,
    tool_name: str,
    config: CommentConfig,
    filename: str = "",
) -> dict[str, str]:
    return {s.id: s.content for s in parse_sections(content, tool_name, config, filename)}


def compare_sections(
    baseline_content: str,
    current_content: str,
    tool_name: str,
    config: CommentConfig,
    skip: set[str] | None = None,
    filename: str = "",
) -> list[str]:
    """Return section IDs with changes (modified or removed), excluding skipped sections."""
    skip_ids = skip or set()
    baseline_secs = extract_sections(baseline_content, tool_name, config, filename)
    current_secs = extract_sections(current_content, tool_name, config, filename)
    return [
        sec_id
        for sec_id, baseline_text in baseline_secs.items()
        if sec_id not in skip_ids and baseline_text != current_secs.get(sec_id, "")
    ]


def changed_sections(
    baseline_content: str,
    current_content: str,
    tool_name: str,
    config: CommentConfig,
    skip: set[str] | None = None,
    filename: str = "",
) -> SectionChanges:
    """Return modified and missing sections separately."""
    skip_ids = skip or set()
    baseline_secs = extract_sections(baseline_content, tool_name, config, filename)
    current_secs = extract_sections(current_content, tool_name, config, filename)
    modified, missing = [], []
    for sec_id, baseline_text in baseline_secs.items():
        if sec_id in skip_ids:
            continue
        if sec_id not in current_secs:
            missing.append(sec_id)
        elif baseline_text != current_secs[sec_id]:
            modified.append(sec_id)
    return SectionChanges(modified=modified, missing=missing)


def wrap_section(content: str, section_id: str, tool_name: str, config: CommentConfig) -> str:
    start = _start_marker(tool_name, section_id, config)
    end = _end_marker(tool_name, section_id, config)
    return f"{start}\n{content}\n{end}"


def wrap_in_default_section(content: str, tool_name: str, config: CommentConfig) -> str:
    return wrap_section(content, "default", tool_name, config)


def _compute_section_content(
    dest_parsed: list[Section],
    src_sections: dict[str, str],
    skip: set[str],
    keep_deleted_sections: bool,
) -> dict[str, str | None]:
    """Compute final content for each dest section: src, original, or None (delete)."""
    result: dict[str, str | None] = {}
    for s in dest_parsed:
        if s.id in skip:
            result[s.id] = s.content
        elif s.id in src_sections:
            result[s.id] = src_sections[s.id]
        elif keep_deleted_sections:
            result[s.id] = s.content
        else:
            result[s.id] = None
    return result


def replace_sections(
    dest_content: str,
    src_sections: dict[str, str],
    tool_name: str,
    config: CommentConfig,
    skip_sections: list[str] | None = None,
    *,
    keep_deleted_sections: bool = False,
) -> str:
    """Replace sections in dest_content with src_sections.

    Args:
        dest_content: The destination content containing sections to update
        src_sections: Dict mapping section IDs to their new content
        tool_name: The tool name used in section markers
        config: Comment configuration for the file type
        skip_sections: Section IDs to preserve unchanged (not replaced, not deleted)
        keep_deleted_sections: If True, preserve sections not in src_sections.
            If False (default), delete sections not in src_sections (unless skipped).

    New sections from src_sections are always added at the end.
    """
    skip = set(skip_sections or [])
    dest_parsed = parse_sections(dest_content, tool_name, config)
    dest_ids = {s.id for s in dest_parsed}
    final_content = _compute_section_content(dest_parsed, src_sections, skip, keep_deleted_sections)

    start_pattern = _build_start_pattern(tool_name, config)
    end_pattern = _build_end_pattern(tool_name, config)
    result: list[str] = []
    current_id: str | None = None

    for line in dest_content.split("\n"):
        if start_match := start_pattern.match(line):
            current_id = start_match.group("id")
            if current_id and final_content.get(current_id) is not None:
                result.append(line)
        elif end_pattern.match(line):
            if current_id and (content := final_content.get(current_id)) is not None:
                result.append(content)
                result.append(line)
            current_id = None
        elif current_id is None:
            result.append(line)

    # Append new sections from src not in dest
    for sid, content in src_sections.items():
        if sid not in dest_ids and sid not in skip:
            result.extend((_start_marker(tool_name, sid, config), content, _end_marker(tool_name, sid, config)))

    return "\n".join(result)


# Path-based convenience functions
def parse_sections_from_path(path: Path, tool_name: str) -> list[Section]:
    config = get_comment_config(path)
    return parse_sections(path.read_text(), tool_name, config, str(path))


def has_sections_in_path(path: Path, tool_name: str) -> bool:
    config = get_comment_config(path)
    return has_sections(path.read_text(), tool_name, config)


def extract_sections_from_path(path: Path, tool_name: str) -> dict[str, str]:
    config = get_comment_config(path)
    return extract_sections(path.read_text(), tool_name, config, str(path))
