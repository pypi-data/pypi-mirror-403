"""
CDL Diagnostics - Error and warning detection for CDL documents.

This module provides validation of CDL syntax and semantics,
generating LSP diagnostics for errors and warnings.
"""

import re
from dataclasses import dataclass
from typing import Any

# Import cdl_parser for parsing
try:
    from cdl_parser import parse_cdl as _parse_cdl

    CDL_PARSER_AVAILABLE = True
except ImportError:
    CDL_PARSER_AVAILABLE = False
    _parse_cdl = None

try:
    from lsprotocol import types
except ImportError:
    # Fallback for testing without lsprotocol
    types = None

from ..constants import (
    ALL_POINT_GROUPS,
    CRYSTAL_SYSTEMS,
    POINT_GROUPS,
    TWIN_LAWS,
    validate_point_group_for_system,
)

# Try to import presets for validation
try:
    from crystal_presets import CRYSTAL_PRESETS, list_presets

    PRESETS_AVAILABLE = True
except ImportError:
    CRYSTAL_PRESETS = {}
    PRESETS_AVAILABLE = False

    def list_presets(category=None):
        return []


@dataclass
class DiagnosticInfo:
    """Diagnostic information without LSP types dependency."""

    line: int
    start_char: int
    end_char: int
    message: str
    severity: str  # 'error', 'warning', 'information', 'hint'
    source: str = "cdl"
    code: str | None = None  # e.g., "typo-form", "typo-twin"
    data: dict | None = None  # e.g., {"suggested": "octahedron"}


def _get_severity(severity_str: str) -> Any:
    """Convert severity string to LSP DiagnosticSeverity."""
    if types is None:
        return severity_str

    severity_map = {
        "error": types.DiagnosticSeverity.Error,
        "warning": types.DiagnosticSeverity.Warning,
        "information": types.DiagnosticSeverity.Information,
        "hint": types.DiagnosticSeverity.Hint,
    }
    return severity_map.get(severity_str, types.DiagnosticSeverity.Error)


def _create_diagnostic(info: DiagnosticInfo) -> Any:
    """Create an LSP Diagnostic from DiagnosticInfo."""
    if types is None:
        return info

    return types.Diagnostic(
        range=types.Range(
            start=types.Position(line=info.line, character=info.start_char),
            end=types.Position(line=info.line, character=info.end_char),
        ),
        message=info.message,
        severity=_get_severity(info.severity),
        source=info.source,
        code=info.code,
        data=info.data,
    )


def _find_position(text: str, char_pos: int) -> tuple[int, int]:
    """Convert character position to (line, column)."""
    line = 0
    col = 0
    for i, ch in enumerate(text):
        if i == char_pos:
            return (line, col)
        if ch == "\n":
            line += 1
            col = 0
        else:
            col += 1
    return (line, col)


def _extract_error_position(error_msg: str) -> int | None:
    """Extract position from parser error message."""
    # Pattern: "at position N"
    match = re.search(r"at position (\d+)", error_msg)
    if match:
        return int(match.group(1))
    return None


def validate_document(text: str) -> list[DiagnosticInfo]:
    """
    Validate CDL document and return diagnostics.

    This performs both syntactic validation (using the parser) and
    semantic validation (additional checks).

    Args:
        text: CDL document text

    Returns:
        List of DiagnosticInfo objects
    """
    diagnostics: list[DiagnosticInfo] = []

    # Skip empty documents
    text = text.strip()
    if not text:
        return diagnostics

    # Process each line separately for multi-line CDL support
    lines = text.split("\n")

    for line_num, line_text in enumerate(lines):
        line_text = line_text.strip()

        # Skip empty lines and comments
        if not line_text or line_text.startswith("#"):
            continue

        # Validate the line
        line_diagnostics = _validate_cdl_line(line_text, line_num)
        diagnostics.extend(line_diagnostics)

    return diagnostics


def _validate_cdl_line(line_text: str, line_num: int) -> list[DiagnosticInfo]:
    """Validate a single CDL line."""
    diagnostics: list[DiagnosticInfo] = []

    # Check if this is a preset name (single word matching a known preset)
    line_stripped = line_text.strip().lower()
    if PRESETS_AVAILABLE and line_stripped in CRYSTAL_PRESETS:
        # Valid preset name - no errors
        return diagnostics

    # First, check for common issues to provide better quick-fix diagnostics
    # These run before parser to catch errors with proper code/data for code actions
    pre_parse_diagnostics: list[DiagnosticInfo] = []

    # Check for syntax errors that we can provide quick fixes for
    _check_missing_colon(line_text, line_num, pre_parse_diagnostics)

    # Check for typos (system, modification, form, twin)
    _check_system_typos(line_text, line_num, pre_parse_diagnostics)
    _check_modification_typos(line_text, line_num, pre_parse_diagnostics)
    _check_form_typos(line_text, line_num, pre_parse_diagnostics)
    _check_twin_typos(line_text, line_num, pre_parse_diagnostics)

    # If we found issues with quick-fix data, return those
    if pre_parse_diagnostics:
        return pre_parse_diagnostics

    # Try parsing with the actual parser
    if CDL_PARSER_AVAILABLE and _parse_cdl is not None:
        try:
            _parse_cdl(line_text)
        except ValueError as e:
            error_msg = str(e)
            pos = _extract_error_position(error_msg)

            if pos is not None:
                # Use exact position from error
                end_pos = min(pos + 10, len(line_text))
                diagnostics.append(
                    DiagnosticInfo(
                        line=line_num,
                        start_char=pos,
                        end_char=end_pos,
                        message=error_msg,
                        severity="error",
                    )
                )
            else:
                # Fallback to full line
                diagnostics.append(
                    DiagnosticInfo(
                        line=line_num,
                        start_char=0,
                        end_char=len(line_text),
                        message=error_msg,
                        severity="error",
                    )
                )
            return diagnostics
        except Exception as e:
            # Unexpected error
            diagnostics.append(
                DiagnosticInfo(
                    line=line_num,
                    start_char=0,
                    end_char=len(line_text),
                    message=f"Unexpected error: {str(e)}",
                    severity="error",
                )
            )
            return diagnostics

    # Additional semantic validation (for valid parses)
    diagnostics.extend(_semantic_validation(line_text, line_num))

    return diagnostics


