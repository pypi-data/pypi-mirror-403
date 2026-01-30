"""
CDL Constants for LSP features.

Provides comprehensive constant definitions, documentation, and metadata
for CDL language elements used by the LSP server.
"""

from pathlib import Path

# =============================================================================
# Crystal Systems
# =============================================================================

# Import from cdl-parser where possible
try:
    from cdl_parser import (
        CRYSTAL_SYSTEMS as _SYSTEMS,
    )
    from cdl_parser import (
        NAMED_FORMS as _FORMS,
    )
    from cdl_parser import (
        POINT_GROUPS as _GROUPS,
    )
    from cdl_parser import (
        TWIN_LAWS as _TWINS,
    )

    CRYSTAL_SYSTEMS: set[str] = set(_SYSTEMS)
    NAMED_FORMS: dict[str, tuple[int, int, int]] = dict(_FORMS)
    TWIN_LAWS: set[str] = set(_TWINS)
    # Flatten all point groups from all systems
    ALL_POINT_GROUPS: set[str] = set()
    for _pgs in _GROUPS.values():
        ALL_POINT_GROUPS.update(_pgs)
    # Point groups by system
    POINT_GROUPS: dict[str, set[str]] = {k: set(v) for k, v in _GROUPS.items()}
except ImportError:
    # Fallback definitions
    CRYSTAL_SYSTEMS: set[str] = {
        "cubic",
        "tetragonal",
        "orthorhombic",
        "hexagonal",
        "trigonal",
        "monoclinic",
        "triclinic",
    }

    # All 32 crystallographic point groups by system
    POINT_GROUPS: dict[str, set[str]] = {
        "cubic": {"m3m", "432", "-43m", "m-3", "23"},
        "hexagonal": {"6/mmm", "622", "6mm", "-6m2", "6/m", "-6", "6"},
        "trigonal": {"-3m", "32", "3m", "-3", "3"},
        "tetragonal": {"4/mmm", "422", "4mm", "-42m", "4/m", "-4", "4"},
        "orthorhombic": {"mmm", "222", "mm2"},
        "monoclinic": {"2/m", "m", "2"},
        "triclinic": {"-1", "1"},
    }

    # All point groups flattened
    ALL_POINT_GROUPS: set[str] = set().union(*POINT_GROUPS.values())

    NAMED_FORMS: dict[str, tuple[int, int, int]] = {
        # Cubic
        "cube": (1, 0, 0),
        "octahedron": (1, 1, 1),
        "dodecahedron": (1, 1, 0),
        "trapezohedron": (2, 1, 1),
        "tetrahexahedron": (2, 1, 0),
        "trisoctahedron": (2, 2, 1),
        "hexoctahedron": (3, 2, 1),
        # Hexagonal/Trigonal
        "prism": (1, 0, 0),
        "prism_1": (1, 0, 0),
        "prism_2": (1, 1, 0),
        "pinacoid": (0, 0, 1),
        "basal": (0, 0, 1),
        "rhombohedron": (1, 0, 1),
        "rhomb_pos": (1, 0, 1),
        "rhomb_neg": (0, 1, 1),
        "dipyramid": (1, 0, 1),
        "dipyramid_1": (1, 0, 1),
        "dipyramid_2": (1, 1, 2),
        "scalenohedron": (2, 1, 1),
        # Tetragonal
        "tetragonal_prism": (1, 0, 0),
        "tetragonal_dipyramid": (1, 0, 1),
        # Orthorhombic
        "pinacoid_a": (1, 0, 0),
        "pinacoid_b": (0, 1, 0),
        "pinacoid_c": (0, 0, 1),
        "prism_ab": (1, 1, 0),
        "prism_ac": (1, 0, 1),
        "prism_bc": (0, 1, 1),
    }

    TWIN_LAWS: set[str] = {
        "spinel",
        "spinel_law",
        "iron_cross",
        "brazil",
        "dauphine",
        "japan",
        "carlsbad",
        "baveno",
        "manebach",
        "albite",
        "pericline",
        "trilling",
        "fluorite",
        "staurolite_60",
        "staurolite_90",
        "gypsum_swallow",
    }

