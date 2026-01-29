"""DOI resolution and Crossref search.

Provides functions to check if a string is a DOI, resolve a DOI to BibTeX,
search Crossref for a DOI, and an orchestrator that combines them.
"""

import re

import requests

from fetchbib import config

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
DOI_URL_PREFIXES = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
)

DOI_BASE_URL = "https://doi.org/"
CROSSREF_API_URL = "https://api.crossref.org/works"


class ResolverError(Exception):
    """Raised when DOI resolution or Crossref search fails."""


def normalize_doi_input(value: str) -> str:
    """Strip common DOI URL prefixes, returning a bare DOI if possible.

    For example, ``https://doi.org/10.2196/jmir.1933`` becomes
    ``10.2196/jmir.1933``. Non-URL strings are returned unchanged.
    """
    for prefix in DOI_URL_PREFIXES:
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def is_doi(value: str) -> bool:
    """Return True if *value* looks like a bare DOI (e.g. 10.xxxx/yyyy)."""
    return bool(DOI_PATTERN.match(value))


def get_user_agent() -> str:
    """Build the User-Agent string using the configured email."""
    email = config.get_email()
    return f"fetchbib/1.0 (mailto:{email})"


def resolve_doi(doi: str) -> str:
    """Fetch BibTeX for a DOI from doi.org.

    Raises ResolverError on non-200 responses.
    """
    headers = {
        "Accept": "text/bibliography; style=bibtex",
        "User-Agent": get_user_agent(),
    }
    resp = requests.get(f"{DOI_BASE_URL}{doi}", headers=headers)
    if resp.status_code != 200:
        raise ResolverError(
            f"DOI resolution failed for '{doi}': HTTP {resp.status_code}"
        )
    return resp.text


def search_crossref(query: str) -> str:
    """Search Crossref and return the DOI of the first result.

    Raises ResolverError on non-200 responses or empty results.
    """
    headers = {"User-Agent": get_user_agent()}
    resp = requests.get(CROSSREF_API_URL, params={"query": query}, headers=headers)
    if resp.status_code != 200:
        raise ResolverError(f"Crossref search failed: HTTP {resp.status_code}")
    items = resp.json()["message"]["items"]
    if not items:
        raise ResolverError(f"No results found for query: '{query}'")
    return items[0]["DOI"]


def resolve(query: str) -> str:
    """Resolve a DOI, DOI URL, or free-text query to raw BibTeX.

    DOI URLs (e.g. https://doi.org/10.xxxx/yyyy) are normalized to bare
    DOIs before resolution. If the input is a DOI, fetches directly.
    Otherwise searches Crossref for the top result and resolves that DOI.
    """
    query = normalize_doi_input(query)
    if is_doi(query):
        return resolve_doi(query)
    doi = search_crossref(query)
    return resolve_doi(doi)
