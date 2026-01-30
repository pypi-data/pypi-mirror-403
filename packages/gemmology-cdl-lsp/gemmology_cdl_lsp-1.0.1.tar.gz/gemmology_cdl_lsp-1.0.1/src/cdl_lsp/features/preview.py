"""
CDL Preview - Generate SVG and 3D previews of CDL crystal descriptions.

This module provides SVG and glTF rendering of CDL code for live preview
in the VS Code extension. 3D preview uses Three.js in a WebView.
"""

import os
import sys
import tempfile
from typing import Any

# Add scripts directory to path for imports
_scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

# Try to import the visualization module
try:
    from crystal_visualization import CDL_AVAILABLE, generate_cdl_svg

    PREVIEW_AVAILABLE = CDL_AVAILABLE
except ImportError:
    PREVIEW_AVAILABLE = False
    generate_cdl_svg = None

# Try to import geometry modules for 3D export
try:
    from crystal_geometry import cdl_to_geometry, geometry_to_gltf
    from crystal_language import parse_cdl

    GLTF_AVAILABLE = True
except ImportError:
    GLTF_AVAILABLE = False
    parse_cdl = None
    cdl_to_geometry = None
    geometry_to_gltf = None

# Try to import presets
try:
    from crystal_presets import CRYSTAL_PRESETS, get_preset

    PRESETS_AVAILABLE = True
except ImportError:
    CRYSTAL_PRESETS = {}
    PRESETS_AVAILABLE = False

    def get_preset(name):
        return None


def _resolve_preset_to_cdl(line: str) -> str | None:
    """
    Check if line is a preset name and return its CDL, otherwise return None.

    Args:
        line: The line to check

    Returns:
        CDL string if line is a preset name, None otherwise
    """
    if not PRESETS_AVAILABLE:
        return None

    line_lower = line.strip().lower()
    if line_lower in CRYSTAL_PRESETS:
        preset = CRYSTAL_PRESETS[line_lower]
        return preset.get("cdl")
    return None


def render_cdl_preview(text: str, width: int = 600, height: int = 500) -> dict[str, Any]:
    """
    Render CDL code as an SVG preview.

    Args:
        text: CDL document text
        width: SVG width in pixels
        height: SVG height in pixels

    Returns:
        Dictionary with SVG content and metadata
    """
    text = text.strip()

    if not text:
        return {
            "success": False,
            "error": "Empty CDL document",
            "svg": _create_error_svg("No CDL code provided", width, height),
        }

    if not PREVIEW_AVAILABLE:
        return {
            "success": False,
            "error": "Preview not available (crystal_visualization module not found)",
            "svg": _create_error_svg("Preview module not available", width, height),
        }

    # Get the first non-comment, non-empty line
    lines = text.split("\n")
    cdl_line = None
    original_line = None
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            original_line = line
            # Check if it's a preset name and resolve to CDL
            resolved = _resolve_preset_to_cdl(line)
            cdl_line = resolved if resolved else line
            break

    if not cdl_line:
        return {
            "success": False,
            "error": "No valid CDL code found",
            "svg": _create_error_svg("No valid CDL code", width, height),
        }

    try:
        # Generate SVG using the visualization module (writes to temp file)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as f:
            temp_path = f.name

        try:
            generate_cdl_svg(
                cdl_line,
                temp_path,
                show_axes=True,
                color_by_form=True,
                show_grid=False,
                info_position="top-right",
                info_style="compact",
            )

            # Read the generated SVG
            with open(temp_path) as f:
                svg_content = f.read()

            return {
                "success": True,
                "svg": svg_content,
                "cdl": cdl_line,
                "preset": original_line if original_line != cdl_line else None,
            }
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except ValueError as e:
        error_msg = str(e)
        return {
            "success": False,
            "error": error_msg,
            "svg": _create_error_svg(f"Parse error: {error_msg}", width, height),
        }
    except Exception as e:
        error_msg = str(e)
        return {
            "success": False,
            "error": error_msg,
            "svg": _create_error_svg(f"Render error: {error_msg}", width, height),
        }


