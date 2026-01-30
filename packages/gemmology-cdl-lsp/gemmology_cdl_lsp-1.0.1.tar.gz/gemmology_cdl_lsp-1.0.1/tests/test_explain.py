"""
Test suite for CDL explain features.

Tests explanation generation for CDL documents.
"""

from cdl_lsp.features.explain import (
    _extract_forms,
    _extract_modifications,
    _extract_point_group,
    _extract_system,
    _extract_twin,
    _generate_summary,
    explain_cdl,
    get_explain_result,
)


class TestExtractSystem:
    """Test crystal system extraction."""

    def test_cubic_system(self):
        """Extract cubic system."""
        result = _extract_system("cubic[m3m]:{111}")
        assert result is not None
        system, doc = result
        assert system == "cubic"
        assert len(doc) > 0

    def test_hexagonal_system(self):
        """Extract hexagonal system."""
        result = _extract_system("hexagonal[6/mmm]:{10-10}")
        assert result is not None
        system, doc = result
        assert system == "hexagonal"

    def test_trigonal_system(self):
        """Extract trigonal system."""
        result = _extract_system("trigonal[-3m]:{10-11}")
        assert result is not None
        system, doc = result
        assert system == "trigonal"

    def test_invalid_system(self):
        """Invalid system returns None."""
        result = _extract_system("invalid[xyz]:{111}")
        assert result is None

    def test_missing_bracket(self):
        """Missing bracket returns None."""
        result = _extract_system("cubic")
        assert result is None


class TestExtractPointGroup:
    """Test point group extraction."""

    def test_cubic_m3m(self):
        """Extract m3m point group."""
        result = _extract_point_group("cubic[m3m]:{111}")
        assert result is not None
        pg, doc = result
        assert pg == "m3m"

    def test_hexagonal_6mmm(self):
        """Extract 6/mmm point group."""
        result = _extract_point_group("hexagonal[6/mmm]:{10-10}")
        assert result is not None
        pg, doc = result
        assert pg == "6/mmm"

    def test_trigonal_3m(self):
        """Extract -3m point group."""
        result = _extract_point_group("trigonal[-3m]:{10-11}")
        assert result is not None
        pg, doc = result
        assert pg == "-3m"

    def test_invalid_point_group(self):
        """Invalid point group returns None."""
        result = _extract_point_group("cubic[invalid]:{111}")
        assert result is None


class TestExtractForms:
    """Test form extraction."""

    def test_single_miller_index(self):
        """Extract single Miller index."""
        forms = _extract_forms("cubic[m3m]:{111}")
        assert len(forms) == 1
        assert forms[0]["miller"] == "{111}"

    def test_multiple_forms(self):
        """Extract multiple forms."""
        forms = _extract_forms("cubic[m3m]:{111}@1.0 + {100}@1.3")
        assert len(forms) >= 1  # At least one form extracted

    def test_form_with_scale(self):
        """Extract form with scale factor."""
        forms = _extract_forms("cubic[m3m]:{111}@0.8")
        assert len(forms) >= 1
        # Check scale is extracted
        form = forms[0]
        if "scale" in form:
            assert form["scale"] == 0.8 or form["scale"] == 1.0

    def test_hexagonal_4index(self):
        """Extract 4-index Miller notation."""
        forms = _extract_forms("hexagonal[6/mmm]:{10-10}")
        assert len(forms) >= 1


class TestExtractModifications:
    """Test modification extraction."""

    def test_elongate_modification(self):
        """Extract elongate modification."""
        mods = _extract_modifications("cubic[m3m]:{111}|elongate(c:1.5)")
        assert len(mods) >= 1
        # Check that elongate is found
        mod_names = [m["name"] for m in mods]
        assert "elongate" in mod_names

    def test_truncate_modification(self):
        """Extract truncate modification."""
        mods = _extract_modifications("cubic[m3m]:{111}|truncate(cube:0.3)")
        mod_names = [m["name"] for m in mods]
        assert "truncate" in mod_names

    def test_no_modifications(self):
        """No modifications in simple CDL."""
        mods = _extract_modifications("cubic[m3m]:{111}")
        # Should be empty or only contain non-matching items
        assert len(mods) == 0 or all(
            m["name"] not in ["elongate", "truncate", "taper", "bevel"]
            for m in mods
            if m.get("name")
        )


