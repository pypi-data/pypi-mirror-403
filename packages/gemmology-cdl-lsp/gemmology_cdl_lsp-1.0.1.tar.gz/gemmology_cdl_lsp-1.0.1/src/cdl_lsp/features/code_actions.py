"""
CDL Code Actions - Quick fixes and refactorings for CDL documents.

This module provides code actions (quick fixes) for CDL documents,
primarily for fixing typos detected by diagnostics.
"""

from typing import Any

try:
    from lsprotocol import types
except ImportError:
    types = None


def get_code_actions(uri: str, range_: Any, diagnostics: list[Any]) -> list[Any]:
    """
    Generate code actions (quick fixes) for the given diagnostics.

    Args:
        uri: Document URI
        range_: The range in the document for which code actions are requested
        diagnostics: List of diagnostics in the range

    Returns:
        List of CodeAction objects
    """
    if types is None:
        return []

    actions: list[Any] = []

    for diag in diagnostics:
        # Check if diagnostic has a code that we can fix
        if not hasattr(diag, "code") or not diag.code:
            continue

        code = diag.code
        data = diag.data if hasattr(diag, "data") else None

        action = None

        # Syntax fixes (insert operations)
        if code == "missing-colon" and data:
            action = _create_insert_fix(uri, diag, data)

        # Typo fixes (replace operations)
        elif code in ("typo-form", "typo-twin", "typo-system", "typo-modification") and data:
            action = _create_typo_fix(uri, diag, data)

        # Scale fixes (replace operations, same pattern as typo)
        elif code in ("scale-large", "scale-small") and data:
            action = _create_typo_fix(uri, diag, data)

        if action:
            actions.append(action)

    return actions


def _create_typo_fix(uri: str, diag: Any, data: dict) -> Any | None:
    """
    Create a quick fix for a typo diagnostic.

    Args:
        uri: Document URI
        diag: The diagnostic object
        data: Diagnostic data containing suggested fix

    Returns:
        CodeAction for fixing the typo, or None if not possible
    """
    if types is None:
        return None

    suggested = data.get("suggested")
    original = data.get("original", "")

    if not suggested:
        return None

    # Create the text edit to replace the typo
    text_edit = types.TextEdit(range=diag.range, new_text=suggested)

    # Create workspace edit
    workspace_edit = types.WorkspaceEdit(changes={uri: [text_edit]})

    # Create the code action
    return types.CodeAction(
        title=f"Change '{original}' to '{suggested}'",
        kind=types.CodeActionKind.QuickFix,
        diagnostics=[diag],
        edit=workspace_edit,
        is_preferred=True,  # Mark as preferred fix
    )


def _create_insert_fix(uri: str, diag: Any, data: dict) -> Any | None:
    """
    Create a quick fix that inserts text at a position.

    Args:
        uri: Document URI
        diag: The diagnostic object
        data: Diagnostic data containing insert position and text

    Returns:
        CodeAction for inserting text, or None if not possible
    """
    if types is None:
        return None

    insert_text = data.get("insert_text", ":")

    if not insert_text:
        return None

    # Insert at the start of the diagnostic range (zero-width insert)
    text_edit = types.TextEdit(
        range=types.Range(
            start=diag.range.start,
            end=diag.range.start,  # Zero-width for insert
        ),
        new_text=insert_text,
    )

    # Create workspace edit
    workspace_edit = types.WorkspaceEdit(changes={uri: [text_edit]})

    # Create the code action
    return types.CodeAction(
        title=f"Insert '{insert_text}'",
        kind=types.CodeActionKind.QuickFix,
        diagnostics=[diag],
        edit=workspace_edit,
        is_preferred=True,  # Mark as preferred fix
    )


def get_code_action_kinds() -> list[str]:
    """Get the list of supported code action kinds."""
    if types is None:
        return ["quickfix"]
    return [types.CodeActionKind.QuickFix]