# Default point group for each system
DEFAULT_POINT_GROUPS: dict[str, str] = {
    "cubic": "m3m",
    "tetragonal": "4/mmm",
    "orthorhombic": "mmm",
    "hexagonal": "6/mmm",
    "trigonal": "-3m",
    "monoclinic": "2/m",
    "triclinic": "-1",
}

# =============================================================================
# Modifications
# =============================================================================

MODIFICATIONS: set[str] = {"elongate", "truncate", "taper", "bevel", "twin"}

# =============================================================================
# Common Miller indices by system
# =============================================================================

COMMON_MILLER_INDICES: dict[str, list[str]] = {
    "cubic": ["{111}", "{100}", "{110}", "{211}", "{210}", "{221}", "{321}"],
    "tetragonal": ["{100}", "{001}", "{101}", "{110}", "{111}", "{011}"],
    "orthorhombic": ["{100}", "{010}", "{001}", "{110}", "{101}", "{011}", "{111}"],
    "hexagonal": ["{10-10}", "{0001}", "{10-11}", "{11-20}", "{11-22}"],
    "trigonal": ["{10-10}", "{0001}", "{10-11}", "{01-11}", "{11-20}", "{21-31}"],
    "monoclinic": ["{100}", "{010}", "{001}", "{110}", "{011}", "{-101}"],
    "triclinic": ["{100}", "{010}", "{001}", "{110}", "{011}", "{101}", "{-111}"],
}

# Common scale values
COMMON_SCALES: list[str] = ["0.3", "0.5", "0.8", "1.0", "1.2", "1.5", "2.0"]

# =============================================================================
# Documentation for hover
# =============================================================================

SYSTEM_DOCS: dict[str, str] = {
    "cubic": """**Cubic (Isometric) System**

Default point group: m3m
Lattice parameters: a = b = c, α = β = γ = 90°

Highest symmetry system with three mutually perpendicular 4-fold axes.
Examples: diamond, garnet, fluorite, pyrite, spinel""",
    "tetragonal": """**Tetragonal System**

Default point group: 4/mmm
Lattice parameters: a = b ≠ c, α = β = γ = 90°

One 4-fold axis of symmetry along c-axis.
Examples: zircon, rutile, vesuvianite, scapolite""",
    "orthorhombic": """**Orthorhombic System**

Default point group: mmm
Lattice parameters: a ≠ b ≠ c, α = β = γ = 90°

Three mutually perpendicular 2-fold axes.
Examples: topaz, peridot, tanzanite, chrysoberyl""",
    "hexagonal": """**Hexagonal System**

Default point group: 6/mmm
Lattice parameters: a = b ≠ c, α = β = 90°, γ = 120°

One 6-fold axis of symmetry along c-axis.
Examples: beryl (emerald, aquamarine), apatite""",
    "trigonal": """**Trigonal (Rhombohedral) System**

Default point group: -3m
Lattice parameters: a = b ≠ c, α = β = 90°, γ = 120°

One 3-fold axis of symmetry along c-axis.
Examples: quartz, corundum (ruby, sapphire), tourmaline, calcite""",
    "monoclinic": """**Monoclinic System**

Default point group: 2/m
Lattice parameters: a ≠ b ≠ c, α = γ = 90°, β ≠ 90°

One 2-fold axis of symmetry.
Examples: orthoclase, gypsum, jadeite, spodumene""",
    "triclinic": """**Triclinic System**

Default point group: -1
Lattice parameters: a ≠ b ≠ c, α ≠ β ≠ γ ≠ 90°

Lowest symmetry system - no rotation axes, only inversion center.
Examples: plagioclase, amazonite, rhodonite, turquoise""",
}

