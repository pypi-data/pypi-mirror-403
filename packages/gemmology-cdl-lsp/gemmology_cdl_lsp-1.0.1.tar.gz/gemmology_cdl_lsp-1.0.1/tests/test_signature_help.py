"""
Test suite for CDL signature help features.

Tests parameter hints for modifications and twins.
"""

from cdl_lsp.features.signature_help import (
    MODIFICATION_SIGNATURES,
    _find_active_modification,
    get_signature_help,
    get_signature_trigger_characters,
)


class TestModificationSignatures:
    """Test modification signature definitions."""

    def test_elongate_signature(self):
        """Elongate has proper signature."""
        sig = MODIFICATION_SIGNATURES["elongate"]
        assert "label" in sig
        assert "documentation" in sig
        assert "parameters" in sig
        assert len(sig["parameters"]) == 2

    def test_truncate_signature(self):
        """Truncate has proper signature."""
        sig = MODIFICATION_SIGNATURES["truncate"]
        assert "label" in sig
        assert len(sig["parameters"]) == 2

    def test_taper_signature(self):
        """Taper has proper signature."""
        sig = MODIFICATION_SIGNATURES["taper"]
        assert "label" in sig
        assert len(sig["parameters"]) == 2

    def test_bevel_signature(self):
        """Bevel has proper signature."""
        sig = MODIFICATION_SIGNATURES["bevel"]
        assert "label" in sig
        assert len(sig["parameters"]) == 2

    def test_twin_signature(self):
        """Twin has proper signature."""
        sig = MODIFICATION_SIGNATURES["twin"]
        assert "label" in sig
        assert len(sig["parameters"]) == 2


class TestFindActiveModification:
    """Test finding active modification."""

    def test_no_modification(self):
        """No modification returns None."""
        mod, param = _find_active_modification("cubic[m3m]:{111}", 15)
        assert mod is None
        assert param == 0

    def test_elongate_first_param(self):
        """Inside elongate first parameter."""
        mod, param = _find_active_modification("elongate(", 9)
        assert mod == "elongate"
        assert param == 0

    def test_elongate_second_param(self):
        """Inside elongate second parameter."""
        mod, param = _find_active_modification("elongate(a:", 11)
        assert mod == "elongate"
        assert param == 1

    def test_truncate_first_param(self):
        """Inside truncate first parameter."""
        mod, param = _find_active_modification("truncate(", 9)
        assert mod == "truncate"
        assert param == 0

    def test_twin_first_param(self):
        """Inside twin first parameter."""
        mod, param = _find_active_modification("twin(", 5)
        assert mod == "twin"
        assert param == 0

    def test_twin_second_param(self):
        """Inside twin second parameter."""
        mod, param = _find_active_modification("twin(spinel,", 12)
        assert mod == "twin"
        assert param == 1

    def test_after_close_paren(self):
        """After close paren returns None."""
        mod, param = _find_active_modification("elongate(a:1.5)", 15)
        assert mod is None

    def test_case_insensitive(self):
        """Modification detection is case insensitive."""
        mod, param = _find_active_modification("ELONGATE(", 9)
        assert mod == "elongate"


class TestGetSignatureHelp:
    """Test signature help generation."""

    def test_no_modification(self):
        """No modification returns None."""
        result = get_signature_help("cubic[m3m]", 10)
        # Without lsprotocol, returns None
        # With lsprotocol, might return None if not in modification
        assert result is None

    def test_inside_modification(self):
        """Inside modification may return help."""
        _result = get_signature_help("elongate(", 9)
        # Depends on whether lsprotocol is available
        # Just verify it doesn't crash
        assert _result is None or hasattr(_result, "signatures")


class TestTriggerCharacters:
    """Test trigger character configuration."""

    def test_trigger_chars(self):
        """Trigger characters include ( and ,."""
        chars = get_signature_trigger_characters()
        assert "(" in chars
        assert "," in chars
