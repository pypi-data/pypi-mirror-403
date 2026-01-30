"""Tests for the BibTeX formatter (Phase 1)."""

from conftest import (
    FORMATTER_EXPECTED_SINGLE_LINE,
    FORMATTER_RAW_AUTHOR_COMMAS,
    FORMATTER_RAW_NESTED_BRACES,
    FORMATTER_RAW_SINGLE_LINE,
    FORMATTER_RAW_TRAILING_COMMA,
)
from fetchbib.formatter import format_bibtex


class TestFormatBibtex:
    """Tests for format_bibtex()."""

    def test_single_line_is_formatted(self):
        """Single-line BibTeX is split into indented, alphabetized fields."""
        assert (
            format_bibtex(FORMATTER_RAW_SINGLE_LINE) == FORMATTER_EXPECTED_SINGLE_LINE
        )

    def test_idempotent(self):
        """Already-formatted BibTeX passes through unchanged."""
        assert (
            format_bibtex(FORMATTER_EXPECTED_SINGLE_LINE)
            == FORMATTER_EXPECTED_SINGLE_LINE
        )

    def test_author_commas_preserved(self):
        """Commas inside braces (author names) are not treated as field separators."""
        result = format_bibtex(FORMATTER_RAW_AUTHOR_COMMAS)
        assert "author = {DeVerna, Matthew R. and Yan, Harry Yaojun" in result

    def test_trailing_comma_removed(self):
        """A trailing comma before the closing brace is stripped."""
        result = format_bibtex(FORMATTER_RAW_TRAILING_COMMA)
        # The last field line should not end with a comma
        lines = result.strip().split("\n")
        last_field_line = lines[-2]  # line before closing '}'
        assert not last_field_line.rstrip().endswith(",")

    def test_nested_braces_preserved(self):
        """Nested braces in field values are kept intact."""
        result = format_bibtex(FORMATTER_RAW_NESTED_BRACES)
        assert "title = {A {GPU}-Accelerated Approach}" in result
