"""
CDL Explain - Generate comprehensive explanations of CDL code.

This module provides detailed explanations of CDL (Crystal Description Language)
code, breaking down each component with crystallographic context.
"""

import os
import re
import sys
from typing import Any

# Add scripts directory to path for imports
_scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from ..constants import (
    ALL_POINT_GROUPS,
    CRYSTAL_SYSTEMS,
    FORM_DOCS,
    MODIFICATION_DOCS,
    MODIFICATIONS,
    NAMED_FORMS,
    POINT_GROUP_DOCS,
    POINT_GROUPS,
    SYSTEM_DOCS,
    TWIN_LAW_DOCS,
)

# Try to import presets for explanation
try:
    from crystal_presets import CRYSTAL_PRESETS, get_preset

    PRESETS_AVAILABLE = True
except ImportError:
    CRYSTAL_PRESETS = {}
    PRESETS_AVAILABLE = False

    def get_preset(name):
        return None


def explain_cdl(text: str) -> str:
    """
    Generate a comprehensive explanation of CDL code.

    Args:
        text: CDL document text

    Returns:
        Markdown-formatted explanation
    """
    text = text.strip()
    if not text:
        return "# Empty CDL Document\n\nNo crystal description provided."

    lines = text.split("\n")
    explanations = []

    for line_num, line in enumerate(lines):
        line = line.strip()

        # Skip empty lines and comments
        if not line:
            continue
        if line.startswith("#"):
            explanations.append(f"*Comment:* {line[1:].strip()}\n")
            continue

        # Check if this is a preset name
        if PRESETS_AVAILABLE and line.lower() in CRYSTAL_PRESETS:
            explanation = _explain_preset(line, line_num + 1)
        else:
            # Explain this CDL line
            explanation = _explain_line(line, line_num + 1)
        explanations.append(explanation)

    if not explanations:
        return "# Empty CDL Document\n\nNo valid crystal descriptions found."

    header = "# CDL Explanation\n\n"
    header += "This document describes a crystal morphology using the Crystal Description Language (CDL).\n\n"
    header += "---\n\n"

    return header + "\n---\n\n".join(explanations)


def _explain_preset(preset_name: str, line_num: int) -> str:
    """Explain a preset crystal definition."""
    parts = []
    preset = CRYSTAL_PRESETS.get(preset_name.lower(), {})

    parts.append(f"## Line {line_num}: `{preset_name}` (Preset)\n")

    # Basic info
    name = preset.get("name", preset_name.title())
    parts.append(f"### {name}\n")

    if preset.get("description"):
        parts.append(f"{preset['description']}\n")

    # CDL notation
    cdl = preset.get("cdl", "")
    if cdl:
        parts.append(f"\n**CDL Notation:** `{cdl}`\n")

    # Crystal system and point group
    system = preset.get("system", "Unknown")
    pg = preset.get("point_group", "")
    parts.append(f"\n### Crystal System: **{system.title()}**\n")
    if pg:
        parts.append(f"Point Group: **{pg}**\n")

    # Chemistry
    if preset.get("chemistry"):
        parts.append("\n### Chemistry\n")
        parts.append(f"**Formula:** {preset['chemistry']}\n")

    # Physical properties
    physical_props = []
    if preset.get("hardness"):
        physical_props.append(f"**Hardness:** {preset['hardness']}")
    if preset.get("sg"):
        physical_props.append(f"**Specific Gravity:** {preset['sg']}")
    if preset.get("cleavage"):
        physical_props.append(f"**Cleavage:** {preset['cleavage']}")
    if preset.get("fracture"):
        physical_props.append(f"**Fracture:** {preset['fracture']}")
    if preset.get("lustre"):
        physical_props.append(f"**Lustre:** {preset['lustre']}")

    if physical_props:
        parts.append("\n### Physical Properties\n")
        parts.append("\n".join(physical_props) + "\n")

    # Optical properties
    optical_props = []
    if preset.get("ri"):
        optical_props.append(f"**Refractive Index:** {preset['ri']}")
    if preset.get("birefringence"):
        optical_props.append(f"**Birefringence:** {preset['birefringence']}")
    if preset.get("optical_character"):
        optical_props.append(f"**Optical Character:** {preset['optical_character']}")
    if preset.get("dispersion"):
        optical_props.append(f"**Dispersion:** {preset['dispersion']}")
    if preset.get("pleochroism"):
        optical_props.append(f"**Pleochroism:** {preset['pleochroism']}")

    if optical_props:
        parts.append("\n### Optical Properties\n")
        parts.append("\n".join(optical_props) + "\n")

    # Colors
    if preset.get("colors"):
        parts.append("\n### Colors\n")
        parts.append(", ".join(preset["colors"]) + "\n")

    # Localities
    if preset.get("localities"):
        parts.append("\n### Localities\n")
        parts.append(", ".join(preset["localities"]) + "\n")

    # Crystal forms
    if preset.get("forms"):
        parts.append("\n### Crystal Forms\n")
        parts.append(", ".join(f.title() for f in preset["forms"]) + "\n")

    # Inclusions
    if preset.get("inclusions"):
        parts.append("\n### Common Inclusions\n")
        parts.append(", ".join(preset["inclusions"]) + "\n")

    # Treatments
    if preset.get("treatments"):
        parts.append("\n### Known Treatments\n")
        parts.append(", ".join(preset["treatments"]) + "\n")

    return "".join(parts)


