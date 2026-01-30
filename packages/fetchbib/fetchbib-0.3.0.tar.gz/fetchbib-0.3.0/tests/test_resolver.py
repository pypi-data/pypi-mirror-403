"""Tests for the resolver (Phase 2).

All HTTP calls are mocked — no network access needed.
"""

from unittest.mock import MagicMock, patch

import pytest

from conftest import DOI_A, SEARCH_QUERY_A
from fetchbib.resolver import (
    ResolverError,
    extract_arxiv_id,
    is_arxiv_doi,
    is_doi,
    normalize_doi_input,
    resolve,
    resolve_arxiv,
    resolve_doi,
    search_crossref,
)

# ---------------------------------------------------------------------------
# is_doi
# ---------------------------------------------------------------------------


class TestIsDoi:
    """Tests for DOI pattern matching."""

    @pytest.mark.parametrize(
        "value",
        [
            "10.2196/jmir.1933",
            "10.1000/xyz123",
            "10.1234/some-thing_(here)",
        ],
    )
    def test_valid_dois(self, value):
        assert is_doi(value) is True

    @pytest.mark.parametrize(
        "value",
        [
            "not a doi",
            "10.12345",  # no suffix after slash
            "",
            "http://doi.org/10.2196/jmir.1933",  # full URL
        ],
    )
    def test_invalid_inputs(self, value):
        assert is_doi(value) is False


# ---------------------------------------------------------------------------
# is_arxiv_doi
# ---------------------------------------------------------------------------


class TestIsArxivDoi:
    """Tests for arXiv DOI detection."""

    @pytest.mark.parametrize(
        "value",
        [
            "10.48550/arXiv.2410.21554",
            "10.48550/arxiv.2410.21554",  # lowercase
            "10.48550/ARXIV.2410.21554",  # uppercase
            "10.48550/arXiv.1234.56789",
            "10.48550/arXiv.hep-ph/0307015",
        ],
    )
    def test_valid_arxiv_dois(self, value):
        assert is_arxiv_doi(value) is True

    @pytest.mark.parametrize(
        "value",
        [
            "10.2196/jmir.1933",  # regular DOI
            "10.1073/pnas.2322823121",  # PNAS DOI
            "10.48550/other.1234",  # different prefix after 10.48550
            "",
        ],
    )
    def test_non_arxiv_dois(self, value):
        assert is_arxiv_doi(value) is False


# ---------------------------------------------------------------------------
# extract_arxiv_id
# ---------------------------------------------------------------------------


class TestExtractArxivId:
    """Tests for extracting arXiv ID from DOI."""

    @pytest.mark.parametrize(
        "doi,expected",
        [
            ("10.48550/arXiv.2410.21554", "2410.21554"),
            ("10.48550/arXiv.1234.56789", "1234.56789"),
            ("10.48550/arXiv.hep-ph/0307015", "hep-ph/0307015"),
        ],
    )
    def test_extracts_arxiv_id(self, doi, expected):
        assert extract_arxiv_id(doi) == expected


# ---------------------------------------------------------------------------
# resolve_arxiv
# ---------------------------------------------------------------------------


class TestResolveArxiv:
    """Tests for fetching BibTeX from arXiv."""

    @patch("fetchbib.resolver.requests.get")
    def test_returns_bibtex_on_success(self, mock_get):
        bibtex = "@misc{deverna2024, author={DeVerna}, year={2024}}"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = bibtex
        mock_get.return_value = mock_resp

        result = resolve_arxiv("2410.21554")

        assert result == bibtex
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "arxiv.org/bibtex/2410.21554" in call_args[0][0]

    @patch("fetchbib.resolver.requests.get")
    def test_raises_on_http_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        with pytest.raises(ResolverError, match="arXiv resolution failed.*404"):
            resolve_arxiv("9999.99999")


# ---------------------------------------------------------------------------
# normalize_doi_input
# ---------------------------------------------------------------------------


class TestNormalizeDOIInput:
    """Tests for stripping DOI URL prefixes."""

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://doi.org/10.2196/jmir.1933", "10.2196/jmir.1933"),
            ("http://doi.org/10.2196/jmir.1933", "10.2196/jmir.1933"),
            ("https://dx.doi.org/10.2196/jmir.1933", "10.2196/jmir.1933"),
            ("http://dx.doi.org/10.2196/jmir.1933", "10.2196/jmir.1933"),
        ],
    )
    def test_strips_doi_url_prefixes(self, url, expected):
        assert normalize_doi_input(url) == expected

    def test_bare_doi_unchanged(self):
        assert normalize_doi_input("10.2196/jmir.1933") == "10.2196/jmir.1933"

    def test_non_doi_string_unchanged(self):
        assert normalize_doi_input(SEARCH_QUERY_A) == SEARCH_QUERY_A