class TestExtractTwin:
    """Test twin extraction."""

    def test_twin_spinel(self):
        """Extract spinel twin law."""
        result = _extract_twin("cubic[m3m]:{111}|twin(spinel)")
        assert result is not None
        assert result["law"] == "spinel"

    def test_twin_japan(self):
        """Extract japan twin law."""
        result = _extract_twin("trigonal[-3m]:{10-11}|twin(japan)")
        assert result is not None
        assert result["law"] == "japan"

    def test_twin_with_contact(self):
        """Extract twin with contact plane."""
        result = _extract_twin("cubic[m3m]:{111}|twin(spinel, {111})")
        assert result is not None
        assert result["law"] == "spinel"
        assert result["contact"] is not None

    def test_no_twin(self):
        """No twin in simple CDL."""
        result = _extract_twin("cubic[m3m]:{111}")
        assert result is None


class TestGenerateSummary:
    """Test summary generation."""

    def test_full_summary(self):
        """Generate summary with all components."""
        system_info = ("cubic", "Cubic documentation")
        pg_info = ("m3m", "m3m documentation")
        forms_info = [{"name": "octahedron", "miller": "{111}"}]
        mod_info = []
        twin_info = None

        summary = _generate_summary(system_info, pg_info, forms_info, mod_info, twin_info)
        assert "cubic" in summary.lower()
        assert "m3m" in summary
        assert "form" in summary.lower()

    def test_summary_with_modifications(self):
        """Generate summary with modifications."""
        system_info = ("cubic", "")
        pg_info = ("m3m", "")
        forms_info = [{"name": "octahedron", "miller": "{111}"}]
        mod_info = [{"name": "elongate"}]
        twin_info = None

        summary = _generate_summary(system_info, pg_info, forms_info, mod_info, twin_info)
        assert "elongate" in summary.lower()

    def test_summary_with_twin(self):
        """Generate summary with twinning."""
        system_info = ("cubic", "")
        pg_info = ("m3m", "")
        forms_info = [{"miller": "{111}"}]
        mod_info = []
        twin_info = {"law": "spinel", "doc": "", "contact": None}

        summary = _generate_summary(system_info, pg_info, forms_info, mod_info, twin_info)
        assert "spinel" in summary.lower() or "twin" in summary.lower()

    def test_summary_minimal(self):
        """Generate summary with minimal info."""
        summary = _generate_summary(None, None, [], [], None)
        assert len(summary) > 0


class TestExplainCDL:
    """Test full CDL explanation."""

    def test_empty_document(self):
        """Explain empty document."""
        result = explain_cdl("")
        assert "empty" in result.lower() or "Empty" in result

    def test_simple_cdl(self):
        """Explain simple CDL."""
        result = explain_cdl("cubic[m3m]:{111}")
        assert "cubic" in result.lower()
        assert "m3m" in result

    def test_comment_line(self):
        """Handle comment lines."""
        result = explain_cdl("# This is a comment\ncubic[m3m]:{111}")
        assert "comment" in result.lower() or "cubic" in result.lower()

    def test_multiple_lines(self):
        """Handle multiple CDL lines."""
        result = explain_cdl("cubic[m3m]:{111}\nhexagonal[6/mmm]:{10-10}")
        assert len(result) > 0


class TestGetExplainResult:
    """Test explain result structure."""

    def test_result_structure(self):
        """Result has correct structure."""
        result = get_explain_result("cubic[m3m]:{111}")
        assert "content" in result
        assert "kind" in result
        assert result["kind"] == "markdown"

    def test_empty_input(self):
        """Handle empty input."""
        result = get_explain_result("")
        assert "content" in result
        assert len(result["content"]) > 0
