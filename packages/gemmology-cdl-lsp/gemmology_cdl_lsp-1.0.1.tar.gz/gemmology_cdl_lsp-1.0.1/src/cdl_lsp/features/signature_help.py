"""
CDL Signature Help - Parameter hints for modifications and twins.

This module provides signature help that shows parameter information
when typing modifications like elongate(), truncate(), or twin().
"""

import re
from typing import Any

try:
    from lsprotocol import types
except ImportError:
    types = None


# Modification signatures with parameter documentation
MODIFICATION_SIGNATURES = {
    "elongate": {
        "label": "elongate(axis:ratio)",
        "documentation": "Stretches the crystal along the specified axis.",
        "parameters": [
            {"label": "axis", "documentation": "Crystallographic axis: a, b, or c"},
            {
                "label": "ratio",
                "documentation": "Scale factor (>1 elongates, <1 shortens). Example: 1.5",
            },
        ],
    },
    "truncate": {
        "label": "truncate(form:depth)",
        "documentation": "Truncates the crystal by cutting off corners or edges.",
        "parameters": [
            {
                "label": "form",
                "documentation": "Named form (e.g., cube) or Miller index (e.g., {100})",
            },
            {
                "label": "depth",
                "documentation": "Truncation depth from 0 (none) to 1 (full). Example: 0.3",
            },
        ],
    },
    "taper": {
        "label": "taper(direction:factor)",
        "documentation": "Tapers the crystal in the specified direction.",
        "parameters": [
            {"label": "direction", "documentation": "Taper direction: +c, -c, +a, -a, +b, -b"},
            {"label": "factor", "documentation": "Taper factor (0-1). Example: 0.5"},
        ],
    },
    "bevel": {
        "label": "bevel(edges:width)",
        "documentation": "Bevels (chamfers) the specified edges of the crystal.",
        "parameters": [
            {"label": "edges", "documentation": "Edge set to bevel: all, vertical, horizontal"},
            {
                "label": "width",
                "documentation": "Bevel width relative to edge length. Example: 0.1",
            },
        ],
    },
    "twin": {
        "label": "twin(law, count?)",
        "documentation": "Creates a twinned crystal using the specified twin law.",
        "parameters": [
            {
                "label": "law",
                "documentation": "Twin law name: spinel, brazil, dauphine, japan, carlsbad, baveno, manebach, albite, trilling, fluorite, staurolite_60, staurolite_90, iron_cross, gypsum_swallow",
            },
            {
                "label": "count",
                "documentation": "Number of individuals for cyclic twins (optional). Example: 3 for trilling",
            },
        ],
    },
}


def _find_active_modification(line: str, col: int) -> tuple[str | None, int]:
    """
    Find which modification (if any) the cursor is inside.

    Args:
        line: Current line text
        col: Column position (0-based)

    Returns:
        Tuple of (modification_name, active_parameter_index)
    """
    text_before = line[:col]

    # Search for modification patterns
    for mod_name in MODIFICATION_SIGNATURES:
        # Pattern: mod_name( with possible content after
        pattern = rf"{mod_name}\s*\("
        for match in re.finditer(pattern, text_before, re.IGNORECASE):
            # Check if we're still inside this call (no closing paren)
            after_open = text_before[match.end() :]
            if ")" not in after_open:
                # Count parameters (commas) to determine active parameter
                param_content = after_open
                # Count colons and commas to estimate parameter
                # Parameters are separated by : for axis:ratio format
                # or , for multiple parameters like twin(law, count)
                colon_count = param_content.count(":")
                comma_count = param_content.count(",")

                # For twin(), params are comma-separated
                # For others, they're colon-separated within a single param
                if mod_name == "twin":
                    active_param = comma_count
                else:
                    active_param = colon_count

                return (
                    mod_name,
                    min(active_param, len(MODIFICATION_SIGNATURES[mod_name]["parameters"]) - 1),
                )

    return (None, 0)


def get_signature_help(line: str, col: int) -> Any | None:
    """
    Get signature help for the current position.

    Args:
        line: Current line text
        col: Column position (0-based)

    Returns:
        SignatureHelp object or None if not in a modification call
    """
    if types is None:
        return None

    mod_name, active_param = _find_active_modification(line, col)

    if mod_name is None:
        return None

    sig_info = MODIFICATION_SIGNATURES.get(mod_name)
    if sig_info is None:
        return None

    # Build parameter information
    parameters = []
    for param in sig_info["parameters"]:
        parameters.append(
            types.ParameterInformation(
                label=param["label"],
                documentation=types.MarkupContent(
                    kind=types.MarkupKind.Markdown, value=param["documentation"]
                ),
            )
        )

    # Create signature
    signature = types.SignatureInformation(
        label=sig_info["label"],
        documentation=types.MarkupContent(
            kind=types.MarkupKind.Markdown, value=sig_info["documentation"]
        ),
        parameters=parameters,
        active_parameter=active_param,
    )

    return types.SignatureHelp(
        signatures=[signature], active_signature=0, active_parameter=active_param
    )


def get_signature_trigger_characters() -> list:
    """Get the characters that trigger signature help."""
    return ["(", ","]
