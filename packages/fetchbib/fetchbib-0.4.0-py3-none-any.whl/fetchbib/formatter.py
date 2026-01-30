"""BibTeX string formatter.

Transforms raw (often single-line) BibTeX into a clean, readable format
with alphabetized fields, 2-space indentation, and proper line breaks.
"""


def format_bibtex(
    raw: str,
    *,
    protect_titles: bool = False,
    exclude_issn: bool = False,
    exclude_doi: bool = False,
) -> str:
    """Format a raw BibTeX entry into a clean, readable string.

    Rules:
        - Entry header (@type{key,) stays on the first line.
        - Each field is on its own line with 2-space indentation.
        - Fields are alphabetized.
        - Closing brace is on its own line.
        - Trailing commas are removed.

    If protect_titles is True, the title field is transformed to use
    double braces (preserving case) with inner braces removed.

    If exclude_issn is True, the ISSN field is removed from the output.

    If exclude_doi is True, the DOI field is removed from the output.

    Commas inside braced values (e.g. author names) are preserved — only
    top-level commas are treated as field separators.
    """
    header, fields_block = _split_header(raw.strip())
    fields = _parse_fields(fields_block)

    if protect_titles:
        fields = [
            (k, _protect_title(v) if k.lower() == "title" else v) for k, v in fields
        ]

    if exclude_issn:
        fields = [(k, v) for k, v in fields if k.lower() != "issn"]

    if exclude_doi:
        fields = [(k, v) for k, v in fields if k.lower() != "doi"]

    fields.sort(key=lambda kv: kv[0].lower())

    field_lines = [f"  {key} = {value}" for key, value in fields]
    return header + "\n" + ",\n".join(field_lines) + "\n}"


def _protect_title(value: str) -> str:
    """Transform a braced title value to use double braces.

    Removes inner braces and wraps the content in double braces.
    Example: {This is {THE} title} -> {{This is THE title}}
    """
    # Strip outer braces if present
    stripped = value.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        inner = stripped[1:-1]
    else:
        inner = stripped

    # Remove all inner braces
    content = inner.replace("{", "").replace("}", "")

    return "{{" + content + "}}"


def _split_header(entry: str) -> tuple[str, str]:
    """Split a BibTeX entry into header and fields block.

    The header is everything up to and including the first top-level comma
    after the citation key (e.g. '@article{Key2020,').
    The fields block is the rest, minus the final closing '}'.
    """
    # Find the first comma that is not inside braces — this ends the key.
    depth = 0
    for i, ch in enumerate(entry):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == "," and depth == 1:
            header = entry[: i + 1]
            rest = entry[i + 1 :]
            # Strip the outermost closing brace from the rest
            rest = rest.strip()
            if rest.endswith("}"):
                rest = rest[:-1].strip()
            return header, rest
    # Fallback: no fields found
    return entry, ""


def _parse_fields(block: str) -> list[tuple[str, str]]:
    """Parse a block of BibTeX fields into (key, value) pairs.

    Splits on top-level commas only (not commas inside braces).
    """
    if not block.strip():
        return []

    fields = []
    for raw_field in _split_top_level(block, ","):
        raw_field = raw_field.strip()
        if not raw_field:
            continue
        # Split on the first '=' to get key and value
        eq_pos = raw_field.find("=")
        if eq_pos == -1:
            continue
        key = raw_field[:eq_pos].strip()
        value = raw_field[eq_pos + 1 :].strip()
        fields.append((key, value))
    return fields


def _split_top_level(text: str, delimiter: str) -> list[str]:
    """Split text on a delimiter, but only at brace depth 0."""
    parts = []
    depth = 0
    current: list[str] = []

    for ch in text:
        if ch == "{":
            depth += 1
            current.append(ch)
        elif ch == "}":
            depth -= 1
            current.append(ch)
        elif ch == delimiter and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)

    # Append whatever is left
    trailing = "".join(current).strip()
    if trailing:
        parts.append(trailing)

    return parts