POINT_GROUP_DOCS: dict[str, str] = {
    # Cubic
    "m3m": "**m3m** (Hermann-Mauguin) - Full cubic symmetry (Oh). 48 operations. Examples: diamond, garnet, fluorite",
    "432": "**432** - Cubic rotations only (O). 24 operations. Chiral (no mirror planes). Examples: sal-ammoniac",
    "-43m": "**-43m** - Tetrahedral symmetry (Td). 24 operations. Examples: sphalerite, tetrahedrite",
    "m-3": "**m-3** (Th). 24 operations. Examples: pyrite",
    "23": "**23** - Tetrahedral rotations (T). 12 operations. Chiral. Examples: ullmannite",
    # Hexagonal
    "6/mmm": "**6/mmm** - Full hexagonal symmetry (D6h). 24 operations. Examples: beryl",
    "622": "**622** - Hexagonal rotations (D6). 12 operations. Chiral. Examples: high quartz",
    "6mm": "**6mm** - Hexagonal polar (C6v). 12 operations. Examples: wurtzite",
    "-6m2": "**-6m2** (D3h). 12 operations. Examples: benitoite",
    "6/m": "**6/m** (C6h). 12 operations. Examples: apatite",
    "-6": "**-6** (C3h). 6 operations.",
    "6": "**6** (C6). 6 operations. Chiral.",
    # Trigonal
    "-3m": "**-3m** - Full trigonal symmetry (D3d). 12 operations. Examples: calcite, corundum",
    "32": "**32** - Trigonal rotations (D3). 6 operations. Chiral. Examples: quartz (low)",
    "3m": "**3m** - Trigonal polar (C3v). 6 operations. Examples: tourmaline",
    "-3": "**-3** (S6/C3i). 6 operations. Examples: dolomite",
    "3": "**3** (C3). 3 operations. Chiral.",
    # Tetragonal
    "4/mmm": "**4/mmm** - Full tetragonal symmetry (D4h). 16 operations. Examples: zircon, rutile",
    "422": "**422** - Tetragonal rotations (D4). 8 operations. Chiral.",
    "4mm": "**4mm** - Tetragonal polar (C4v). 8 operations.",
    "-42m": "**-42m** (D2d). 8 operations. Examples: urea",
    "4/m": "**4/m** (C4h). 8 operations. Examples: scheelite",
    "-4": "**-4** (S4). 4 operations.",
    "4": "**4** (C4). 4 operations. Chiral.",
    # Orthorhombic
    "mmm": "**mmm** - Full orthorhombic symmetry (D2h). 8 operations. Examples: topaz, olivine",
    "222": "**222** - Orthorhombic rotations (D2). 4 operations. Chiral. Examples: epsomite",
    "mm2": "**mm2** - Orthorhombic polar (C2v). 4 operations. Examples: hemimorphite",
    # Monoclinic
    "2/m": "**2/m** - Full monoclinic symmetry (C2h). 4 operations. Examples: orthoclase, gypsum",
    "m": "**m** - Mirror only (Cs). 2 operations. Examples: clinohedrite",
    "2": "**2** - 2-fold rotation only (C2). 2 operations. Chiral. Examples: sucrose",
    # Triclinic
    "-1": "**-1** - Inversion center only (Ci). 2 operations. Examples: plagioclase, rhodonite",
    "1": "**1** - Identity only (C1). 1 operation. Chiral. No symmetry.",
}

