"""Tests for the BibTeX formatter (Phase 1)."""

from fetchbib.formatter import format_bibtex


class TestFormatBibtex:
    """Tests for format_bibtex()."""

    def test_single_line_is_formatted(self):
        """Single-line BibTeX is split into indented, alphabetized fields."""
        raw = (
            "@article{Eysenbach2011,"
            "doi={10.2196/jmir.1933},"
            "title={Can Tweets Predict Citations?},"
            "author={Eysenbach, Gunther},"
            "year={2011},"
            "journal={JMIR}}"
        )
        expected = (
            "@article{Eysenbach2011,\n"
            "  author = {Eysenbach, Gunther},\n"
            "  doi = {10.2196/jmir.1933},\n"
            "  journal = {JMIR},\n"
            "  title = {Can Tweets Predict Citations?},\n"
            "  year = {2011}\n"
            "}"
        )
        assert format_bibtex(raw) == expected

    def test_idempotent(self):
        """Already-formatted BibTeX passes through unchanged."""
        clean = (
            "@article{Eysenbach2011,\n"
            "  author = {Eysenbach, Gunther},\n"
            "  doi = {10.2196/jmir.1933},\n"
            "  journal = {JMIR},\n"
            "  title = {Can Tweets Predict Citations?},\n"
            "  year = {2011}\n"
            "}"
        )
        assert format_bibtex(clean) == clean

    def test_author_commas_preserved(self):
        """Commas inside braces (author names) are not treated as field separators."""
        raw = (
            "@article{Key2020,"
            "author={Last, First and Last2, First2},"
            "title={A Title},"
            "year={2020}}"
        )
        result = format_bibtex(raw)
        assert "author = {Last, First and Last2, First2}" in result

    def test_trailing_comma_removed(self):
        """A trailing comma before the closing brace is stripped."""
        raw = "@article{Key2020," "author={Someone}," "year={2020},}"
        result = format_bibtex(raw)
        # The last field line should not end with a comma
        lines = result.strip().split("\n")
        last_field_line = lines[-2]  # line before closing '}'
        assert not last_field_line.rstrip().endswith(",")

    def test_nested_braces_preserved(self):
        """Nested braces in field values are kept intact."""
        raw = (
            "@inproceedings{Key2021,"
            "title={A {GPU}-Accelerated Approach},"
            "author={Smith, John},"
            "year={2021}}"
        )
        result = format_bibtex(raw)
        assert "title = {A {GPU}-Accelerated Approach}" in result
