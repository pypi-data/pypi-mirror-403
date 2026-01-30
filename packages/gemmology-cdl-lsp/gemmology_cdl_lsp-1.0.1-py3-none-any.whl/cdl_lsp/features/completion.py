"""
CDL Completions - Context-aware code completion for CDL documents.

This module provides intelligent completions based on the current
cursor position and context within the CDL syntax.
"""

import re
from enum import Enum, auto
from typing import Any

try:
    from lsprotocol import types
except ImportError:
    types = None

from ..constants import (
    COMMON_MILLER_INDICES,
    COMMON_SCALES,
    CRYSTAL_SYSTEMS,
    DEFAULT_POINT_GROUPS,
    FORM_DOCS,
    MODIFICATION_DOCS,
    MODIFICATIONS,
    NAMED_FORMS,
    POINT_GROUP_DOCS,
    POINT_GROUPS,
    SYSTEM_DOCS,
    TWIN_LAW_DOCS,
    TWIN_LAWS,
)
from .snippets import get_preset_snippets


class CompletionContext(Enum):
    """Context types for completion."""

    EMPTY = auto()  # Empty line or start of line
    SYSTEM = auto()  # Inside or after system name
    POINT_GROUP = auto()  # Inside brackets [...]
    AFTER_COLON = auto()  # After : expecting forms
    MILLER_INDEX = auto()  # Inside {} for Miller index
    FORM_NAME = auto()  # Expecting form name
    AFTER_AT = auto()  # After @ expecting scale
    AFTER_PLUS = auto()  # After + expecting another form
    AFTER_PIPE = auto()  # After | expecting modification or twin
    MODIFICATION = auto()  # Inside modification name
    MODIFICATION_PARAM = auto()  # Inside modification parameters
    TWIN_LAW = auto()  # Inside twin() parameters
    UNKNOWN = auto()


def _detect_context(line: str, col: int) -> tuple[CompletionContext, str]:
    """
    Detect the completion context based on cursor position.

    Args:
        line: Current line text
        col: Column position (0-based)

    Returns:
        Tuple of (context, current_word)
    """
    text_before = line[:col]
    text_before_stripped = text_before.rstrip()

    # Extract current word being typed
    word_match = re.search(r"[\w_-]+$", text_before)
    current_word = word_match.group(0) if word_match else ""

    # Empty or start of line
    if not text_before_stripped:
        return (CompletionContext.EMPTY, current_word)

    # Inside twin()
    twin_match = re.search(r"twin\s*\(\s*(\w*)$", text_before, re.IGNORECASE)
    if twin_match:
        return (CompletionContext.TWIN_LAW, twin_match.group(1))

    # Inside modification parameters
    for mod in ["elongate", "truncate", "taper", "bevel"]:
        mod_match = re.search(rf"{mod}\s*\([^)]*$", text_before, re.IGNORECASE)
        if mod_match:
            return (CompletionContext.MODIFICATION_PARAM, current_word)

    # Inside Miller index {}
    brace_match = re.search(r"\{[^}]*$", text_before)
    if brace_match:
        # Get content inside braces
        inside = brace_match.group(0)[1:]  # Remove leading {
        return (CompletionContext.MILLER_INDEX, inside)

    # After @
    if text_before_stripped.endswith("@"):
        return (CompletionContext.AFTER_AT, "")

    # Inside point group brackets
    bracket_match = re.search(r"\[[^\]]*$", text_before)
    if bracket_match:
        inside = bracket_match.group(0)[1:]  # Remove leading [
        return (CompletionContext.POINT_GROUP, inside)

    # After |
    if text_before_stripped.endswith("|") or re.search(r"\|\s*\w*$", text_before):
        return (CompletionContext.AFTER_PIPE, current_word)

    # After +
    if text_before_stripped.endswith("+") or re.search(r"\+\s*$", text_before):
        return (CompletionContext.AFTER_PLUS, "")

    # After :
    if ":" in text_before and not re.search(r"\{[^}]+\}", text_before):
        # After colon but no forms yet
        if text_before_stripped.endswith(":") or re.search(r":\s*\w*$", text_before):
            return (CompletionContext.AFTER_COLON, current_word)

    # Check if we have a system already
    system_match = re.match(r"(\w+)\s*(?:\[|$)", text_before)
    if system_match:
        system_name = system_match.group(1).lower()
        if system_name in CRYSTAL_SYSTEMS:
            # Check if we're still typing system or moving on
            if col <= len(system_match.group(1)):
                return (CompletionContext.SYSTEM, current_word)
            # After system name
            if "[" in text_before:
                return (CompletionContext.POINT_GROUP, current_word)
            return (CompletionContext.SYSTEM, current_word)

    # Default to expecting system
    if current_word and any(s.startswith(current_word.lower()) for s in CRYSTAL_SYSTEMS):
        return (CompletionContext.SYSTEM, current_word)

    return (CompletionContext.EMPTY, current_word)


