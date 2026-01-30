"""
CDL Hover - Documentation on hover for CDL documents.

This module provides hover information (documentation) for CDL elements
like crystal systems, point groups, forms, and twin laws.
"""

import re
from typing import Any

try:
    from lsprotocol import types
except ImportError:
    types = None

from ..constants import (
    ALL_POINT_GROUPS,
    CRYSTAL_SYSTEMS,
    FORM_DOCS,
    MODIFICATION_DOCS,
    MODIFICATIONS,
    NAMED_FORMS,
    POINT_GROUP_DOCS,
    SYSTEM_DOCS,
    TWIN_LAW_DOCS,
    TWIN_LAWS,
    get_system_for_point_group,
)


def _get_word_at_position(line: str, col: int) -> tuple[str, int, int]:
    """
    Get the word at the given column position.

    Args:
        line: Line text
        col: Column position (0-based)

    Returns:
        Tuple of (word, start_col, end_col)
    """
    # Handle out of bounds
    if col >= len(line):
        col = len(line) - 1 if line else 0
    if col < 0:
        col = 0

    # Find word boundaries
    # Words can contain alphanumerics, underscores, hyphens, and slashes (for point groups)
    word_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-/")

    start = col
    end = col

    # Expand left
    while start > 0 and line[start - 1] in word_chars:
        start -= 1

    # Expand right
    while end < len(line) and line[end] in word_chars:
        end += 1

    word = line[start:end]
    return (word, start, end)


def _get_miller_at_position(line: str, col: int) -> tuple[str, int, int] | None:
    """
    Check if position is inside a Miller index and return it.

    Args:
        line: Line text
        col: Column position

    Returns:
        Tuple of (miller_string, start, end) or None
    """
    # Find Miller index boundaries
    for match in re.finditer(r"\{[^}]+\}", line):
        if match.start() <= col <= match.end():
            return (match.group(0), match.start(), match.end())
    return None


def _create_hover(content: str, start: int, end: int, line: int) -> Any:
    """Create an LSP Hover object."""
    if types is None:
        return {
            "contents": content,
            "range": {
                "start": {"line": line, "character": start},
                "end": {"line": line, "character": end},
            },
        }

    return types.Hover(
        contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=content),
        range=types.Range(
            start=types.Position(line=line, character=start),
            end=types.Position(line=line, character=end),
        ),
    )


def get_hover_info(line: str, col: int, line_num: int = 0) -> Any | None:
    """
    Get hover information for the position.

    Args:
        line: Current line text
        col: Column position (0-based)
        line_num: Line number (0-based)

    Returns:
        Hover object or None if no hover info available
    """
    # Check for Miller index first
    miller_info = _get_miller_at_position(line, col)
    if miller_info:
        miller_str, start, end = miller_info
        content = _get_miller_hover(miller_str)
        if content:
            return _create_hover(content, start, end, line_num)

    # Get word at position
    word, start, end = _get_word_at_position(line, col)

    if not word:
        return None

    word_lower = word.lower()

    # Check if it's a crystal system
    if word_lower in CRYSTAL_SYSTEMS:
        content = SYSTEM_DOCS.get(word_lower)
        if content:
            return _create_hover(content, start, end, line_num)

    # Check if it's a point group
    if word in ALL_POINT_GROUPS:
        content = POINT_GROUP_DOCS.get(word)
        if content:
            # Add system info
            system = get_system_for_point_group(word)
            if system:
                content += f"\n\nBelongs to **{system}** system."
            return _create_hover(content, start, end, line_num)

    # Check if it's a named form
    if word_lower in NAMED_FORMS:
        content = FORM_DOCS.get(word_lower)
        if content:
            miller = NAMED_FORMS[word_lower]
            content += f"\n\nMiller indices: {{{miller[0]}{miller[1]}{miller[2]}}}"
            return _create_hover(content, start, end, line_num)

    # Check if it's a twin law
    if word_lower in TWIN_LAWS:
        content = TWIN_LAW_DOCS.get(word_lower)
        if content:
            return _create_hover(content, start, end, line_num)

    # Check if it's a modification
    if word_lower in MODIFICATIONS:
        content = MODIFICATION_DOCS.get(word_lower)
        if content:
            return _create_hover(content, start, end, line_num)

    # Check for 'twin' keyword
    if word_lower == "twin":
        content = MODIFICATION_DOCS.get("twin")
        if content:
            return _create_hover(content, start, end, line_num)

    # Check for scale value (@N.N)
    scale_match = re.search(r"@(\d+\.?\d*)", line)
    if scale_match and scale_match.start() <= col <= scale_match.end():
        scale = float(scale_match.group(1))
        content = _get_scale_hover(scale)
        return _create_hover(content, scale_match.start(), scale_match.end(), line_num)

    return None


def _get_miller_hover(miller_str: str) -> str:
    """Get hover content for a Miller index."""
    # Parse the Miller index
    inner = miller_str[1:-1]  # Remove braces

    # Try to identify the form
    for form_name, indices in NAMED_FORMS.items():
        miller_repr = f"{{{indices[0]}{indices[1]}{indices[2]}}}"
        if miller_str == miller_repr:
            doc = FORM_DOCS.get(form_name, "")
            return f"**Miller Index {miller_str}**\n\nNamed form: **{form_name}**\n\n{doc}"

    # Count faces based on system (approximate)
    content = f"**Miller Index {miller_str}**\n\n"

    # Check if it's 4-index (Miller-Bravais)
    digits = re.findall(r"-?\d", inner)
    if len(digits) == 4:
        content += "Miller-Bravais notation (hexagonal/trigonal system)\n\n"
        content += "The third index `i` satisfies `i = -(h+k)`"
    elif len(digits) == 3:
        content += "Standard 3-index Miller notation"

    return content


def _get_scale_hover(scale: float) -> str:
    """Get hover content for a scale value."""
    content = f"**Scale Factor: {scale}**\n\n"

    if scale == 1.0:
        content += "Default scale - form at standard distance from origin."
    elif scale < 1.0:
        content += f"Form is closer to origin ({scale:.0%} of standard distance).\n"
        content += "Results in larger face area relative to other forms."
    else:
        content += f"Form is farther from origin ({scale:.0%} of standard distance).\n"
        content += "Results in smaller face area relative to other forms."

    content += "\n\n**Typical values:**\n"
    content += "- `0.3-0.5`: Dominant form (large faces)\n"
    content += "- `0.8-1.2`: Standard presence\n"
    content += "- `1.5-2.0`: Minor truncation"

    if scale > 3.0:
        content += "\n\n⚠️ This scale value is unusually large."
    elif scale < 0.2:
        content += "\n\n⚠️ This scale value is unusually small."

    return content
