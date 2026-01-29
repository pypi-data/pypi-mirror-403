"""Integration tests that hit live APIs.

Skipped by default. Run with:
    pytest -m integration
"""

import tempfile

import pytest

from fetchbib.formatter import format_bibtex
from fetchbib.resolver import resolve, resolve_doi, search_crossref

pytestmark = pytest.mark.integration


class TestLiveResolution:
    """End-to-end tests against doi.org and Crossref."""

    def test_doi_resolution(self):
        raw = resolve_doi("10.2196/jmir.1933")
        result = format_bibtex(raw)
        assert "Eysenbach" in result
        assert "2011" in result

    def test_free_text_search(self):
        doi = search_crossref("Eysenbach JMIR 2011")
        raw = resolve_doi(doi)
        result = format_bibtex(raw)
        assert "Eysenbach" in result

    def test_file_input_via_cli(self):
        """Resolve a DOI through the full CLI path."""
        import sys
        from io import StringIO
        from unittest.mock import patch

        from fetchbib.cli import main

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("10.2196/jmir.1933\n")
            f.flush()
            path = f.name

        old_argv = sys.argv
        sys.argv = ["fbib", "--file", path]
        stdout_capture = StringIO()

        try:
            with patch("sys.stdout", stdout_capture):
                main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

        output = stdout_capture.getvalue()
        assert "Eysenbach" in output