def _create_error_svg(message: str, width: int = 600, height: int = 500) -> str:
    """Create an SVG displaying an error message."""
    # Escape special characters for SVG
    message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Word wrap long messages
    words = message.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 40:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    # Generate text elements
    text_y = height // 2 - (len(lines) * 12)
    text_elements = []
    for i, line in enumerate(lines):
        y = text_y + i * 24
        text_elements.append(
            f'<text x="{width // 2}" y="{y}" '
            f'text-anchor="middle" font-family="sans-serif" font-size="14" fill="#666">'
            f"{line}</text>"
        )

    text_content = "\n    ".join(text_elements)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f5f5f5"/>
  <rect x="20" y="20" width="{width - 40}" height="{height - 40}"
        fill="none" stroke="#ddd" stroke-width="2" stroke-dasharray="10,5" rx="10"/>

  <!-- Error icon -->
  <circle cx="{width // 2}" cy="{height // 2 - 60}" r="25" fill="none" stroke="#e74c3c" stroke-width="3"/>
  <text x="{width // 2}" y="{height // 2 - 52}"
        text-anchor="middle" font-family="sans-serif" font-size="36" font-weight="bold" fill="#e74c3c">!</text>

  <!-- Error message -->
  {text_content}

  <!-- Hint -->
  <text x="{width // 2}" y="{height - 40}"
        text-anchor="middle" font-family="sans-serif" font-size="11" fill="#999">
    Write valid CDL code to see a crystal preview
  </text>
</svg>'''


def render_cdl_preview_3d(text: str) -> dict[str, Any]:
    """
    Render CDL code as a 3D glTF model for Three.js preview.

    Args:
        text: CDL document text

    Returns:
        Dictionary with glTF JSON data and metadata
    """
    text = text.strip()

    if not text:
        return {"success": False, "error": "Empty CDL document", "gltf": None}

    if not GLTF_AVAILABLE:
        return {
            "success": False,
            "error": "3D preview not available (crystal_geometry module not found)",
            "gltf": None,
        }

    # Get the first non-comment, non-empty line
    lines = text.split("\n")
    cdl_line = None
    original_line = None
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            original_line = line
            # Check if it's a preset name and resolve to CDL
            resolved = _resolve_preset_to_cdl(line)
            cdl_line = resolved if resolved else line
            break

    if not cdl_line:
        return {"success": False, "error": "No valid CDL code found", "gltf": None}

    try:
        # Parse and generate geometry
        description = parse_cdl(cdl_line)
        geometry = cdl_to_geometry(cdl_line)

        # Convert to glTF
        gltf_data = geometry_to_gltf(geometry)

        # Create title from CDL (include preset name if applicable)
        forms_str = " + ".join(str(f.miller) for f in description.forms)
        preset_name = original_line if original_line != cdl_line else None
        if preset_name:
            title = (
                f"{preset_name.title()} - {description.system.title()} [{description.point_group}]"
            )
        else:
            title = f"{description.system.title()} [{description.point_group}] : {forms_str}"

        return {
            "success": True,
            "gltf": gltf_data,
            "cdl": cdl_line,
            "preset": preset_name,
            "title": title,
            "system": description.system,
            "point_group": description.point_group,
            "num_forms": len(description.forms),
            "num_vertices": len(geometry.vertices),
            "num_faces": len(geometry.faces),
        }

    except ValueError as e:
        return {"success": False, "error": f"Parse error: {str(e)}", "gltf": None}
    except Exception as e:
        return {"success": False, "error": f"Render error: {str(e)}", "gltf": None}


def get_preview_capabilities() -> dict[str, Any]:
    """Get information about preview capabilities."""
    formats = []
    if PREVIEW_AVAILABLE:
        formats.append("svg")
    if GLTF_AVAILABLE:
        formats.append("gltf")

    return {
        "available": PREVIEW_AVAILABLE or GLTF_AVAILABLE,
        "formats": formats,
        "features": {
            "axes": True,
            "info_panel": True,
            "rotation": GLTF_AVAILABLE,  # 3D rotation available with glTF
            "export": ["svg", "png", "gltf"]
            if GLTF_AVAILABLE
            else (["svg", "png"] if PREVIEW_AVAILABLE else []),
        },
        "preferred": "gltf" if GLTF_AVAILABLE else "svg",
    }