def _semantic_validation(line_text: str, line_num: int) -> list[DiagnosticInfo]:
    """Perform semantic validation beyond syntax checking."""
    diagnostics: list[DiagnosticInfo] = []

    # Check for unusually large scale values
    scale_pattern = r"@(\d+\.?\d*)"
    for match in re.finditer(scale_pattern, line_text):
        scale = float(match.group(1))
        if scale > 5.0:
            diagnostics.append(
                DiagnosticInfo(
                    line=line_num,
                    start_char=match.start(),
                    end_char=match.end(),
                    message=f"Scale value {scale} is unusually large (typical range: 0.1-3.0)",
                    severity="warning",
                    code="scale-large",
                    data={"suggested": "@3.0", "original": match.group(0)},
                )
            )
        elif scale < 0.1:
            diagnostics.append(
                DiagnosticInfo(
                    line=line_num,
                    start_char=match.start(),
                    end_char=match.end(),
                    message=f"Scale value {scale} is unusually small (typical range: 0.1-3.0)",
                    severity="warning",
                    code="scale-small",
                    data={"suggested": "@0.1", "original": match.group(0)},
                )
            )

    # Check for system-point group mismatch (if we can identify them)
    system_match = re.match(r"(\w+)\s*\[(\S+)\]", line_text)
    if system_match:
        system = system_match.group(1).lower()
        pg = system_match.group(2)

        if system in CRYSTAL_SYSTEMS and pg in ALL_POINT_GROUPS:
            if not validate_point_group_for_system(system, pg):
                diagnostics.append(
                    DiagnosticInfo(
                        line=line_num,
                        start_char=system_match.start(2),
                        end_char=system_match.end(2),
                        message=f"Point group '{pg}' is not valid for {system} system. "
                        f"Valid groups: {', '.join(sorted(POINT_GROUPS[system]))}",
                        severity="error",
                    )
                )

    # Note: Typo checks are now run before parsing in _validate_cdl_line
    # to ensure proper code/data fields are set for code actions

    return diagnostics


def _check_form_typos(line_text: str, line_num: int, diagnostics: list[DiagnosticInfo]) -> None:
    """Check for common form name typos."""
    # Common typos
    typos = {
        "octohedron": "octahedron",
        "octahedon": "octahedron",
        "dodecahedrom": "dodecahedron",
        "dodecahedon": "dodecahedron",
        "trisoctohedron": "trisoctahedron",
        "hexoctohedron": "hexoctahedron",
        "trapezohedon": "trapezohedron",
        "rhombohedon": "rhombohedron",
        "rhombohedrom": "rhombohedron",
        "scalenohedon": "scalenohedron",
        "dipyrmaid": "dipyramid",
        "dipyrmid": "dipyramid",
        "pinaciod": "pinacoid",
    }

    # Extract identifiers from line
    for word in re.findall(r"\b([a-z_]+)\b", line_text.lower()):
        if word in typos:
            start = line_text.lower().find(word)
            if start >= 0:
                suggested = typos[word]
                diagnostics.append(
                    DiagnosticInfo(
                        line=line_num,
                        start_char=start,
                        end_char=start + len(word),
                        message=f"Unknown form '{word}'. Did you mean '{suggested}'?",
                        severity="error",
                        code="typo-form",
                        data={"suggested": suggested, "original": word},
                    )
                )


