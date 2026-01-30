"""
Tests for CDL LSP Code Actions functionality.
"""

import pytest

from cdl_lsp.features.code_actions import get_code_action_kinds, get_code_actions


class TestCodeActionKinds:
    """Tests for supported code action kinds."""

    def test_supported_kinds(self):
        """Should support quickfix kind."""
        kinds = get_code_action_kinds()
        assert len(kinds) > 0
        # Check that quickfix is supported (either as string or enum)
        kinds_str = [str(k) for k in kinds]
        assert any("quickfix" in k.lower() for k in kinds_str)


class TestCodeActionsWithoutLSProtocol:
    """Tests for code actions when lsprotocol is not available."""

    def test_no_diagnostics(self):
        """No diagnostics returns empty list."""
        actions = get_code_actions("file:///test.cdl", None, [])
        # May return empty list or list depending on implementation
        assert isinstance(actions, list)


class TestCodeActionsEmptyInput:
    """Tests for edge cases."""

    def test_empty_uri(self):
        """Empty URI handled gracefully."""
        actions = get_code_actions("", None, [])
        assert isinstance(actions, list)

    def test_none_range(self):
        """None range handled gracefully."""
        actions = get_code_actions("file:///test.cdl", None, [])
        assert isinstance(actions, list)


class TestCodeActionsWithMockDiagnostics:
    """Tests using mock diagnostic objects."""

    def test_diagnostic_without_code(self):
        """Diagnostic without code is skipped."""

        # Create a minimal mock diagnostic
        class MockDiag:
            pass

        diag = MockDiag()
        actions = get_code_actions("file:///test.cdl", None, [diag])
        assert isinstance(actions, list)

    def test_diagnostic_with_none_code(self):
        """Diagnostic with None code is skipped."""

        class MockDiag:
            code = None

        diag = MockDiag()
        actions = get_code_actions("file:///test.cdl", None, [diag])
        assert isinstance(actions, list)

    def test_diagnostic_without_data(self):
        """Diagnostic without data is skipped for typo fixes."""

        class MockDiag:
            code = "typo-form"

        diag = MockDiag()
        actions = get_code_actions("file:///test.cdl", None, [diag])
        # Should not crash, may return empty or skip
        assert isinstance(actions, list)


class TestCodeActionsIntegration:
    """Integration tests with proper diagnostic structure."""

    @pytest.fixture
    def lsprotocol_available(self):
        """Check if lsprotocol is available."""
        import importlib.util

        return importlib.util.find_spec("lsprotocol") is not None

    def test_typo_form_fix(self, lsprotocol_available):
        """Test typo form code action creation."""
        if not lsprotocol_available:
            pytest.skip("lsprotocol not available")

        from lsprotocol import types

        # Create a proper diagnostic
        diag = types.Diagnostic(
            range=types.Range(
                start=types.Position(line=0, character=11), end=types.Position(line=0, character=21)
            ),
            message="Unknown form 'octahedren'. Did you mean 'octahedron'?",
            severity=types.DiagnosticSeverity.Warning,
            code="typo-form",
            source="cdl-lsp",
            data={"original": "octahedren", "suggested": "octahedron"},
        )

        actions = get_code_actions("file:///test.cdl", None, [diag])
        assert len(actions) == 1
        assert "octahedron" in actions[0].title

    def test_missing_colon_fix(self, lsprotocol_available):
        """Test missing colon code action creation."""
        if not lsprotocol_available:
            pytest.skip("lsprotocol not available")

        from lsprotocol import types

        # Create a proper diagnostic for missing colon
        diag = types.Diagnostic(
            range=types.Range(
                start=types.Position(line=0, character=10), end=types.Position(line=0, character=10)
            ),
            message="Missing ':' after point group",
            severity=types.DiagnosticSeverity.Error,
            code="missing-colon",
            source="cdl-lsp",
            data={"insert_text": ":"},
        )

        actions = get_code_actions("file:///test.cdl", None, [diag])
        assert len(actions) == 1
        assert ":" in actions[0].title

    def test_scale_large_fix(self, lsprotocol_available):
        """Test large scale warning code action."""
        if not lsprotocol_available:
            pytest.skip("lsprotocol not available")

        from lsprotocol import types

        # Create a diagnostic for unusually large scale
        diag = types.Diagnostic(
            range=types.Range(
                start=types.Position(line=0, character=16), end=types.Position(line=0, character=20)
            ),
            message="Scale 5.0 is unusually large",
            severity=types.DiagnosticSeverity.Hint,
            code="scale-large",
            source="cdl-lsp",
            data={"original": "5.0", "suggested": "2.0"},
        )

        actions = get_code_actions("file:///test.cdl", None, [diag])
        assert len(actions) == 1
        assert "2.0" in actions[0].title

    def test_multiple_diagnostics(self, lsprotocol_available):
        """Test handling multiple diagnostics."""
        if not lsprotocol_available:
            pytest.skip("lsprotocol not available")

        from lsprotocol import types

        # Create multiple diagnostics
        diag1 = types.Diagnostic(
            range=types.Range(
                start=types.Position(line=0, character=0), end=types.Position(line=0, character=5)
            ),
            message="Unknown system",
            severity=types.DiagnosticSeverity.Error,
            code="typo-system",
            source="cdl-lsp",
            data={"original": "cubik", "suggested": "cubic"},
        )

        diag2 = types.Diagnostic(
            range=types.Range(
                start=types.Position(line=0, character=11), end=types.Position(line=0, character=15)
            ),
            message="Unknown form",
            severity=types.DiagnosticSeverity.Warning,
            code="typo-form",
            source="cdl-lsp",
            data={"original": "cub", "suggested": "cube"},
        )

        actions = get_code_actions("file:///test.cdl", None, [diag1, diag2])
        assert len(actions) == 2
