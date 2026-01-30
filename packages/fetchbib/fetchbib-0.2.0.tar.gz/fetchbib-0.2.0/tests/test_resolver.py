"""Tests for the resolver (Phase 2).

All HTTP calls are mocked — no network access needed.
"""

from unittest.mock import MagicMock, patch

import pytest

from conftest import DOI_A, SEARCH_QUERY_A
from fetchbib.resolver import (
    ResolverError,
    is_doi,
    normalize_doi_input,
    resolve,
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
    def test_returns_fewer_if_crossref_has_fewer(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {
                "items": [
                    {"DOI": DOI_A},
                ]
            }
        }
        mock_get.return_value = mock_resp

        result = search_crossref(SEARCH_QUERY_A, max_results=5)
        assert result == [DOI_A]

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
    def test_routes_doi_url_directly(self, mock_search, mock_resolve_doi):
        mock_resolve_doi.return_value = "@article{...}"

        resolve("https://doi.org/10.2196/jmir.1933")

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

    @patch("fetchbib.resolver.requests.get")
    @patch("fetchbib.resolver.config.get_email", return_value="fetchbib@example.com")
    def test_default_email_in_user_agent(self, _mock_email, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "@article{...}"
        mock_get.return_value = mock_resp

        resolve_doi("10.1234/test")

        headers = (
            mock_get.call_args.kwargs.get("headers") or mock_get.call_args[1]["headers"]
        )
        assert "fetchbib@example.com" in headers["User-Agent"]
