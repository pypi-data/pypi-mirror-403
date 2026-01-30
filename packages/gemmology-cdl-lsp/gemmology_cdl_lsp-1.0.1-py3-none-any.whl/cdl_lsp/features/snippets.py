"""
CDL Snippets - Gemstone preset snippets for CDL documents.

This module provides snippet completions that expand gemstone names
into full CDL definitions with metadata.
"""

import os
import sys
from typing import Any

# Add scripts directory to path for imports
_scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

try:
    from lsprotocol import types
except ImportError:
    types = None


def _get_presets() -> dict:
    """Load presets from crystal_presets module."""
    try:
        from crystal_presets import CRYSTAL_PRESETS

        return CRYSTAL_PRESETS
    except ImportError:
        return {}


def _create_snippet_item(name: str, preset: dict, sort_prefix: str = "") -> Any:
    """Create a completion item for a preset snippet."""
    cdl = preset.get("cdl", "")
    display_name = preset.get("name", name)
    preset.get("system", "unknown")
    chemistry = preset.get("chemistry", "")
    hardness = preset.get("hardness", "")

    # Build documentation
    doc_parts = [f"**{display_name}**\n"]
    if chemistry:
        doc_parts.append(f"Chemistry: {chemistry}")
    if hardness:
        doc_parts.append(f"Hardness: {hardness}")

    # Add optical properties if available
    ri = preset.get("ri", "")
    sg = preset.get("sg", "")
    if ri:
        doc_parts.append(f"RI: {ri}")
    if sg:
        doc_parts.append(f"SG: {sg}")

    doc_parts.append(f"\n**Expands to:**\n```cdl\n{cdl}\n```")

    documentation = "\n".join(doc_parts)

    # Detail shows CDL expansion hint
    detail = f"→ {cdl[:40]}{'...' if len(cdl) > 40 else ''}"

    if types is None:
        return {
            "label": name,
            "kind": "Snippet",
            "detail": detail,
            "documentation": documentation,
            "insert_text": cdl,
            "insert_text_format": 2,  # Snippet format
        }

    return types.CompletionItem(
        label=name,
        kind=types.CompletionItemKind.Snippet,
        detail=detail,
        documentation=types.MarkupContent(kind=types.MarkupKind.Markdown, value=documentation),
        insert_text=cdl,
        insert_text_format=types.InsertTextFormat.PlainText,
        sort_text=sort_prefix + name,
    )


def get_preset_snippets(prefix: str = "") -> list[Any]:
    """
    Generate snippet completions from crystal presets.

    Args:
        prefix: Optional prefix to filter presets by name

    Returns:
        List of completion items for matching presets
    """
    presets = _get_presets()
    items = []

    prefix_lower = prefix.lower() if prefix else ""

    for name, preset in sorted(presets.items()):
        # Filter by prefix if provided
        if prefix_lower and not name.lower().startswith(prefix_lower):
            continue

        # Skip if preset has no CDL
        if "cdl" not in preset:
            continue

        # Give presets higher priority when prefix matches (sort before systems)
        # When no prefix, use '1' so systems appear first
        sort_prefix = "0" if prefix_lower else "1"
        items.append(_create_snippet_item(name, preset, sort_prefix=sort_prefix))

    return items


def get_snippet_for_preset(preset_name: str) -> str | None:
    """
    Get the CDL snippet for a specific preset.

    Args:
        preset_name: Name of the preset

    Returns:
        CDL string or None if preset not found
    """
    presets = _get_presets()
    preset = presets.get(preset_name)
    if preset and "cdl" in preset:
        return preset["cdl"]
    return None


def list_preset_names() -> list[str]:
    """Get list of all available preset names."""
    presets = _get_presets()
    return sorted(presets.keys())
