"""Command-line interface for fetchbib.

Entry point: ``fbib``
"""

import argparse
import sys

from fetchbib import config
from fetchbib.formatter import format_bibtex
from fetchbib.resolver import (
    ResolverError,
    is_doi,
    normalize_doi_input,
    resolve_doi,
    search_crossref,
)


def main() -> None:
    """Parse arguments and resolve each input to formatted BibTeX."""
    parser = argparse.ArgumentParser(
        prog="fbib",
        description="Resolve DOIs or search queries into formatted BibTeX.",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="DOIs or search queries (comma-separated values are split)",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Path to a text file with one input per line",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write results to this file instead of stdout",
    )
    parser.add_argument(
        "-a",
        "--append",
        action="store_true",
        help="Append to the output file instead of overwriting (requires --output)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print which DOI was selected for search queries",
    )
    parser.add_argument(
        "--config-email",
        metavar="EMAIL",
        help="Set the email used in the User-Agent header and exit",
    )

    args = parser.parse_args()

    # --config-email: save and exit immediately
    if args.config_email:
        config.set_email(args.config_email)
        sys.exit(0)

    # Collect inputs
    queries = _collect_inputs(args)
    if not queries:
        print(
            "Error: no inputs provided. Pass DOIs/queries as arguments or use --file.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Resolve each input
    results: list[str] = []
    had_error = False

    for query in queries:
        try:
            bibtex = _resolve_single(query, verbose=args.verbose)
            results.append(bibtex)
        except ResolverError as exc:
            print(f"Error resolving '{query}': {exc}", file=sys.stderr)
            had_error = True

    output_text = "\n\n".join(results)
    if results:
        output_text += "\n"

    # Write output
    if args.output:
        mode = "a" if args.append else "w"
        with open(args.output, mode) as f:
            f.write(output_text)
    else:
        print(output_text, end="")

    if had_error:
        sys.exit(1)


def _collect_inputs(args: argparse.Namespace) -> list[str]:
    """Gather inputs from positional args and --file, deduplicate."""
    raw: list[str] = []

    # Positional args (each may be comma-separated)
    for arg in args.inputs or []:
        raw.extend(_split_and_strip(arg))

    # File input (each line may also be comma-separated)
    if args.file:
        try:
            with open(args.file) as f:
                for line in f:
                    raw.extend(_split_and_strip(line))
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)

    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for item in raw:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _split_and_strip(value: str) -> list[str]:
    """Split a string on commas and return non-empty stripped parts."""
    return [part.strip() for part in value.split(",") if part.strip()]


def _resolve_single(query: str, *, verbose: bool) -> str:
    """Resolve a single query to formatted BibTeX."""
    query = normalize_doi_input(query)
    if is_doi(query):
        raw = resolve_doi(query)
    else:
        doi = search_crossref(query)
        if verbose:
            print(
                f'Searching for: "{query}" -> DOI: {doi}',
                file=sys.stderr,
            )
        raw = resolve_doi(doi)
    return format_bibtex(raw)