def _get_system_from_line(line: str) -> str | None:
    """Extract the crystal system from a CDL line."""
    match = re.match(r"(\w+)", line)
    if match:
        system = match.group(1).lower()
        if system in CRYSTAL_SYSTEMS:
            return system
    return None


def _create_completion_item(
    label: str,
    kind: Any = None,
    detail: str = "",
    documentation: str = "",
    insert_text: str | None = None,
    sort_text: str | None = None,
) -> Any:
    """Create a completion item."""
    if types is None:
        return {
            "label": label,
            "kind": kind,
            "detail": detail,
            "documentation": documentation,
            "insert_text": insert_text or label,
        }

    return types.CompletionItem(
        label=label,
        kind=kind or types.CompletionItemKind.Keyword,
        detail=detail,
        documentation=types.MarkupContent(kind=types.MarkupKind.Markdown, value=documentation)
        if documentation
        else None,
        insert_text=insert_text,
        sort_text=sort_text,
    )


def get_completions(line: str, col: int, trigger_character: str | None = None) -> list[Any]:
    """
    Get completion items for the current position.

    Args:
        line: Current line text
        col: Column position (0-based)
        trigger_character: The character that triggered completion (if any)

    Returns:
        List of completion items
    """
    context, current_word = _detect_context(line, col)
    items: list[Any] = []

    kind = types.CompletionItemKind if types else None

    if context == CompletionContext.EMPTY:
        # Filter by current word if user is typing something
        prefix = current_word.lower() if current_word else ""

        # Suggest crystal systems (filtered by prefix if applicable)
        for system in sorted(CRYSTAL_SYSTEMS):
            if prefix and not system.startswith(prefix):
                continue
            doc = SYSTEM_DOCS.get(system, "")
            items.append(
                _create_completion_item(
                    label=system,
                    kind=kind.Keyword if kind else "Keyword",
                    detail=f"Crystal system (default: {DEFAULT_POINT_GROUPS[system]})",
                    documentation=doc,
                    insert_text=f"{system}[{DEFAULT_POINT_GROUPS[system]}]:",
                    sort_text="0" + system,  # Systems first
                )
            )

        # Suggest preset snippets (filtered by prefix) - these expand to full CDL
        snippets = get_preset_snippets(prefix)
        items.extend(snippets)

    elif context == CompletionContext.SYSTEM:
        # Suggest crystal systems matching prefix
        prefix = current_word.lower()
        for system in sorted(CRYSTAL_SYSTEMS):
            if system.startswith(prefix):
                doc = SYSTEM_DOCS.get(system, "")
                items.append(
                    _create_completion_item(
                        label=system,
                        kind=kind.Keyword if kind else "Keyword",
                        detail=f"Crystal system (default: {DEFAULT_POINT_GROUPS[system]})",
                        documentation=doc,
                        insert_text=f"{system}[{DEFAULT_POINT_GROUPS[system]}]:",
                        sort_text="0" + system,  # Systems first
                    )
                )

        # Also suggest matching preset snippets
        snippets = get_preset_snippets(prefix)
        items.extend(snippets)

    elif context == CompletionContext.POINT_GROUP:
        # Suggest point groups for the current system
        system = _get_system_from_line(line)
        prefix = current_word.lower()

        if system and system in POINT_GROUPS:
            groups = POINT_GROUPS[system]
        else:
            # Fallback to all point groups
            groups = set()
            for s_groups in POINT_GROUPS.values():
                groups.update(s_groups)

        for pg in sorted(groups):
            if pg.lower().startswith(prefix) or not prefix:
                doc = POINT_GROUP_DOCS.get(pg, "")
                is_default = system and pg == DEFAULT_POINT_GROUPS.get(system)
                detail = f"Point group{' (default)' if is_default else ''}"
                items.append(
                    _create_completion_item(
                        label=pg,
                        kind=kind.EnumMember if kind else "EnumMember",
                        detail=detail,
                        documentation=doc,
                        sort_text="0" + pg if is_default else "1" + pg,
                    )
                )

    elif context in (
        CompletionContext.AFTER_COLON,
        CompletionContext.AFTER_PLUS,
        CompletionContext.FORM_NAME,
    ):
        # Suggest named forms and Miller index start
        prefix = current_word.lower()

        # Named forms
        for form_name in sorted(NAMED_FORMS.keys()):
            if form_name.startswith(prefix) or not prefix:
                miller = NAMED_FORMS[form_name]
                doc = FORM_DOCS.get(form_name, "")
                items.append(
                    _create_completion_item(
                        label=form_name,
                        kind=kind.Value if kind else "Value",
                        detail=f"{{{miller[0]}{miller[1]}{miller[2]}}}",
                        documentation=doc,
                    )
                )

        # Miller index start
        items.append(
            _create_completion_item(
                label="{",
                kind=kind.Snippet if kind else "Snippet",
                detail="Miller index",
                documentation="Enter a Miller index like {111}, {100}, or {10-10}",
                insert_text="{",
            )
        )

    elif context == CompletionContext.MILLER_INDEX:
        # Suggest common Miller indices for the current system
        system = _get_system_from_line(line)
        indices = COMMON_MILLER_INDICES.get(system or "cubic", COMMON_MILLER_INDICES["cubic"])

        for idx in indices:
            # Remove outer braces for insertion since we're inside {}
            inner = idx[1:-1]
            items.append(
                _create_completion_item(
                    label=idx,
                    kind=kind.Value if kind else "Value",
                    detail="Miller index",
                    insert_text=inner + "}",
                )
            )

    elif context == CompletionContext.AFTER_AT:
        # Suggest common scale values
        for scale in COMMON_SCALES:
            items.append(
                _create_completion_item(
                    label=scale,
                    kind=kind.Value if kind else "Value",
                    detail="Scale factor",
                    documentation=f"Scale the form by {scale}",
                )
            )

    elif context == CompletionContext.AFTER_PIPE:
        # Suggest modifications and twin
        prefix = current_word.lower()

        for mod in sorted(MODIFICATIONS):
            if mod.startswith(prefix) or not prefix:
                doc = MODIFICATION_DOCS.get(mod, "")
                items.append(
                    _create_completion_item(
                        label=mod,
                        kind=kind.Function if kind else "Function",
                        detail="Modification" if mod != "twin" else "Twin operation",
                        documentation=doc,
                        insert_text=f"{mod}(",
                    )
                )

    elif context == CompletionContext.TWIN_LAW:
        # Suggest twin laws
        prefix = current_word.lower()

        for law in sorted(TWIN_LAWS):
            if law.startswith(prefix) or not prefix:
                doc = TWIN_LAW_DOCS.get(law, "")
                items.append(
                    _create_completion_item(
                        label=law,
                        kind=kind.EnumMember if kind else "EnumMember",
                        detail="Twin law",
                        documentation=doc,
                        insert_text=f"{law})",
                    )
                )

    elif context == CompletionContext.MODIFICATION_PARAM:
        # Context-sensitive parameter completions
        # Detect which modification we're in
        for mod in ["elongate", "truncate", "taper", "bevel"]:
            if re.search(rf"{mod}\s*\(", line, re.IGNORECASE):
                if mod == "elongate":
                    for axis in ["a", "b", "c"]:
                        items.append(
                            _create_completion_item(
                                label=f"{axis}:",
                                kind=kind.Property if kind else "Property",
                                detail="Axis parameter",
                                documentation=f"Elongate along {axis}-axis",
                            )
                        )
                elif mod == "truncate":
                    # Suggest forms for truncation
                    for form_name in sorted(NAMED_FORMS.keys()):
                        miller = NAMED_FORMS[form_name]
                        items.append(
                            _create_completion_item(
                                label=f"{form_name}:",
                                kind=kind.Value if kind else "Value",
                                detail=f"{{{miller[0]}{miller[1]}{miller[2]}}}",
                            )
                        )
                break

    return items