FORM_DOCS: dict[str, str] = {
    "cube": "**Cube** {100} - 6 faces. Cardinal form of the cubic system.",
    "octahedron": "**Octahedron** {111} - 8 faces. Dual of the cube.",
    "dodecahedron": "**Rhombic Dodecahedron** {110} - 12 faces. Common in garnet.",
    "trapezohedron": "**Trapezohedron** {211} - 24 faces. Common in garnet, leucite.",
    "tetrahexahedron": "**Tetrahexahedron** {210} - 24 faces.",
    "trisoctahedron": "**Trisoctahedron** {221} - 24 faces.",
    "hexoctahedron": "**Hexoctahedron** {321} - 48 faces. General form of m3m.",
    "prism": "**Hexagonal Prism** {10-10} - 6 faces. First-order prism.",
    "prism_1": "**First-order Prism** {10-10} - 6 faces.",
    "prism_2": "**Second-order Prism** {11-20} - 6 faces.",
    "pinacoid": "**Pinacoid (Basal)** {0001} - 2 faces. Perpendicular to c-axis.",
    "basal": "**Basal Pinacoid** {0001} - 2 faces. Perpendicular to c-axis.",
    "rhombohedron": "**Rhombohedron** {10-11} - 6 faces. Common in calcite, quartz.",
    "rhomb_pos": "**Positive Rhombohedron** {10-11} - 6 faces.",
    "rhomb_neg": "**Negative Rhombohedron** {01-11} - 6 faces.",
    "dipyramid": "**Dipyramid** {10-11} - 12 faces.",
    "dipyramid_1": "**First-order Dipyramid** {10-11} - 12 faces.",
    "dipyramid_2": "**Second-order Dipyramid** {11-22} - 12 faces.",
    "scalenohedron": "**Scalenohedron** {21-31} - 12 faces. Characteristic of calcite.",
    "tetragonal_prism": "**Tetragonal Prism** {100} - 4 faces.",
    "tetragonal_dipyramid": "**Tetragonal Dipyramid** {101} - 8 faces.",
    "pinacoid_a": "**Pinacoid a** {100} - 2 faces. Perpendicular to a-axis.",
    "pinacoid_b": "**Pinacoid b** {010} - 2 faces. Perpendicular to b-axis.",
    "pinacoid_c": "**Pinacoid c** {001} - 2 faces. Perpendicular to c-axis.",
    "prism_ab": "**Prism ab** {110} - 4 faces.",
    "prism_ac": "**Prism ac** {101} - 4 faces.",
    "prism_bc": "**Prism bc** {011} - 4 faces.",
}

TWIN_LAW_DOCS: dict[str, str] = {
    "spinel": "**Spinel Law (Macle)** - 180° rotation about [111]. Contact twin forming triangular plates. Examples: spinel, diamond, magnetite.",
    "spinel_law": "**Spinel Law (Macle)** - 180° rotation about [111]. Contact twin forming triangular plates. Examples: spinel, diamond, magnetite.",
    "iron_cross": "**Iron Cross Twin** - 90° rotation about [001]. Penetration twin characteristic of pyrite.",
    "brazil": "**Brazil Twin** - 180° rotation about [110]. Optical/penetration twin creating opposite handedness regions. Examples: quartz.",
    "dauphine": "**Dauphine Twin** - 180° rotation about [001]. Internal/electrical twin. No visible external morphology change. Examples: quartz.",
    "japan": "**Japan Twin** - Contact twin at 84°33'30\" angle. Twin plane {11-22}. Characteristic V-shape. Examples: quartz.",
    "carlsbad": "**Carlsbad Twin** - 180° rotation about [001]. Penetration twin. Examples: orthoclase, feldspar.",
    "baveno": "**Baveno Twin** - 180° rotation about [021]. Contact twin. Examples: orthoclase, feldspar.",
    "manebach": "**Manebach Twin** - 180° rotation about [001] with (001) composition plane. Contact twin. Examples: orthoclase, feldspar.",
    "albite": "**Albite Twin** - 180° rotation about normal to (010). Polysynthetic (lamellar) twinning. Examples: plagioclase, albite.",
    "pericline": "**Pericline Twin** - Twin axis in (010) plane. Examples: albite.",
    "trilling": "**Trilling (Cyclic Twin)** - Three crystals rotated 120° about c-axis. Examples: chrysoberyl, aragonite.",
    "fluorite": "**Fluorite Penetration Twin** - Two cubes interpenetrating along [111]. Creates octahedral outline.",
    "staurolite_60": "**Staurolite 60° Twin** - 60° cross-shaped penetration twin forming X pattern.",
    "staurolite_90": "**Staurolite 90° Twin** - 90° cross-shaped penetration twin forming + pattern.",
    "gypsum_swallow": "**Gypsum Swallow-Tail Twin** - Contact twin forming characteristic swallow-tail shape.",
}

