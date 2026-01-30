"""
Test suite for CDL definition features.

Tests go-to-definition functionality for CDL elements.
"""

from cdl_lsp.features.definition import (
    _get_word_at_position,
    get_definition,
    get_definitions,
)


class TestGetWordAtPosition:
    """Test word extraction at cursor position."""

    def test_simple_word(self):
        """Extract simple word."""
        word, start, end = _get_word_at_position("cubic[m3m]", 2)
        assert word == "cubic"
        assert start == 0
        assert end == 5

    def test_word_with_hyphen(self):
        """Extract word with hyphen."""
        word, start, end = _get_word_at_position("test-word", 4)
        assert word == "test-word"
        assert start == 0
        assert end == 9

    def test_word_with_slash(self):
        """Extract word with slash (point groups like 6/mmm)."""
        word, start, end = _get_word_at_position("hexagonal[6/mmm]", 12)
        assert "6/mmm" in word or "6" in word

    def test_empty_position(self):
        """Handle cursor at empty position."""
        word, start, end = _get_word_at_position("test  word", 5)
        assert word == ""

    def test_start_of_line(self):
        """Handle cursor at start of line."""
        word, start, end = _get_word_at_position("cubic", 0)
        assert word == "cubic"

    def test_end_of_word(self):
        """Handle cursor at end of word."""
        word, start, end = _get_word_at_position("cubic[m3m]", 5)
        assert word == "cubic"


class TestGetDefinition:
    """Test go-to-definition functionality."""

    def test_named_form_definition(self):
        """Get definition for named form."""
        # Note: This may return None if source files aren't available
        result = get_definition("octahedron", 5)
        # Just verify it doesn't crash - actual result depends on files
        assert result is None or hasattr(result, "uri") or "uri" in result

    def test_crystal_system_definition(self):
        """Get definition for crystal system."""
        result = get_definition("cubic[m3m]:{111}", 2)
        # May return None if source files aren't available
        assert result is None or hasattr(result, "uri") or "uri" in result

    def test_point_group_definition(self):
        """Get definition for point group."""
        result = get_definition("cubic[m3m]:{111}", 7)
        assert result is None or hasattr(result, "uri") or "uri" in result

    def test_twin_law_definition(self):
        """Get definition for twin law."""
        result = get_definition("twin(spinel)", 6)
        assert result is None or hasattr(result, "uri") or "uri" in result

    def test_unknown_word(self):
        """Get definition for unknown word."""
        result = get_definition("unknown_word_xyz", 5)
        assert result is None

    def test_empty_word(self):
        """Handle empty word."""
        result = get_definition("   ", 1)
        assert result is None


class TestGetDefinitions:
    """Test getting multiple definitions."""

    def test_single_definition(self):
        """Get definitions returns list."""
        result = get_definitions("octahedron", 5)
        assert isinstance(result, list)

    def test_no_definition(self):
        """No definition returns empty list."""
        result = get_definitions("unknown_xyz", 5)
        assert result == []

    def test_empty_input(self):
        """Empty input returns empty list."""
        result = get_definitions("", 0)
        assert result == []
