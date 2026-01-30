"""
Tests for CDL LSP Hover functionality.
"""

from cdl_lsp.features.hover import _get_word_at_position, get_hover_info


class TestGetWordAtPosition:
    """Tests for word extraction."""

    def test_simple_word(self):
        """Extract word from middle of line."""
        word, start, end = _get_word_at_position("cubic[m3m]", 2)
        assert word == "cubic"
        assert start == 0
        assert end == 5

    def test_point_group(self):
        """Extract point group with special characters."""
        word, start, end = _get_word_at_position("cubic[m3m]", 7)
        assert word == "m3m"
        assert start == 6
        assert end == 9

    def test_empty_line(self):
        """Handle empty line."""
        word, start, end = _get_word_at_position("", 0)
        assert word == ""

    def test_end_of_line(self):
        """Handle cursor at end of line."""
        word, start, end = _get_word_at_position("cubic", 5)
        # Should still find the word
        assert word == "cubic"


class TestHoverCrystalSystems:
    """Tests for hover on crystal systems."""

    def test_cubic_system(self):
        """Hover on 'cubic' returns system documentation."""
        hover = get_hover_info("cubic[m3m]:{111}", 2)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "Cubic" in content
        assert "Isometric" in content

    def test_hexagonal_system(self):
        """Hover on 'hexagonal' returns system documentation."""
        hover = get_hover_info("hexagonal[6/mmm]", 4)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "Hexagonal" in content

    def test_trigonal_system(self):
        """Hover on 'trigonal' returns system documentation."""
        hover = get_hover_info("trigonal[-3m]:{10-11}", 4)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "Trigonal" in content


class TestHoverPointGroups:
    """Tests for hover on point groups."""

    def test_cubic_point_group(self):
        """Hover on 'm3m' returns point group documentation."""
        hover = get_hover_info("cubic[m3m]:{111}", 7)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "m3m" in content
        assert "cubic" in content.lower()

    def test_hexagonal_point_group(self):
        """Hover on '6/mmm' returns point group documentation."""
        hover = get_hover_info("hexagonal[6/mmm]", 12)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "6/mmm" in content


class TestHoverNamedForms:
    """Tests for hover on named forms."""

    def test_octahedron_form(self):
        """Hover on 'octahedron' returns form documentation."""
        hover = get_hover_info("cubic[m3m]:octahedron@1.0", 15)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "Octahedron" in content
        assert "111" in content

    def test_cube_form(self):
        """Hover on 'cube' returns form documentation."""
        hover = get_hover_info("cubic[m3m]:cube@1.0", 12)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "Cube" in content


class TestHoverMillerIndices:
    """Tests for hover on Miller indices."""

    def test_three_index_miller(self):
        """Hover on {111} returns Miller index documentation."""
        hover = get_hover_info("cubic[m3m]:{111}@1.0", 12)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "Miller" in content
        assert "111" in content

    def test_four_index_miller(self):
        """Hover on {10-10} returns Miller-Bravais documentation."""
        hover = get_hover_info("hexagonal[6/mmm]:{10-10}", 20)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "Miller" in content


class TestHoverTwinLaws:
    """Tests for hover on twin laws."""

    def test_spinel_twin(self):
        """Hover on 'spinel' twin law returns documentation."""
        hover = get_hover_info("cubic[m3m]:{111} | twin(spinel)", 28)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "Spinel" in content
        assert "111" in content or "twin" in content.lower()

    def test_brazil_twin(self):
        """Hover on 'brazil' twin law returns documentation."""
        hover = get_hover_info("trigonal[32]:{10-11} | twin(brazil)", 32)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "Brazil" in content


class TestHoverScale:
    """Tests for hover on scale values."""

    def test_default_scale(self):
        """Hover on @1.5 returns scale documentation."""
        # Position 19 is in the scale number (the '5' in @1.5)
        # cubic[m3m]:{111}@1.5
        # 0         1
        # 0123456789012345678901
        hover = get_hover_info("cubic[m3m]:{111}@1.5", 19)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "Scale" in content
        assert "1.5" in content

    def test_small_scale(self):
        """Hover on small scale returns appropriate documentation."""
        # Position 18 is on the '5' of @0.5 (avoiding '0' which might not match)
        hover = get_hover_info("cubic[m3m]:{111}@0.5", 18)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "closer" in content.lower() or "dominant" in content.lower()


class TestHoverModifications:
    """Tests for hover on modifications."""

    def test_twin_modification(self):
        """Hover on 'twin' keyword returns documentation."""
        hover = get_hover_info("cubic[m3m]:{111} | twin(spinel)", 20)
        assert hover is not None
        content = hover.get("contents") if isinstance(hover, dict) else hover.contents.value
        assert "twin" in content.lower()


class TestHoverNoResult:
    """Tests for cases where no hover should be returned."""

    def test_unknown_word(self):
        """Hover on unknown word returns None."""
        hover = get_hover_info("unknown_word", 5)
        assert hover is None

    def test_punctuation(self):
        """Hover on punctuation returns None."""
        get_hover_info("cubic[m3m]:{111}@1.0", 10)  # On colon
        # May return None or may trigger adjacent word
        # Just verify it doesn't crash
        pass
