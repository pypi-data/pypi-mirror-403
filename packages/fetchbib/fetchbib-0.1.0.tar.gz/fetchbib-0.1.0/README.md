# fetchbib

A command-line tool to resolve DOIs and free-text search queries into formatted BibTeX entries.
Powered by [doi.org](https://www.doi.org/) and the [Crossref API](https://api.crossref.org/).

## Installation

```bash
pip install fetchbib
```

Requires Python 3.9+.

## Quick start

Fetch BibTeX by DOI (bare or full URL):

```bash
fbib 10.2196/jmir.1933
fbib https://doi.org/10.2196/jmir.1933
```

```bibtex
@article{Eysenbach2011,
  author = {Eysenbach, Gunther},
  doi = {10.2196/jmir.1933},
  journal = {Journal of Medical Internet Research},
  title = {Can Tweets Predict Citations? Metrics of Social Impact Based on Twitter and Correlation with Traditional Metrics of Scientific Impact},
  year = {2011}
}
```

Search by free text:

```bash
fbib "Eysenbach JMIR 2011"
```

## Usage

```
fbib [-h] [-f FILE] [-o OUTPUT] [-a] [-v] [--config-email EMAIL]
     [inputs ...]
```

### Flexible input

`fbib` accepts DOIs in any format — bare, full URL, or free-text search queries — and you can mix them freely.
Inputs are comma-separated, so all of the following work:

```bash
# Multiple positional arguments
fbib 10.2196/jmir.1933 10.1038/nature12373

# Comma-separated string
fbib "10.2196/jmir.1933, 10.1038/nature12373"

# Full DOI URLs
fbib "https://doi.org/10.2196/jmir.1933, https://doi.org/10.1038/nature12373"

# Mix DOIs, URLs, and search queries
fbib 10.2196/jmir.1933 "Eysenbach JMIR 2011"
```

From a file (`--file`), each line is treated the same way — one entry per line, or comma-separated on a single line:

```bash
fbib --file dois.txt
```

Duplicate inputs are automatically removed.

### Write to a file

Overwrite (default):

```bash
fbib --output refs.bib 10.2196/jmir.1933
```

Append to an existing `.bib` file:

```bash
fbib --append --output refs.bib 10.1038/nature12373
```

### Verbose mode

See which DOI was matched when searching by free text:

```bash
fbib -v "Eysenbach JMIR 2011"
# stderr: Searching for: "Eysenbach JMIR 2011" -> DOI: 10.2196/jmir.1933
```

### Configure email

Crossref gives better rate limits to requests that include a contact email. Set yours once and it will be used for all future requests:

```bash
fbib --config-email you@example.com
```

The email is stored in `~/.config/fetchbib/config.json`. If not set, a default placeholder is used.

## Development

Clone the repo and sync dependencies with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/mr-devs/fetchbib.git
cd fetchbib
uv sync
```

Run unit tests:

```bash
uv run pytest
```

Run integration tests (hits live APIs):

```bash
uv run pytest -m integration
```

## License

MIT
