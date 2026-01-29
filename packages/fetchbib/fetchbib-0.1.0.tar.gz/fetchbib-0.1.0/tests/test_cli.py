"""Tests for the CLI (Phase 3).

All resolver calls are mocked — no network access needed.
"""

import json
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from fetchbib.resolver import ResolverError

# Sample raw BibTeX that the mock resolver returns (unformatted).
RAW_BIBTEX_A = "@article{Key1,author={Alice},year={2020}}"
RAW_BIBTEX_B = "@article{Key2,author={Bob},year={2021}}"


def run_cli(args: list[str]) -> tuple[int, str, str]:
    """Run the CLI main() with the given args, returning (exit_code, stdout, stderr)."""
    from fetchbib.cli import main

    old_argv = sys.argv
    sys.argv = ["fbib"] + args

    stdout_capture = StringIO()
    stderr_capture = StringIO()

    exit_code = 0
    try:
        with patch("sys.stdout", stdout_capture), patch("sys.stderr", stderr_capture):
            main()
    except SystemExit as e:
        exit_code = e.code if e.code is not None else 0
    finally:
        sys.argv = old_argv

    return exit_code, stdout_capture.getvalue(), stderr_capture.getvalue()


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------


class TestInputParsing:
    """Tests for how the CLI collects and processes inputs."""

    @patch("fetchbib.cli.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_single_positional_doi(self, mock_resolve):
        code, stdout, _ = run_cli(["10.2196/jmir.1933"])

        mock_resolve.assert_called_once_with("10.2196/jmir.1933")
        assert "@article{Key1," in stdout
        assert code == 0

    @patch("fetchbib.cli.resolve_doi", side_effect=[RAW_BIBTEX_A, RAW_BIBTEX_B])
    def test_multiple_positional_arguments(self, mock_resolve):
        code, stdout, _ = run_cli(["10.2196/jmir.1933", "10.1000/xyz123"])

        assert mock_resolve.call_count == 2
        assert "Key1" in stdout
        assert "Key2" in stdout
        assert code == 0

    @patch("fetchbib.cli.resolve_doi", side_effect=[RAW_BIBTEX_A, RAW_BIBTEX_B])
    def test_comma_separated_string_is_split(self, mock_resolve):
        code, stdout, _ = run_cli(["10.2196/jmir.1933, 10.1000/xyz123"])

        assert mock_resolve.call_count == 2
        calls = [c.args[0] for c in mock_resolve.call_args_list]
        assert "10.2196/jmir.1933" in calls
        assert "10.1000/xyz123" in calls
        assert code == 0

    @patch("fetchbib.cli.resolve_doi", side_effect=[RAW_BIBTEX_A, RAW_BIBTEX_B])
    def test_file_input_reads_lines(self, mock_resolve):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("10.2196/jmir.1933\n\n10.1000/xyz123\n")
            f.flush()
            code, stdout, _ = run_cli(["--file", f.name])

        assert mock_resolve.call_count == 2
        assert code == 0

    @patch("fetchbib.cli.resolve_doi", side_effect=[RAW_BIBTEX_A, RAW_BIBTEX_B])
    def test_file_input_splits_comma_separated_line(self, mock_resolve):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("10.2196/jmir.1933, 10.1000/xyz123\n")
            f.flush()
            code, stdout, _ = run_cli(["--file", f.name])

        assert mock_resolve.call_count == 2
        calls = [c.args[0] for c in mock_resolve.call_args_list]
        assert "10.2196/jmir.1933" in calls
        assert "10.1000/xyz123" in calls
        assert code == 0

    @patch("fetchbib.cli.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_doi_url_is_normalized(self, mock_resolve):
        code, stdout, _ = run_cli(["https://doi.org/10.2196/jmir.1933"])

        mock_resolve.assert_called_once_with("10.2196/jmir.1933")
        assert "@article{Key1," in stdout
        assert code == 0

    @patch("fetchbib.cli.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_duplicate_inputs_are_deduplicated(self, mock_resolve):
        code, _, _ = run_cli(["10.2196/jmir.1933", "10.2196/jmir.1933"])

        mock_resolve.assert_called_once()
        assert code == 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for error conditions and exit codes."""

    def test_nonexistent_file_exits_1(self):
        code, _, stderr = run_cli(["--file", "nonexistent_file.txt"])

        assert code == 1
        assert "nonexistent_file.txt" in stderr

    @patch("fetchbib.cli.resolve_doi")
    def test_resolution_error_does_not_stop_others(self, mock_resolve):
        mock_resolve.side_effect = [
            ResolverError("fail"),
            RAW_BIBTEX_B,
        ]

        code, stdout, stderr = run_cli(["10.1234/bad", "10.1234/good"])

        assert "Key2" in stdout
        assert "fail" in stderr
        assert code == 1

    def test_no_inputs_exits_1(self):
        code, _, stderr = run_cli([])

        assert code == 1
        assert stderr  # should contain some usage hint


# ---------------------------------------------------------------------------
# Verbose mode
# ---------------------------------------------------------------------------


class TestVerbose:
    """Tests for the --verbose flag."""

    @patch("fetchbib.cli.resolve_doi", return_value=RAW_BIBTEX_A)
    @patch("fetchbib.cli.search_crossref", return_value="10.2196/jmir.1933")
    def test_verbose_prints_search_mapping(self, mock_search, mock_resolve):
        code, _, stderr = run_cli(["-v", "Eysenbach JMIR 2011"])

        assert "Eysenbach JMIR 2011" in stderr
        assert "10.2196/jmir.1933" in stderr
        assert code == 0


# ---------------------------------------------------------------------------
# Output file
# ---------------------------------------------------------------------------


class TestOutputFile:
    """Tests for --output and --append flags."""

    @patch("fetchbib.cli.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_output_writes_to_file(self, mock_resolve):
        with tempfile.NamedTemporaryFile(suffix=".bib", delete=False) as f:
            path = f.name

        code, stdout, _ = run_cli(["--output", path, "10.1234/test"])

        assert code == 0
        assert stdout == ""  # nothing to stdout
        content = Path(path).read_text()
        assert "Key1" in content

    @patch("fetchbib.cli.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_output_overwrites_by_default(self, mock_resolve):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write("OLD CONTENT\n")
            path = f.name

        run_cli(["--output", path, "10.1234/test"])

        content = Path(path).read_text()
        assert "OLD CONTENT" not in content
        assert "Key1" in content

    @patch("fetchbib.cli.resolve_doi", return_value=RAW_BIBTEX_B)
    def test_append_flag_preserves_existing(self, mock_resolve):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write("EXISTING ENTRY\n\n")
            path = f.name

        code, stdout, _ = run_cli(["--append", "--output", path, "10.1234/test"])

        assert code == 0
        assert stdout == ""
        content = Path(path).read_text()
        assert "EXISTING ENTRY" in content
        assert "Key2" in content


# ---------------------------------------------------------------------------
# Config email
# ---------------------------------------------------------------------------


class TestConfigEmail:
    """Tests for --config-email."""

    def test_config_email_saves_and_exits(self, tmp_path):
        config_file = tmp_path / "config.json"
        with (
            patch("fetchbib.config.CONFIG_FILE", config_file),
            patch("fetchbib.config.CONFIG_DIR", tmp_path),
        ):
            code, _, _ = run_cli(["--config-email", "user@university.edu"])

        assert code == 0
        saved = json.loads(config_file.read_text())
        assert saved["email"] == "user@university.edu"

    @patch("fetchbib.cli.resolve_doi", return_value=RAW_BIBTEX_A)
    def test_config_email_used_by_resolver(self, mock_resolve, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"email": "custom@uni.edu"}))

        with (
            patch("fetchbib.config.CONFIG_FILE", config_file),
            patch("fetchbib.config.CONFIG_DIR", tmp_path),
        ):
            run_cli(["10.1234/test"])

        headers = mock_resolve.call_args  # we can't easily check headers here
        # Instead, verify the user agent function reads the config
        with (
            patch("fetchbib.config.CONFIG_FILE", config_file),
            patch("fetchbib.config.CONFIG_DIR", tmp_path),
        ):
            from fetchbib.resolver import get_user_agent

            ua = get_user_agent()
        assert "custom@uni.edu" in ua
