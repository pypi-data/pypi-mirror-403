"""
CDL Definition - Go to definition support for CDL documents.

This module provides go-to-definition functionality for CDL elements,
allowing navigation to the source definitions of forms, twin laws, etc.
"""

import os
import re
from typing import Any

try:
    from lsprotocol import types
except ImportError:
    types = None

from ..constants import (
    ALL_POINT_GROUPS,
    CRYSTAL_SYSTEMS,
    DEFINITION_PATTERNS,
    NAMED_FORMS,
    TWIN_LAWS,
    get_definition_source,
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
    word_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-/")

    start = col
    end = col

    while start > 0 and line[start - 1] in word_chars:
        start -= 1

    while end < len(line) and line[end] in word_chars:
        end += 1

    word = line[start:end]
    return (word, start, end)


def _find_line_in_file(file_path: str, pattern: str, target: str) -> int | None:
    """
    Find the line number of a target definition in a file.

    Args:
        file_path: Path to the file
        pattern: Pattern to locate the dict start
        target: The specific key to find

    Returns:
        Line number (0-based) or None
    """
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        in_dict = False
        dict_depth = 0

        for i, line in enumerate(lines):
            # Check if we found the dict start
            if pattern in line:
                in_dict = True
                dict_depth = 0

            if in_dict:
                # Track brace depth
                dict_depth += line.count("{") - line.count("}")

                # Look for the target key
                # Patterns like: 'target': or "target":
                key_pattern = rf"['\"]({re.escape(target)})['\"]:"
                if re.search(key_pattern, line, re.IGNORECASE):
                    return i

                # Also check for unquoted keys
                if f"'{target}'" in line or f'"{target}"' in line:
                    return i

                # Exit dict when depth returns to 0
                if dict_depth <= 0 and i > 0:
                    in_dict = False

        return None

    except Exception:
        return None


def _get_source_file(category: str) -> str | None:
    """Get the source file path for a definition category."""
    source_path = get_definition_source(category)
    if source_path is not None and source_path.exists():
        return str(source_path)
    return None


def _create_location(file_path: str, line: int, character: int = 0) -> Any:
    """Create an LSP Location object."""
    if types is None:
        return {
            "uri": f"file://{file_path}",
            "range": {
                "start": {"line": line, "character": character},
                "end": {"line": line, "character": character + 20},
            },
        }

    from urllib.parse import quote

    uri = f"file://{quote(file_path, safe='/:@')}"

    return types.Location(
        uri=uri,
        range=types.Range(
            start=types.Position(line=line, character=character),
            end=types.Position(line=line, character=character + 20),
        ),
    )


def get_definition(line: str, col: int, line_num: int = 0, document_uri: str = "") -> Any | None:
    """
    Get definition location for the symbol at position.

    Args:
        line: Current line text
        col: Column position (0-based)
        line_num: Line number (0-based)
        document_uri: URI of the current document

    Returns:
        Location object or None if no definition found
    """
    word, start, end = _get_word_at_position(line, col)

    if not word:
        return None

    word_lower = word.lower()

    # Check if it's a named form
    if word_lower in NAMED_FORMS:
        file_path = _get_source_file("forms")
        if file_path:
            pattern = DEFINITION_PATTERNS["forms"]
            found_line = _find_line_in_file(file_path, pattern, word_lower)
            if found_line is not None:
                return _create_location(file_path, found_line)

    # Check if it's a twin law
    if word_lower in TWIN_LAWS:
        file_path = _get_source_file("twin_laws")
        if file_path:
            pattern = DEFINITION_PATTERNS["twin_laws"]
            # Handle both 'spinel' and 'spinel_law' style names
            found_line = _find_line_in_file(file_path, pattern, word_lower)
            if found_line is None and not word_lower.endswith("_law"):
                found_line = _find_line_in_file(file_path, pattern, word_lower + "_law")
            if found_line is not None:
                return _create_location(file_path, found_line)

    # Check if it's a crystal system
    if word_lower in CRYSTAL_SYSTEMS:
        file_path = _get_source_file("systems")
        if file_path:
            pattern = DEFINITION_PATTERNS["systems"]
            found_line = _find_line_in_file(file_path, pattern, word_lower)
            if found_line is not None:
                return _create_location(file_path, found_line)

    # Check if it's a point group
    if word in ALL_POINT_GROUPS:
        file_path = _get_source_file("point_groups")
        if file_path:
            pattern = DEFINITION_PATTERNS["point_groups"]
            found_line = _find_line_in_file(file_path, pattern, word)
            if found_line is not None:
                return _create_location(file_path, found_line)

    return None


def get_definitions(line: str, col: int, line_num: int = 0, document_uri: str = "") -> list[Any]:
    """
    Get all definition locations for the symbol at position.

    This is useful when a symbol might have multiple definitions
    (e.g., a form defined in multiple places).

    Args:
        line: Current line text
        col: Column position (0-based)
        line_num: Line number (0-based)
        document_uri: URI of the current document

    Returns:
        List of Location objects
    """
    definition = get_definition(line, col, line_num, document_uri)
    if definition:
        return [definition]
    return []
