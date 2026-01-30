"""
Test suite for cdl-lsp.

Tests LSP features including diagnostics, completion, hover, and formatting.
"""

import pytest

from cdl_lsp.constants import (
    ALL_POINT_GROUPS,
    CRYSTAL_SYSTEMS,
    MODIFICATIONS,
    NAMED_FORMS,
    POINT_GROUP_DOCS,
    POINT_GROUPS,
    SYSTEM_DOCS,
    TWIN_LAWS,
)

# =============================================================================
# Constants Tests
# =============================================================================


class TestConstants:
    """Test CDL constants."""

    def test_crystal_systems(self):
        """Test crystal systems are defined."""
        assert len(CRYSTAL_SYSTEMS) == 7
        assert "cubic" in CRYSTAL_SYSTEMS
        assert "hexagonal" in CRYSTAL_SYSTEMS
        assert "trigonal" in CRYSTAL_SYSTEMS

    def test_point_groups(self):
        """Test point groups are defined for each system."""
        assert len(POINT_GROUPS) == 7
        for system in CRYSTAL_SYSTEMS:
            assert system in POINT_GROUPS
            assert len(POINT_GROUPS[system]) > 0

    def test_all_point_groups(self):
        """Test all point groups set."""
        assert "m3m" in ALL_POINT_GROUPS
        assert "6/mmm" in ALL_POINT_GROUPS
        assert "-3m" in ALL_POINT_GROUPS
        assert len(ALL_POINT_GROUPS) == 32

    def test_named_forms(self):
        """Test named forms are defined."""
        assert "cube" in NAMED_FORMS
        assert "octahedron" in NAMED_FORMS
        assert NAMED_FORMS["cube"] == (1, 0, 0)
        assert NAMED_FORMS["octahedron"] == (1, 1, 1)

    def test_twin_laws(self):
        """Test twin laws are defined."""
        assert "spinel" in TWIN_LAWS
        assert "japan" in TWIN_LAWS
        assert "brazil" in TWIN_LAWS

    def test_modifications(self):
        """Test modifications are defined."""
        assert "elongate" in MODIFICATIONS
        assert "truncate" in MODIFICATIONS
        assert "twin" in MODIFICATIONS

    def test_system_docs(self):
        """Test system documentation exists."""
        for system in CRYSTAL_SYSTEMS:
            assert system in SYSTEM_DOCS
            assert len(SYSTEM_DOCS[system]) > 0

    def test_point_group_docs(self):
        """Test point group documentation exists."""
        for pg in ["m3m", "6/mmm", "-3m", "4/mmm", "mmm", "2/m", "-1"]:
            assert pg in POINT_GROUP_DOCS


# =============================================================================
# Feature Import Tests
# =============================================================================


class TestFeatureImports:
    """Test that all feature modules can be imported."""

    def test_import_diagnostics(self):
        """Test diagnostics module import."""
        from cdl_lsp.features import get_diagnostics

        assert callable(get_diagnostics)

    def test_import_completion(self):
        """Test completion module import."""
        from cdl_lsp.features import get_completions

        assert callable(get_completions)

    def test_import_hover(self):
        """Test hover module import."""
        from cdl_lsp.features import get_hover_info

        assert callable(get_hover_info)

    def test_import_definition(self):
        """Test definition module import."""
        from cdl_lsp.features import get_definition

        assert callable(get_definition)

    def test_import_formatting(self):
        """Test formatting module import."""
        from cdl_lsp.features import format_cdl

        assert callable(format_cdl)

    def test_import_snippets(self):
        """Test snippets module import."""
        from cdl_lsp.features import get_preset_snippets, list_preset_names

        assert callable(get_preset_snippets)
        assert callable(list_preset_names)

    def test_import_code_actions(self):
        """Test code actions module import."""
        from cdl_lsp.features import get_code_actions

        assert callable(get_code_actions)

    def test_import_signature_help(self):
        """Test signature help module import."""
        from cdl_lsp.features import get_signature_help

        assert callable(get_signature_help)

    def test_import_document_symbols(self):
        """Test document symbols module import."""
        from cdl_lsp.features import get_document_symbols

        assert callable(get_document_symbols)


# =============================================================================
# Diagnostics Tests
# =============================================================================


class TestDiagnostics:
    """Test diagnostics feature."""

    def test_valid_cdl_no_errors(self):
        """Test valid CDL produces no errors."""
        from cdl_lsp.features import get_diagnostics

        # Valid CDL
        diagnostics = get_diagnostics("cubic[m3m]:{111}")
        errors = [d for d in diagnostics if d.severity == 1]  # Error severity
        assert len(errors) == 0

    def test_invalid_system_error(self):
        """Test invalid system produces error."""
        from cdl_lsp.features import get_diagnostics

        diagnostics = get_diagnostics("invalid[m3m]:{111}")
        assert len(diagnostics) > 0

    def test_invalid_point_group_error(self):
        """Test invalid point group produces error."""
        from cdl_lsp.features import get_diagnostics

        diagnostics = get_diagnostics("cubic[xyz]:{111}")
        assert len(diagnostics) > 0


# =============================================================================
# Completion Tests
# =============================================================================


class TestCompletion:
    """Test completion feature."""

    def test_system_completion(self):
        """Test system name completion."""
        from cdl_lsp.features import get_completions

        # At start of line, should suggest systems
        completions = get_completions("", 0, 0)
        labels = [c.label for c in completions]
        assert "cubic" in labels
        assert "hexagonal" in labels


# =============================================================================
# Formatting Tests
# =============================================================================


class TestFormatting:
    """Test formatting feature."""

    def test_format_basic(self):
        """Test basic CDL formatting."""
        from cdl_lsp.features import format_cdl

        # Should normalize spacing - returns list of TextEdit objects
        result = format_cdl("cubic[m3m]:{111}@1.0+{100}@1.3")
        assert result is not None  # Ensure a result is returned
        assert isinstance(result, list)  # Result should be a list of TextEdits
        assert len(result) > 0  # Should have at least one edit
        # Check that the formatted text contains proper spacing
        formatted_text = result[0].new_text
        assert " + " in formatted_text  # Forms should be separated by ' + '


# =============================================================================
# Server Tests
# =============================================================================


class TestServer:
    """Test server creation."""

    def test_create_server(self):
        """Test server can be created."""
        try:
            from cdl_lsp import create_server

            server = create_server()
            assert server is not None
        except ImportError:
            pytest.skip("pygls not installed")

    def test_server_name(self):
        """Test server name constant."""
        from cdl_lsp import SERVER_NAME, SERVER_VERSION

        assert SERVER_NAME == "cdl-language-server"
        assert SERVER_VERSION == "1.0.0"
