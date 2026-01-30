"""
Test suite for CDL completion features.

Tests context detection and completion generation for all CDL contexts.
"""

from cdl_lsp.features.completion import (
    CompletionContext,
    _detect_context,
    _get_system_from_line,
    get_completions,
)


class TestDetectContext:
    """Test completion context detection."""

    def test_empty_line(self):
        """Empty line returns EMPTY context."""
        ctx, word = _detect_context("", 0)
        assert ctx == CompletionContext.EMPTY
        assert word == ""

    def test_whitespace_only(self):
        """Whitespace-only returns EMPTY context."""
        ctx, word = _detect_context("   ", 3)
        assert ctx == CompletionContext.EMPTY

    def test_system_partial(self):
        """Partial system name returns SYSTEM context."""
        ctx, word = _detect_context("cub", 3)
        assert ctx == CompletionContext.SYSTEM
        assert word == "cub"

    def test_system_full(self):
        """Full system name returns SYSTEM context."""
        ctx, word = _detect_context("cubic", 5)
        assert ctx == CompletionContext.SYSTEM
        assert word == "cubic"

    def test_point_group_open_bracket(self):
        """Open bracket returns POINT_GROUP context."""
        ctx, word = _detect_context("cubic[", 6)
        assert ctx == CompletionContext.POINT_GROUP
        assert word == ""

    def test_point_group_partial(self):
        """Partial point group returns POINT_GROUP context."""
        ctx, word = _detect_context("cubic[m3", 8)
        assert ctx == CompletionContext.POINT_GROUP
        assert word == "m3"

    def test_after_colon(self):
        """After colon returns AFTER_COLON context."""
        ctx, word = _detect_context("cubic[m3m]:", 11)
        assert ctx == CompletionContext.AFTER_COLON
        assert word == ""

    def test_miller_index_start(self):
        """Inside braces returns MILLER_INDEX context."""
        ctx, word = _detect_context("cubic[m3m]:{", 12)
        assert ctx == CompletionContext.MILLER_INDEX
        assert word == ""

    def test_miller_index_partial(self):
        """Partial Miller index returns MILLER_INDEX context."""
        ctx, word = _detect_context("cubic[m3m]:{11", 14)
        assert ctx == CompletionContext.MILLER_INDEX
        assert word == "11"

    def test_after_at(self):
        """After @ returns AFTER_AT context."""
        ctx, word = _detect_context("cubic[m3m]:{111}@", 17)
        assert ctx == CompletionContext.AFTER_AT
        assert word == ""

    def test_after_plus(self):
        """After + returns AFTER_PLUS context."""
        ctx, word = _detect_context("cubic[m3m]:{111}@1.0 + ", 23)
        assert ctx == CompletionContext.AFTER_PLUS
        assert word == ""

    def test_after_pipe(self):
        """After | returns AFTER_PIPE context."""
        ctx, word = _detect_context("cubic[m3m]:{111}|", 17)
        assert ctx == CompletionContext.AFTER_PIPE
        assert word == ""

    def test_after_pipe_partial(self):
        """Partial modification after | returns AFTER_PIPE context."""
        ctx, word = _detect_context("cubic[m3m]:{111}|tw", 19)
        assert ctx == CompletionContext.AFTER_PIPE
        assert word == "tw"

    def test_twin_law_context(self):
        """Inside twin() returns TWIN_LAW context."""
        ctx, word = _detect_context("cubic[m3m]:{111}|twin(", 22)
        assert ctx == CompletionContext.TWIN_LAW
        assert word == ""

    def test_twin_law_partial(self):
        """Partial twin law returns TWIN_LAW context."""
        ctx, word = _detect_context("cubic[m3m]:{111}|twin(sp", 24)
        assert ctx == CompletionContext.TWIN_LAW
        assert word == "sp"

    def test_modification_param(self):
        """Inside elongate() returns MODIFICATION_PARAM context."""
        ctx, word = _detect_context("cubic[m3m]:{111}|elongate(", 26)
        assert ctx == CompletionContext.MODIFICATION_PARAM

    def test_truncate_param(self):
        """Inside truncate() returns MODIFICATION_PARAM context."""
        ctx, word = _detect_context("cubic[m3m]:{111}|truncate(", 26)
        assert ctx == CompletionContext.MODIFICATION_PARAM

    def test_taper_param(self):
        """Inside taper() returns MODIFICATION_PARAM context."""
        ctx, word = _detect_context("cubic[m3m]:{111}|taper(", 23)
        assert ctx == CompletionContext.MODIFICATION_PARAM

    def test_bevel_param(self):
        """Inside bevel() returns MODIFICATION_PARAM context."""
        ctx, word = _detect_context("cubic[m3m]:{111}|bevel(", 23)
        assert ctx == CompletionContext.MODIFICATION_PARAM


