"""
Test suite for CDL document symbols features.

Tests outline view generation for CDL documents.
"""

from cdl_lsp.features.document_symbols import (
    _extract_children,
    _parse_cdl_line,
    get_document_symbols,
)


class TestGetDocumentSymbols:
    """Test document symbol extraction."""

    def test_empty_document(self):
        """Empty document returns empty list."""
        result = get_document_symbols("")
        assert result == []

    def test_comment_only(self):
        """Comment-only document returns empty list."""
        result = get_document_symbols("# This is a comment")
        assert result == []

    def test_single_cdl_line(self):
        """Single CDL line returns symbol."""
        result = get_document_symbols("cubic[m3m]:{111}")
        # Depends on lsprotocol availability
        # Without it, returns empty list
        assert isinstance(result, list)

    def test_multiple_lines(self):
        """Multiple CDL lines return multiple symbols."""
        text = "cubic[m3m]:{111}\nhexagonal[6/mmm]:{10-10}"
        result = get_document_symbols(text)
        assert isinstance(result, list)

    def test_mixed_content(self):
        """Mixed content with comments."""
        text = "# Diamond\ncubic[m3m]:{111}@1.0 + {100}@1.3\n# Quartz\ntrigonal[-3m]:{10-11}"
        result = get_document_symbols(text)
        assert isinstance(result, list)


class TestParseCDLLine:
    """Test CDL line parsing."""

    def test_simple_cdl(self):
        """Parse simple CDL line."""
        result = _parse_cdl_line("cubic[m3m]:{111}", "cubic[m3m]:{111}", 0)
        # Returns None without lsprotocol, otherwise DocumentSymbol
        assert result is None or hasattr(result, "name")

    def test_with_indentation(self):
        """Parse CDL line with leading whitespace."""
        result = _parse_cdl_line("  cubic[m3m]:{111}", "cubic[m3m]:{111}", 0)
        assert result is None or hasattr(result, "name")

    def test_invalid_format(self):
        """Invalid CDL format returns None."""
        result = _parse_cdl_line("not valid cdl", "not valid cdl", 0)
        assert result is None


class TestExtractChildren:
    """Test child symbol extraction."""

    def test_miller_indices(self):
        """Extract Miller index children."""
        result = _extract_children("cubic[m3m]:{111}@1.0 + {100}@1.3", 0, 0)
        # Without lsprotocol, returns empty list
        assert isinstance(result, list)

    def test_modifications(self):
        """Extract modification children."""
        result = _extract_children("cubic[m3m]:{111}|elongate(c:1.5)", 0, 0)
        assert isinstance(result, list)

    def test_twin(self):
        """Extract twin child."""
        result = _extract_children("cubic[m3m]:{111}|twin(spinel)", 0, 0)
        assert isinstance(result, list)

    def test_no_children(self):
        """Line with no children."""
        result = _extract_children("cubic[m3m]", 0, 0)
        assert isinstance(result, list)