def _check_twin_typos(line_text: str, line_num: int, diagnostics: list[DiagnosticInfo]) -> None:
    """Check for common twin law typos."""
    # Look for twin() calls
    twin_match = re.search(r"twin\s*\(\s*(\w+)", line_text)
    if twin_match:
        law_name = twin_match.group(1).lower()

        # Check common typos
        typos = {
            "spinell": "spinel",
            "spinel_law": "spinel",  # Alternative name
            "brazill": "brazil",
            "dauphina": "dauphine",
            "dauphene": "dauphine",
            "japn": "japan",
            "carlsbadt": "carlsbad",
            "carlsbadh": "carlsbad",
            "bavenow": "baveno",
            "mannebach": "manebach",
            "albight": "albite",
            "albit": "albite",
        }

        if law_name in typos and law_name not in TWIN_LAWS:
            start = twin_match.start(1)
            suggested = typos[law_name]
            diagnostics.append(
                DiagnosticInfo(
                    line=line_num,
                    start_char=start,
                    end_char=start + len(law_name),
                    message=f"Unknown twin law '{law_name}'. Did you mean '{suggested}'?",
                    severity="error",
                    code="typo-twin",
                    data={"suggested": suggested, "original": law_name},
                )
            )


def _check_missing_colon(line_text: str, line_num: int, diagnostics: list[DiagnosticInfo]) -> None:
    """Check for missing colon between point group and forms.

    Detects patterns like 'cubic[m3m]{111}' which should be 'cubic[m3m]:{111}'.
    """
    # Pattern: system[pg]{forms} - missing colon before brace
    # Match: word, optional whitespace, [...], optional whitespace, { (without colon)
    pattern = r"(\w+)\s*\[[^\]]+\]\s*(\{)"

    for match in re.finditer(pattern, line_text):
        # Check that there's no colon between ] and {
        bracket_end = line_text.find("]", match.start()) + 1
        brace_start = match.start(2)
        between = line_text[bracket_end:brace_start]

        if ":" not in between:
            diagnostics.append(
                DiagnosticInfo(
                    line=line_num,
                    start_char=brace_start,
                    end_char=brace_start + 1,
                    message="Missing colon before forms. Expected ':' before '{'",
                    severity="error",
                    code="missing-colon",
                    data={"insert_pos": brace_start, "insert_text": ":"},
                )
            )


def _check_system_typos(line_text: str, line_num: int, diagnostics: list[DiagnosticInfo]) -> None:
    """Check for common crystal system typos."""
    typos = {
        "cubik": "cubic",
        "cubci": "cubic",
        "cubiс": "cubic",  # Cyrillic с
        "hexagnal": "hexagonal",
        "hexagnol": "hexagonal",
        "hexogonal": "hexagonal",
        "tetragnol": "tetragonal",
        "tetragnal": "tetragonal",
        "tetragonl": "tetragonal",
        "trignoal": "trigonal",
        "trignol": "trigonal",
        "trigonl": "trigonal",
        "monoclinc": "monoclinic",
        "monoclinik": "monoclinic",
        "monoclinoc": "monoclinic",
        "orthrhombic": "orthorhombic",
        "orthorhombc": "orthorhombic",
        "orthorhombik": "orthorhombic",
        "orthohombic": "orthorhombic",
        "triclinc": "triclinic",
        "triclinik": "triclinic",
        "triclnic": "triclinic",
    }

    # Look for system at start of CDL (word followed by [)
    match = re.match(r"(\w+)\s*\[", line_text)
    if match:
        system = match.group(1).lower()
        if system in typos:
            suggested = typos[system]
            diagnostics.append(
                DiagnosticInfo(
                    line=line_num,
                    start_char=match.start(1),
                    end_char=match.end(1),
                    message=f"Unknown crystal system '{system}'. Did you mean '{suggested}'?",
                    severity="error",
                    code="typo-system",
                    data={"suggested": suggested, "original": system},
                )
            )


def _check_modification_typos(
    line_text: str, line_num: int, diagnostics: list[DiagnosticInfo]
) -> None:
    """Check for common modification typos."""
    typos = {
        "elognate": "elongate",
        "elongte": "elongate",
        "elogante": "elongate",
        "truncat": "truncate",
        "truncte": "truncate",
        "truincate": "truncate",
        "tapir": "taper",
        "tapper": "taper",
        "tapr": "taper",
        "bevle": "bevel",
        "bevl": "bevel",
        "bevell": "bevel",
        "twinn": "twin",
        "twinned": "twin",
        "twim": "twin",
        "flattn": "flatten",
        "flaten": "flatten",
        "flattten": "flatten",
    }

    # Look for modification keywords (standalone or in + operations)
    for word in re.findall(r"\b([a-z]+)\b", line_text.lower()):
        if word in typos:
            # Find position of this word
            pattern = rf"\b{re.escape(word)}\b"
            for match in re.finditer(pattern, line_text, re.IGNORECASE):
                suggested = typos[word]
                diagnostics.append(
                    DiagnosticInfo(
                        line=line_num,
                        start_char=match.start(),
                        end_char=match.end(),
                        message=f"Unknown modification '{word}'. Did you mean '{suggested}'?",
                        severity="error",
                        code="typo-modification",
                        data={"suggested": suggested, "original": word},
                    )
                )
                break  # Only report first occurrence


def get_diagnostics(text: str) -> list[Any]:
    """
    Get LSP Diagnostic objects for a CDL document.

    Args:
        text: CDL document text

    Returns:
        List of lsprotocol.types.Diagnostic objects
    """
    diagnostic_infos = validate_document(text)
    return [_create_diagnostic(info) for info in diagnostic_infos]