class TestGetSystemFromLine:
    """Test crystal system extraction."""

    def test_cubic_system(self):
        """Extract cubic system."""
        assert _get_system_from_line("cubic[m3m]:{111}") == "cubic"

    def test_hexagonal_system(self):
        """Extract hexagonal system."""
        assert _get_system_from_line("hexagonal[6/mmm]:{10-10}") == "hexagonal"

    def test_trigonal_system(self):
        """Extract trigonal system."""
        assert _get_system_from_line("trigonal[-3m]:{10-11}") == "trigonal"

    def test_invalid_system(self):
        """Invalid system returns None."""
        assert _get_system_from_line("invalid[xyz]") is None

    def test_empty_line(self):
        """Empty line returns None."""
        assert _get_system_from_line("") is None


class TestGetCompletions:
    """Test completion item generation."""

    def test_empty_line_returns_systems(self):
        """Empty line should return crystal systems."""
        completions = get_completions("", 0)
        labels = [c.label for c in completions]
        assert "cubic" in labels
        assert "hexagonal" in labels
        assert "trigonal" in labels
        assert "tetragonal" in labels
        assert "orthorhombic" in labels
        assert "monoclinic" in labels
        assert "triclinic" in labels

    def test_system_prefix_filters(self):
        """System prefix should filter completions."""
        completions = get_completions("cub", 3)
        labels = [c.label for c in completions]
        assert "cubic" in labels
        # Other systems should not match "cub"
        assert "hexagonal" not in labels

    def test_point_group_completions_for_cubic(self):
        """Point group completions for cubic system."""
        completions = get_completions("cubic[", 6)
        labels = [c.label for c in completions]
        assert "m3m" in labels
        assert "432" in labels

    def test_point_group_completions_for_hexagonal(self):
        """Point group completions for hexagonal system."""
        completions = get_completions("hexagonal[", 10)
        labels = [c.label for c in completions]
        assert "6/mmm" in labels

    def test_form_completions_after_colon(self):
        """Form completions after colon."""
        completions = get_completions("cubic[m3m]:", 11)
        labels = [c.label for c in completions]
        # Should include named forms
        assert "octahedron" in labels or "cube" in labels or "{" in labels

    def test_miller_index_completions(self):
        """Miller index completions inside braces."""
        completions = get_completions("cubic[m3m]:{", 12)
        labels = [c.label for c in completions]
        # Should suggest common Miller indices
        assert any("{111}" in label or "111" in label for label in labels)

    def test_scale_completions_after_at(self):
        """Scale completions after @."""
        completions = get_completions("cubic[m3m]:{111}@", 17)
        labels = [c.label for c in completions]
        assert "1.0" in labels or any("1" in label for label in labels)

    def test_modification_completions_after_pipe(self):
        """Modification completions after |."""
        completions = get_completions("cubic[m3m]:{111}|", 17)
        labels = [c.label for c in completions]
        assert "twin" in labels
        assert "elongate" in labels

    def test_twin_law_completions(self):
        """Twin law completions inside twin()."""
        completions = get_completions("cubic[m3m]:{111}|twin(", 22)
        labels = [c.label for c in completions]
        assert "spinel" in labels

    def test_elongate_param_completions(self):
        """Parameter completions for elongate."""
        completions = get_completions("cubic[m3m]:{111}|elongate(", 26)
        labels = [c.label for c in completions]
        # Should suggest axis parameters
        assert any("a:" in label or "b:" in label or "c:" in label for label in labels)

    def test_truncate_param_completions(self):
        """Parameter completions for truncate."""
        completions = get_completions("cubic[m3m]:{111}|truncate(", 26)
        labels = [c.label for c in completions]
        # Should suggest forms for truncation
        assert len(labels) > 0