def _explain_line(line: str, line_num: int) -> str:
    """Explain a single CDL line."""
    parts = []
    parts.append(f"## Line {line_num}: `{line}`\n")

    # Parse the components
    system_info = _extract_system(line)
    point_group_info = _extract_point_group(line)
    forms_info = _extract_forms(line)
    modifications_info = _extract_modifications(line)
    twin_info = _extract_twin(line)

    # Crystal System
    if system_info:
        system, system_doc = system_info
        parts.append(f"### Crystal System: **{system.title()}**\n")
        if system_doc:
            parts.append(f"{system_doc}\n")

        # Add valid point groups for this system
        if system in POINT_GROUPS:
            pgs = sorted(POINT_GROUPS[system])
            parts.append(f"\n*Valid point groups for {system}:* {', '.join(pgs)}\n")

    # Point Group
    if point_group_info:
        pg, pg_doc = point_group_info
        parts.append(f"\n### Point Group: **{pg}**\n")
        if pg_doc:
            parts.append(f"{pg_doc}\n")

    # Forms
    if forms_info:
        parts.append(f"\n### Crystal Forms ({len(forms_info)} forms)\n")
        for form in forms_info:
            form_name = form.get("name")
            miller = form.get("miller")
            scale = form.get("scale")
            form_doc = form.get("doc", "")

            if form_name:
                parts.append(f"\n#### {form_name.title()} {miller}\n")
                if form_doc:
                    parts.append(f"{form_doc}\n")
            else:
                parts.append(f"\n#### Miller Index {miller}\n")
                parts.append("Custom form defined by Miller indices.\n")

            if scale and scale != 1.0:
                if scale < 1.0:
                    parts.append(
                        f"\n*Scale:* {scale} — This form is **dominant** (closer to origin, larger faces).\n"
                    )
                else:
                    parts.append(
                        f"\n*Scale:* {scale} — This form is **subordinate** (farther from origin, smaller faces).\n"
                    )

    # Modifications
    if modifications_info:
        parts.append("\n### Modifications\n")
        for mod in modifications_info:
            mod_name = mod.get("name")
            mod_doc = mod.get("doc", "")
            mod_value = mod.get("value")

            parts.append(f"\n#### {mod_name.title()}")
            if mod_value:
                parts.append(f" ({mod_value})")
            parts.append("\n")
            if mod_doc:
                parts.append(f"{mod_doc}\n")

    # Twinning
    if twin_info:
        twin_law = twin_info.get("law")
        twin_doc = twin_info.get("doc", "")
        contact = twin_info.get("contact")

        parts.append(f"\n### Twinning: **{twin_law.title()} Law**\n")
        if twin_doc:
            parts.append(f"{twin_doc}\n")
        if contact:
            parts.append(f"\n*Twin plane/contact:* {contact}\n")

    # Overall description
    parts.append("\n### Summary\n")
    summary = _generate_summary(
        system_info, point_group_info, forms_info, modifications_info, twin_info
    )
    parts.append(summary)

    return "".join(parts)


def _extract_system(line: str) -> tuple | None:
    """Extract crystal system from line."""
    match = re.match(r"(\w+)\s*\[", line)
    if match:
        system = match.group(1).lower()
        if system in CRYSTAL_SYSTEMS:
            doc = SYSTEM_DOCS.get(system, "")
            return (system, doc)
    return None


def _extract_point_group(line: str) -> tuple | None:
    """Extract point group from line."""
    match = re.search(r"\[([^\]]+)\]", line)
    if match:
        pg = match.group(1)
        if pg in ALL_POINT_GROUPS:
            doc = POINT_GROUP_DOCS.get(pg, "")
            return (pg, doc)
    return None