# ---------------------------------------------------------------------------
# resolve_doi
# ---------------------------------------------------------------------------


class TestResolveDoi:
    """Tests for fetching BibTeX from doi.org."""

    @patch("fetchbib.resolver.requests.get")
    def test_returns_bibtex_on_success(self, mock_get):
        bibtex = "@article{Key, author={Someone}, year={2020}}"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = bibtex
        mock_get.return_value = mock_resp

        result = resolve_doi("10.1234/test")

        assert result == bibtex
        # Verify correct headers were sent
        call_kwargs = mock_get.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert headers["Accept"] == "text/bibliography; style=bibtex"
        assert "fetchbib" in headers["User-Agent"]

    @patch("fetchbib.resolver.requests.get")
    def test_raises_on_http_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        with pytest.raises(ResolverError, match="404"):
            resolve_doi("10.1234/missing")


# ---------------------------------------------------------------------------
# search_crossref
# ---------------------------------------------------------------------------


class TestSearchCrossref:
    """Tests for the Crossref search API."""

    @patch("fetchbib.resolver.requests.get")
    def test_returns_list_of_dois(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {
                "items": [
                    {"DOI": DOI_A},
                    {"DOI": "10.9999/other"},
                ]
            }
        }
        mock_get.return_value = mock_resp

        result = search_crossref(SEARCH_QUERY_A)
        assert result == [DOI_A]

    @patch("fetchbib.resolver.requests.get")
    def test_max_results_parameter(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {
                "items": [
                    {"DOI": DOI_A},
                    {"DOI": "10.9999/second"},
                    {"DOI": "10.9999/third"},
                ]
            }
        }
        mock_get.return_value = mock_resp

        result = search_crossref(SEARCH_QUERY_A, max_results=3)
        assert result == [DOI_A, "10.9999/second", "10.9999/third"]
        # Verify rows parameter was passed
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params", {})
        assert params["rows"] == 3

    @patch("fetchbib.resolver.requests.get")
    def test_raises_on_empty_results(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"message": {"items": []}}
        mock_get.return_value = mock_resp

        with pytest.raises(ResolverError, match="[Nn]o results"):
            search_crossref("nonexistent gibberish query")

    @patch("fetchbib.resolver.requests.get")
    def test_raises_on_http_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_get.return_value = mock_resp

        with pytest.raises(ResolverError, match="503"):
            search_crossref("anything")


# ---------------------------------------------------------------------------
# resolve (orchestrator)
# ---------------------------------------------------------------------------


class TestResolve:
    """Tests for the top-level resolve() orchestrator."""

    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_crossref")
    def test_routes_doi_directly(self, mock_search, mock_resolve_doi):
        mock_resolve_doi.return_value = "@article{...}"

        resolve("10.2196/jmir.1933")

        mock_resolve_doi.assert_called_once_with("10.2196/jmir.1933")
        mock_search.assert_not_called()

    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_crossref")
    def test_routes_non_doi_through_search(self, mock_search, mock_resolve_doi):
        mock_search.return_value = [DOI_A]
        mock_resolve_doi.return_value = "@article{...}"

        resolve(SEARCH_QUERY_A)

        mock_search.assert_called_once_with(SEARCH_QUERY_A)
        mock_resolve_doi.assert_called_once_with(DOI_A)

    @patch("fetchbib.resolver.resolve_arxiv")
    @patch("fetchbib.resolver.resolve_doi")
    @patch("fetchbib.resolver.search_crossref")
    def test_routes_arxiv_doi_to_arxiv(self, mock_search, mock_resolve_doi, mock_arxiv):
        mock_arxiv.return_value = "@misc{deverna2024...}"

        resolve("10.48550/arXiv.2410.21554")

        mock_arxiv.assert_called_once_with("2410.21554")
        mock_resolve_doi.assert_not_called()
        mock_search.assert_not_called()


# ---------------------------------------------------------------------------
# Config / User-Agent
# ---------------------------------------------------------------------------


class TestUserAgentConfig:
    """Tests for configurable User-Agent email."""

    @patch("fetchbib.resolver.requests.get")
    @patch("fetchbib.resolver.config.get_email", return_value="custom@university.edu")
    def test_custom_email_in_user_agent(self, _mock_email, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "@article{...}"
        mock_get.return_value = mock_resp

        resolve_doi("10.1234/test")

        headers = (
            mock_get.call_args.kwargs.get("headers") or mock_get.call_args[1]["headers"]
        )
        assert "custom@university.edu" in headers["User-Agent"]