MODIFICATION_DOCS: dict[str, str] = {
    "elongate": """**elongate(axis:ratio)**

Stretches the crystal along the specified axis.

Parameters:
- axis: a, b, or c
- ratio: scaling factor (> 1 elongates, < 1 shortens)

Example: `elongate(c:1.5)` - elongate 50% along c-axis""",
    "truncate": """**truncate(form:depth)**

Truncates the crystal by the specified form.

Parameters:
- form: Named form or Miller index
- depth: truncation depth (0-1)

Example: `truncate({100}:0.3)` - truncate by cube faces at 30%""",
    "taper": """**taper(direction:factor)**

Tapers the crystal in the specified direction.

Parameters:
- direction: direction to taper (e.g., +c, -c)
- factor: taper factor

Example: `taper(+c:0.5)` - taper toward +c by 50%""",
    "bevel": """**bevel(edges:width)**

Bevels the specified edges.

Parameters:
- edges: edge set to bevel
- width: bevel width

Example: `bevel(all:0.1)` - bevel all edges with width 0.1""",
    "twin": """**twin(law) or twin(law,count)**

Creates a twinned crystal using the specified twin law.

Parameters:
- law: Named twin law (spinel, brazil, japan, etc.)
- count: Number of individuals for cyclic twins (optional)

Examples:
- `twin(spinel)` - Spinel law macle
- `twin(japan)` - Japan V-twin
- `twin(trilling,3)` - Three-part cyclic twin""",
}

# =============================================================================
# Dynamic definition source resolution
# =============================================================================


def get_definition_source(category: str) -> Path | None:
    """
    Locate definition source file dynamically via package introspection.

    Args:
        category: One of 'forms', 'point_groups', 'twin_laws', 'systems'

    Returns:
        Path to the source file containing the definition, or None
    """
    try:
        # Try cdl_parser first (the canonical source)
        import cdl_parser

        parser_constants = Path(cdl_parser.__file__).parent / "constants.py"
        if parser_constants.exists():
            return parser_constants
    except ImportError:
        pass

    # Fallback to local constants
    return Path(__file__)


# Definition search patterns for each category
DEFINITION_PATTERNS: dict[str, str] = {
    "forms": "NAMED_FORMS",
    "twin_laws": "TWIN_LAWS",
    "point_groups": "POINT_GROUPS",
    "systems": "CRYSTAL_SYSTEMS",
}

# =============================================================================
# Utility functions
# =============================================================================


def get_system_for_point_group(pg: str) -> str | None:
    """Get the crystal system for a given point group."""
    for system, groups in POINT_GROUPS.items():
        if pg in groups:
            return system
    return None


def validate_point_group_for_system(system: str, pg: str) -> bool:
    """Check if a point group is valid for a given system."""
    if system not in POINT_GROUPS:
        return False
    return pg in POINT_GROUPS[system]


def get_form_miller_indices(form_name: str) -> tuple[int, int, int] | None:
    """Get Miller indices for a named form."""
    return NAMED_FORMS.get(form_name.lower())


def is_valid_system(name: str) -> bool:
    """Check if a name is a valid crystal system."""
    return name.lower() in CRYSTAL_SYSTEMS


def is_valid_point_group(name: str) -> bool:
    """Check if a name is a valid point group."""
    return name in ALL_POINT_GROUPS


def is_valid_form_name(name: str) -> bool:
    """Check if a name is a valid named form."""
    return name.lower() in NAMED_FORMS


def is_valid_twin_law(name: str) -> bool:
    """Check if a name is a valid twin law."""
    return name.lower() in TWIN_LAWS


def is_valid_modification(name: str) -> bool:
    """Check if a name is a valid modification type."""
    return name.lower() in MODIFICATIONS