def _extract_forms(line: str) -> list[dict[str, Any]]:
    """Extract crystal forms from line."""
    forms = []

    # Find forms section (after colon, before modifications)
    forms_match = re.search(r":\s*\{(.+?)\}", line)
    if not forms_match:
        # Try without colon for backward compatibility
        forms_match = re.search(r"\]\s*\{(.+?)\}", line)

    if forms_match:
        forms_section = forms_match.group(0)

        # Find all Miller indices or named forms
        # Pattern for Miller index with optional scale: {hkl}@scale or {hkil}@scale
        miller_pattern = r"\{([^}]+)\}(?:@(\d+\.?\d*))?"

        for match in re.finditer(miller_pattern, forms_section):
            miller_str = match.group(1)
            scale_str = match.group(2)

            form_info = {
                "miller": f"{{{miller_str}}}",
                "scale": float(scale_str) if scale_str else 1.0,
            }

            # Check if this is a named form
            for form_name, indices in NAMED_FORMS.items():
                expected = f"{indices[0]}{indices[1]}{indices[2]}"
                if miller_str == expected:
                    form_info["name"] = form_name
                    form_info["doc"] = FORM_DOCS.get(form_name, "")
                    break

            forms.append(form_info)

    # Also check for named forms outside braces (in combined expressions)
    for form_name in NAMED_FORMS.keys():
        # Check if form name appears in the line (not inside braces)
        pattern = rf"\b{re.escape(form_name)}\b(?:@(\d+\.?\d*))?"
        for match in re.finditer(pattern, line, re.IGNORECASE):
            # Skip if this is inside a twin() call
            if "twin(" in line[: match.start()].lower():
                continue

            # Check if already captured
            already_found = any(f.get("name", "").lower() == form_name.lower() for f in forms)
            if not already_found:
                scale_str = match.group(1)
                indices = NAMED_FORMS[form_name]
                forms.append(
                    {
                        "name": form_name,
                        "miller": f"{{{indices[0]}{indices[1]}{indices[2]}}}",
                        "scale": float(scale_str) if scale_str else 1.0,
                        "doc": FORM_DOCS.get(form_name, ""),
                    }
                )

    return forms


def _extract_modifications(line: str) -> list[dict[str, Any]]:
    """Extract modifications from line."""
    modifications = []

    for mod_name in MODIFICATIONS:
        # Check for modification with optional value
        pattern = rf"\b{re.escape(mod_name)}\b(?:\(([^)]+)\))?"
        for match in re.finditer(pattern, line, re.IGNORECASE):
            # Skip if this is part of system name
            if mod_name == line.split("[")[0].strip().lower():
                continue

            mod_info = {
                "name": mod_name,
                "doc": MODIFICATION_DOCS.get(mod_name, ""),
                "value": match.group(1) if match.group(1) else None,
            }
            modifications.append(mod_info)

    return modifications


def _extract_twin(line: str) -> dict[str, Any] | None:
    """Extract twin information from line."""
    # Look for twin(law) or twin(law, contact)
    twin_match = re.search(r"twin\s*\(\s*(\w+)(?:\s*,\s*([^)]+))?\s*\)", line, re.IGNORECASE)
    if twin_match:
        law = twin_match.group(1).lower()
        contact = twin_match.group(2)

        return {
            "law": law,
            "doc": TWIN_LAW_DOCS.get(law, ""),
            "contact": contact.strip() if contact else None,
        }

    return None


def _generate_summary(
    system_info, point_group_info, forms_info, modifications_info, twin_info
) -> str:
    """Generate a human-readable summary."""
    parts = []

    if system_info:
        system, _ = system_info
        parts.append(f"This describes a **{system}** crystal")
    else:
        parts.append("This describes a crystal")

    if point_group_info:
        pg, _ = point_group_info
        parts.append(f" with **{pg}** symmetry")

    if forms_info:
        form_count = len(forms_info)
        named_forms = [f["name"] for f in forms_info if f.get("name")]
        if named_forms:
            parts.append(f", showing {form_count} form(s): {', '.join(named_forms)}")
        else:
            parts.append(f", showing {form_count} crystallographic form(s)")

    if modifications_info:
        mod_names = [m["name"] for m in modifications_info]
        parts.append(f", modified by {', '.join(mod_names)}")

    if twin_info:
        parts.append(f", exhibiting **{twin_info['law']}** twinning")

    parts.append(".")

    return "".join(parts)


def get_explain_result(text: str) -> dict[str, Any]:
    """
    Get explanation result in a structured format.

    Args:
        text: CDL document text

    Returns:
        Dictionary with explanation content
    """
    explanation = explain_cdl(text)
    return {"content": explanation, "kind": "markdown"}
