"""
CDL Formatting - Auto-format CDL documents.

This module provides document formatting for CDL files with
consistent spacing and style conventions.

Formatting Rules:
- Lowercase system names: cubic not Cubic
- Single space around + and |
- No space before @, single space after scale
- No space inside {} or []
- Consistent modification formatting
"""

import re
from typing import Any

try:
    from lsprotocol import types
except ImportError:
    types = None


def format_cdl(text: str, options: Any | None = None) -> list[Any]:
    """
    Format a CDL document.

    Args:
        text: Document text
        options: Formatting options (tab size, etc.)

    Returns:
        List of TextEdit objects
    """
    if types is None:
        return []

    edits: list[Any] = []
    lines = text.split("\n")

    for line_num, line in enumerate(lines):
        formatted = format_line(line)
        if formatted != line:
            edits.append(
                types.TextEdit(
                    range=types.Range(
                        start=types.Position(line=line_num, character=0),
                        end=types.Position(line=line_num, character=len(line)),
                    ),
                    new_text=formatted,
                )
            )

    return edits


def format_line(line: str) -> str:
    """
    Format a single CDL line.

    Args:
        line: Line content

    Returns:
        Formatted line
    """
    # Preserve leading whitespace
    leading_ws = ""
    content = line
    ws_match = re.match(r"^(\s*)", line)
    if ws_match:
        leading_ws = ws_match.group(1)
        content = line[len(leading_ws) :]

    # Skip empty lines
    if not content.strip():
        return line

    # Skip comments (preserve as-is)
    if content.strip().startswith("#"):
        return line

    formatted = content

    # 1. Lowercase crystal system names
    formatted = re.sub(
        r"^(Cubic|Tetragonal|Orthorhombic|Hexagonal|Trigonal|Monoclinic|Triclinic)\b",
        lambda m: m.group(1).lower(),
        formatted,
        flags=re.IGNORECASE,
    )

    # 2. Normalize spacing around + (form addition)
    # Before: {111}+{100}, {111}  +  {100}
    # After: {111} + {100}
    formatted = re.sub(r"\s*\+\s*", " + ", formatted)

    # 3. Normalize spacing around | (modification separator)
    # Before: {111}|twin(...), {111}  |  twin(...)
    # After: {111} | twin(...)
    formatted = re.sub(r"\s*\|\s*", " | ", formatted)

    # 4. No space before @
    # Before: {111} @1.0
    # After: {111}@1.0
    formatted = re.sub(r"\s+@", "@", formatted)

    # 5. No space inside {} for Miller indices
    # Before: { 111 }, {1 1 1}
    # After: {111}
    formatted = re.sub(
        r"\{\s*([^}]+?)\s*\}", lambda m: "{" + m.group(1).replace(" ", "") + "}", formatted
    )

    # 6. No space inside [] for point group
    # Before: [ m3m ]
    # After: [m3m]
    formatted = re.sub(r"\[\s*([^\]]+?)\s*\]", lambda m: "[" + m.group(1).strip() + "]", formatted)

    # 7. No space after [ or before ]
    formatted = re.sub(r"\[\s+", "[", formatted)
    formatted = re.sub(r"\s+\]", "]", formatted)

    # 8. Single space after : when followed by form/miller
    # Before: cubic[m3m]:  {111}
    # After: cubic[m3m]:{111}
    formatted = re.sub(r":\s+", ":", formatted)

    # 9. Normalize modification calls - no space before (
    # Before: twin ( spinel )
    # After: twin(spinel)
    for mod in ["elongate", "truncate", "taper", "bevel", "twin"]:
        # Fix space before parenthesis
        formatted = re.sub(rf"({mod})\s+\(", r"\1(", formatted, flags=re.IGNORECASE)
        # Fix spaces inside parentheses
        pattern = rf"({mod})\(\s*([^)]*?)\s*\)"
        formatted = re.sub(
            pattern, lambda m: f"{m.group(1)}({m.group(2).strip()})", formatted, flags=re.IGNORECASE
        )

    # 10. Lowercase modification names
    for mod in ["Elongate", "Truncate", "Taper", "Bevel", "Twin"]:
        formatted = re.sub(rf"\b{mod}\b", mod.lower(), formatted)

    # 11. Normalize colon-separated parameters in modifications
    # Before: elongate(c : 1.5)
    # After: elongate(c:1.5)
    formatted = re.sub(r"(\w)\s*:\s*(\d)", r"\1:\2", formatted)
    formatted = re.sub(r"(\w)\s*:\s*([a-z])", r"\1:\2", formatted, flags=re.IGNORECASE)

    # 12. Fix double spaces
    formatted = re.sub(r"  +", " ", formatted)

    # 13. Trim trailing whitespace
    formatted = formatted.rstrip()

    return leading_ws + formatted


def format_range(
    text: str, start_line: int, end_line: int, options: Any | None = None
) -> list[Any]:
    """
    Format a range within a CDL document.

    Args:
        text: Full document text
        start_line: Start line (0-based, inclusive)
        end_line: End line (0-based, inclusive)
        options: Formatting options

    Returns:
        List of TextEdit objects
    """
    if types is None:
        return []

    edits: list[Any] = []
    lines = text.split("\n")

    for line_num in range(start_line, min(end_line + 1, len(lines))):
        line = lines[line_num]
        formatted = format_line(line)
        if formatted != line:
            edits.append(
                types.TextEdit(
                    range=types.Range(
                        start=types.Position(line=line_num, character=0),
                        end=types.Position(line=line_num, character=len(line)),
                    ),
                    new_text=formatted,
                )
            )

    return edits
