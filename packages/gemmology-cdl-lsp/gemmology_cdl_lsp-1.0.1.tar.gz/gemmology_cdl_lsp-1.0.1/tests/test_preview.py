"""
Test suite for CDL preview features.

Tests SVG and 3D preview generation.
"""

from cdl_lsp.features.preview import (
    GLTF_AVAILABLE,
    PREVIEW_AVAILABLE,
    _create_error_svg,
    _resolve_preset_to_cdl,
    get_preview_capabilities,
    render_cdl_preview,
    render_cdl_preview_3d,
)


class TestCreateErrorSVG:
    """Test error SVG generation."""

    def test_basic_error_svg(self):
        """Generate basic error SVG."""
        svg = _create_error_svg("Test error message")
        assert "<?xml" in svg
        assert "<svg" in svg
        assert "Test error message" in svg or "Test" in svg

    def test_custom_dimensions(self):
        """Generate error SVG with custom dimensions."""
        svg = _create_error_svg("Error", width=800, height=600)
        assert "800" in svg
        assert "600" in svg

    def test_special_characters_escaped(self):
        """Special characters are escaped."""
        svg = _create_error_svg("Error <test> & more")
        # Characters should be escaped
        assert "<test>" not in svg
        assert "&amp;" in svg or "&lt;" in svg

    def test_long_message_wrapped(self):
        """Long messages are word-wrapped."""
        long_msg = "This is a very long error message that should be wrapped across multiple lines"
        svg = _create_error_svg(long_msg)
        assert "<text" in svg
        # Multiple text elements expected for long messages
        assert svg.count("<text") >= 1


class TestResolvePresetToCDL:
    """Test preset resolution."""

    def test_nonexistent_preset(self):
        """Non-existent preset returns None."""
        result = _resolve_preset_to_cdl("nonexistent_preset_xyz")
        assert result is None

    def test_empty_string(self):
        """Empty string returns None."""
        result = _resolve_preset_to_cdl("")
        assert result is None

    def test_whitespace(self):
        """Whitespace-only returns None."""
        result = _resolve_preset_to_cdl("   ")
        assert result is None


class TestRenderCDLPreview:
    """Test CDL preview rendering."""

    def test_empty_document(self):
        """Empty document returns error."""
        result = render_cdl_preview("")
        assert result["success"] is False
        assert "error" in result
        assert "svg" in result

    def test_whitespace_only(self):
        """Whitespace-only document returns error."""
        result = render_cdl_preview("   ")
        assert result["success"] is False

    def test_comment_only(self):
        """Comment-only document returns error."""
        result = render_cdl_preview("# This is a comment")
        assert result["success"] is False
        assert "No valid CDL code" in result["error"] or "svg" in result

    def test_valid_cdl_without_module(self):
        """Valid CDL without preview module."""
        result = render_cdl_preview("cubic[m3m]:{111}")
        # Without the visualization module, should return error
        if not PREVIEW_AVAILABLE:
            assert result["success"] is False
            assert "not available" in result["error"] or "svg" in result


class TestRenderCDLPreview3D:
    """Test 3D preview rendering."""

    def test_empty_document(self):
        """Empty document returns error."""
        result = render_cdl_preview_3d("")
        assert result["success"] is False
        assert "error" in result

    def test_valid_cdl_without_module(self):
        """Valid CDL without geometry module."""
        result = render_cdl_preview_3d("cubic[m3m]:{111}")
        # Without the geometry module, should return error
        if not GLTF_AVAILABLE:
            assert result["success"] is False
            assert "not available" in result["error"] or result["gltf"] is None


class TestGetPreviewCapabilities:
    """Test preview capabilities query."""

    def test_capabilities_structure(self):
        """Capabilities has correct structure."""
        caps = get_preview_capabilities()
        assert "available" in caps
        assert "formats" in caps
        assert "features" in caps
        assert "preferred" in caps

    def test_formats_list(self):
        """Formats is a list."""
        caps = get_preview_capabilities()
        assert isinstance(caps["formats"], list)

    def test_features_dict(self):
        """Features is a dictionary."""
        caps = get_preview_capabilities()
        assert isinstance(caps["features"], dict)
        assert "axes" in caps["features"]
        assert "info_panel" in caps["features"]
        assert "rotation" in caps["features"]
        assert "export" in caps["features"]

    def test_preferred_format(self):
        """Preferred format is valid."""
        caps = get_preview_capabilities()
        assert caps["preferred"] in ["svg", "gltf"]

    def test_availability_consistency(self):
        """Availability is consistent with formats."""
        caps = get_preview_capabilities()
        if caps["available"]:
            assert len(caps["formats"]) > 0
        else:
            assert len(caps["formats"]) == 0
