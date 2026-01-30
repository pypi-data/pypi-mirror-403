"""
LSP feature implementations for CDL.

This package contains the individual feature modules:
- diagnostics: Error and warning detection
- completion: Context-aware code completion
- hover: Documentation on hover
- definition: Go to definition support
- snippets: Gemstone preset snippets
- code_actions: Quick fixes for typos
- signature_help: Parameter hints for modifications
- document_symbols: Outline view
- formatting: Auto-format CDL
- explain: CDL explanation
- preview: Crystal preview rendering
"""

from .code_actions import get_code_action_kinds, get_code_actions
from .completion import get_completions
from .definition import get_definition
from .diagnostics import DiagnosticInfo, get_diagnostics, validate_document
from .document_symbols import get_document_symbols
from .explain import explain_cdl, get_explain_result
from .formatting import format_cdl, format_line, format_range
from .hover import get_hover_info
from .preview import get_preview_capabilities, render_cdl_preview, render_cdl_preview_3d
from .signature_help import get_signature_help, get_signature_trigger_characters
from .snippets import get_preset_snippets, get_snippet_for_preset, list_preset_names

__all__ = [
    # Diagnostics
    "validate_document",
    "get_diagnostics",
    "DiagnosticInfo",
    # Completion
    "get_completions",
    # Hover
    "get_hover_info",
    # Definition
    "get_definition",
    # Snippets
    "get_preset_snippets",
    "get_snippet_for_preset",
    "list_preset_names",
    # Code Actions
    "get_code_actions",
    "get_code_action_kinds",
    # Signature Help
    "get_signature_help",
    "get_signature_trigger_characters",
    # Document Symbols
    "get_document_symbols",
    # Formatting
    "format_cdl",
    "format_line",
    "format_range",
    # Explain
    "explain_cdl",
    "get_explain_result",
    # Preview
    "render_cdl_preview",
    "render_cdl_preview_3d",
    "get_preview_capabilities",
]
