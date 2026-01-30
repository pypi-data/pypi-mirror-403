"""
CDL Document Symbols - Outline view for CDL documents.

This module provides document symbols that create an outline view
showing crystal definitions, forms, and modifications in the sidebar.
"""

import re
from typing import Any

try:
    from lsprotocol import types
except ImportError:
    types = None


def get_document_symbols(text: str) -> list[Any]:
    """
    Extract symbols from a CDL document.

    Symbols include:
    - Crystal definitions (system[point_group])
    - Forms ({hkl} or named forms)
    - Modifications (twin, elongate, etc.)

    Args:
        text: CDL document text

    Returns:
        List of DocumentSymbol objects
    """
    if types is None:
        return []

    symbols: list[Any] = []
    lines = text.split("\n")

    for line_num, line in enumerate(lines):
        line_stripped = line.strip()

        # Skip empty lines and comments
        if not line_stripped or line_stripped.startswith("#"):
            continue

        # Parse the CDL line
        symbol = _parse_cdl_line(line, line_stripped, line_num)
        if symbol:
            symbols.append(symbol)

    return symbols


def _parse_cdl_line(original_line: str, line: str, line_num: int) -> Any | None:
    """
    Parse a CDL line and create a DocumentSymbol.

    Args:
        original_line: Original line with leading whitespace
        line: Stripped line content
        line_num: Line number (0-based)

    Returns:
        DocumentSymbol or None
    """
    if types is None:
        return None

    # Match system and point group
    system_match = re.match(r"(\w+)\s*\[([^\]]+)\]", line)
    if not system_match:
        return None

    system = system_match.group(1)
    point_group = system_match.group(2)

    # Calculate range for the entire line
    start_col = len(original_line) - len(original_line.lstrip())
    line_range = types.Range(
        start=types.Position(line=line_num, character=start_col),
        end=types.Position(line=line_num, character=len(original_line)),
    )

    # Selection range is just the system[pg] part
    selection_range = types.Range(
        start=types.Position(line=line_num, character=start_col),
        end=types.Position(line=line_num, character=start_col + system_match.end()),
    )

    # Extract children (forms and modifications)
    children = _extract_children(line, line_num, start_col)

    # Create the main symbol
    return types.DocumentSymbol(
        name=f"{system}[{point_group}]",
        kind=types.SymbolKind.Class,
        range=line_range,
        selection_range=selection_range,
        detail=f"Crystal ({system})",
        children=children if children else None,
    )


def _extract_children(line: str, line_num: int, base_col: int) -> list[Any]:
    """
    Extract form and modification symbols from a CDL line.

    Args:
        line: CDL line content
        line_num: Line number
        base_col: Base column offset

    Returns:
        List of child DocumentSymbol objects
    """
    if types is None:
        return []

    children: list[Any] = []

    # Find Miller indices {hkl}
    for match in re.finditer(r"\{([^}]+)\}", line):
        miller = match.group(1)
        start = match.start()
        end = match.end()

        children.append(
            types.DocumentSymbol(
                name=f"{{{miller}}}",
                kind=types.SymbolKind.Field,
                range=types.Range(
                    start=types.Position(line=line_num, character=base_col + start),
                    end=types.Position(line=line_num, character=base_col + end),
                ),
                selection_range=types.Range(
                    start=types.Position(line=line_num, character=base_col + start),
                    end=types.Position(line=line_num, character=base_col + end),
                ),
                detail="Miller index",
            )
        )

    # Find named forms (after : and before @, +, |)
    form_pattern = r":(\w+)(?=[@+|]|$)"
    for match in re.finditer(form_pattern, line):
        form_name = match.group(1)
        # Skip if it's a crystal system
        if form_name.lower() in (
            "cubic",
            "tetragonal",
            "orthorhombic",
            "hexagonal",
            "trigonal",
            "monoclinic",
            "triclinic",
        ):
            continue
        start = match.start(1)
        end = match.end(1)

        children.append(
            types.DocumentSymbol(
                name=form_name,
                kind=types.SymbolKind.Field,
                range=types.Range(
                    start=types.Position(line=line_num, character=base_col + start),
                    end=types.Position(line=line_num, character=base_col + end),
                ),
                selection_range=types.Range(
                    start=types.Position(line=line_num, character=base_col + start),
                    end=types.Position(line=line_num, character=base_col + end),
                ),
                detail="Named form",
            )
        )

    # Find modifications (elongate, truncate, taper, bevel, twin)
    mod_pattern = r"\b(elongate|truncate|taper|bevel|twin)\s*\(([^)]*)\)"
    for match in re.finditer(mod_pattern, line, re.IGNORECASE):
        mod_name = match.group(1)
        mod_params = match.group(2)
        start = match.start()
        end = match.end()

        children.append(
            types.DocumentSymbol(
                name=f"{mod_name}({mod_params})" if mod_params else mod_name,
                kind=types.SymbolKind.Method
                if mod_name.lower() == "twin"
                else types.SymbolKind.Property,
                range=types.Range(
                    start=types.Position(line=line_num, character=base_col + start),
                    end=types.Position(line=line_num, character=base_col + end),
                ),
                selection_range=types.Range(
                    start=types.Position(line=line_num, character=base_col + match.start(1)),
                    end=types.Position(line=line_num, character=base_col + match.end(1)),
                ),
                detail="Twin law" if mod_name.lower() == "twin" else "Modification",
            )
        )

    return children
