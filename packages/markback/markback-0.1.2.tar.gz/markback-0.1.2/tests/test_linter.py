"""Tests for MarkBack linter."""

import pytest
from pathlib import Path

from markback import (
    lint_file,
    lint_string,
    lint_files,
    format_diagnostics,
    summarize_results,
    ErrorCode,
    WarningCode,
    Severity,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"
ERRORS_DIR = FIXTURES_DIR / "errors"


class TestLintString:
    """Tests for lint_string function."""

    def test_valid_minimal(self):
        """Test linting a valid minimal record."""
        text = "Content here.\n<<< positive\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert not result.has_errors

    def test_valid_with_uri(self):
        """Test linting a valid record with URI."""
        text = "@uri local:example\n\nContent.\n<<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert not result.has_errors

    def test_missing_feedback_error(self):
        """Test E001: Missing feedback."""
        text = "@uri local:example\n\nContent without feedback.\n"
        result = lint_string(text)

        assert result.has_errors
        errors = [d for d in result.diagnostics if d.code == ErrorCode.E001]
        assert len(errors) == 1

    def test_empty_feedback_error(self):
        """Test E009: Empty feedback."""
        text = "Content.\n<<<\n"
        result = lint_string(text)

        assert result.has_errors
        errors = [d for d in result.diagnostics if d.code == ErrorCode.E009]
        assert len(errors) == 1

    def test_malformed_uri_error(self):
        """Test E003: Malformed URI."""
        text = "@uri invalid\n\nContent.\n<<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert result.has_errors
        errors = [d for d in result.diagnostics if d.code == ErrorCode.E003]
        assert len(errors) == 1

    def test_invalid_json_error(self):
        """Test E007: Invalid JSON."""
        text = "Content.\n<<< json:{invalid json}\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert result.has_errors
        errors = [d for d in result.diagnostics if d.code == ErrorCode.E007]
        assert len(errors) == 1

    def test_valid_json(self):
        """Test valid JSON feedback."""
        text = 'Content.\n<<< json:{"key":"value"}\n'
        result = lint_string(text, check_sources=False, check_canonical=False)

        json_errors = [d for d in result.diagnostics if d.code == ErrorCode.E007]
        assert len(json_errors) == 0

    def test_unclosed_quote_error(self):
        """Test E008: Unclosed quote."""
        text = 'Content.\n<<< note="unclosed\n'
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert result.has_errors
        errors = [d for d in result.diagnostics if d.code == ErrorCode.E008]
        assert len(errors) == 1

    def test_duplicate_uri_warning(self):
        """Test W001: Duplicate URI."""
        text = """@uri local:same

Content 1.
<<< good

---
@uri local:same

Content 2.
<<< bad
"""
        result = lint_string(text, check_sources=False, check_canonical=False)

        warnings = [d for d in result.diagnostics if d.code == WarningCode.W001]
        assert len(warnings) == 1

    def test_missing_uri_warning(self):
        """Test W006: Missing URI."""
        text = "Content without URI.\n<<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        warnings = [d for d in result.diagnostics if d.code == WarningCode.W006]
        assert len(warnings) == 1

    def test_unknown_header_warning(self):
        """Test W002: Unknown header."""
        text = "@uri local:example\n@custom value\n\nContent.\n<<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        warnings = [d for d in result.diagnostics if d.code == WarningCode.W002]
        assert len(warnings) == 1

    def test_prior_file_not_found_warning(self):
        """Test W009: @prior file not found."""
        text = "@uri local:example\n@prior ./nonexistent_prior.txt\n@source ./nonexistent.txt\n<<< good\n"
        result = lint_string(text, check_sources=True, check_canonical=False)

        # Should have W009 for @prior and W003 for @source
        prior_warnings = [d for d in result.diagnostics if d.code == WarningCode.W009]
        assert len(prior_warnings) == 1
        assert "@prior file not found" in prior_warnings[0].message

    def test_prior_uri_not_checked(self):
        """Test that @prior URIs are not checked for file existence."""
        text = "@uri local:example\n@prior https://example.com/prior.txt\n\nContent.\n<<< good\n"
        result = lint_string(text, check_sources=True, check_canonical=False)

        # Should not have W009 for URI-based @prior
        prior_warnings = [d for d in result.diagnostics if d.code == WarningCode.W009]
        assert len(prior_warnings) == 0


class TestLintFile:
    """Tests for lint_file function."""

    def test_lint_minimal(self):
        """Test linting minimal.mb fixture."""
        result = lint_file(FIXTURES_DIR / "minimal.mb", check_sources=False)

        # Should have W006 (missing URI) but no errors
        assert not result.has_errors

    def test_lint_with_uri(self):
        """Test linting with_uri.mb fixture."""
        result = lint_file(FIXTURES_DIR / "with_uri.mb", check_sources=False)

        assert not result.has_errors

    def test_lint_multi_record(self):
        """Test linting multi_record.mb fixture."""
        result = lint_file(FIXTURES_DIR / "multi_record.mb", check_sources=False)

        assert not result.has_errors

    def test_lint_missing_feedback_error(self):
        """Test linting file with missing feedback."""
        result = lint_file(ERRORS_DIR / "missing_feedback.mb")

        assert result.has_errors
        errors = [d for d in result.diagnostics if d.code == ErrorCode.E001]
        assert len(errors) == 1

    def test_lint_empty_feedback_error(self):
        """Test linting file with empty feedback."""
        result = lint_file(ERRORS_DIR / "empty_feedback.mb")

        assert result.has_errors
        errors = [d for d in result.diagnostics if d.code == ErrorCode.E009]
        assert len(errors) == 1

    def test_lint_malformed_uri_error(self):
        """Test linting file with malformed URI."""
        result = lint_file(ERRORS_DIR / "malformed_uri.mb", check_sources=False)

        assert result.has_errors
        errors = [d for d in result.diagnostics if d.code == ErrorCode.E003]
        assert len(errors) == 1


class TestLintFiles:
    """Tests for lint_files function."""

    def test_lint_directory(self):
        """Test linting a directory of files."""
        results = lint_files([FIXTURES_DIR], check_sources=False)

        assert len(results) > 0

    def test_lint_multiple_files(self):
        """Test linting multiple specific files."""
        files = [
            FIXTURES_DIR / "minimal.mb",
            FIXTURES_DIR / "with_uri.mb",
        ]
        results = lint_files(files, check_sources=False)

        assert len(results) == 2


class TestFormatDiagnostics:
    """Tests for format_diagnostics function."""

    def test_human_format(self):
        """Test human-readable format."""
        text = "@uri invalid\n\nContent.\n<<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        output = format_diagnostics(result.diagnostics, format="human")
        assert "E003" in output

    def test_json_format(self):
        """Test JSON format."""
        import json

        text = "@uri invalid\n\nContent.\n<<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        output = format_diagnostics(result.diagnostics, format="json")
        data = json.loads(output)
        assert isinstance(data, list)


class TestSummarizeResults:
    """Tests for summarize_results function."""

    def test_summary(self):
        """Test result summarization."""
        results = lint_files([FIXTURES_DIR / "minimal.mb"], check_sources=False)
        summary = summarize_results(results)

        assert "files" in summary
        assert "records" in summary
        assert "errors" in summary
        assert "warnings" in summary


class TestLineRangeSupport:
    """Tests for line range support in @source and @prior."""

    def test_source_with_single_line(self):
        """Test @source with single line reference."""
        text = "@source ./code.py:42 <<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert not result.has_errors
        assert result.records[0].source is not None
        assert result.records[0].source.path == "./code.py"
        assert result.records[0].source.start_line == 42
        assert result.records[0].source.end_line == 42

    def test_source_with_line_range(self):
        """Test @source with line range reference."""
        text = "@source ./code.py:10-20 <<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert not result.has_errors
        assert result.records[0].source is not None
        assert result.records[0].source.path == "./code.py"
        assert result.records[0].source.start_line == 10
        assert result.records[0].source.end_line == 20

    def test_prior_with_line_range(self):
        """Test @prior with line range reference."""
        text = "@prior ./prompts/template.txt:1-20\n@source ./output.txt\n<<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert not result.has_errors
        assert result.records[0].prior is not None
        assert result.records[0].prior.path == "./prompts/template.txt"
        assert result.records[0].prior.start_line == 1
        assert result.records[0].prior.end_line == 20

    def test_compact_record_with_line_range(self):
        """Test compact record with line range in @source."""
        text = "@uri local:item-001\n@source ./file.txt:100-150 <<< feedback\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert not result.has_errors
        assert result.records[0].source is not None
        assert result.records[0].source.path == "./file.txt"
        assert result.records[0].source.start_line == 100
        assert result.records[0].source.end_line == 150

    def test_uri_with_line_range(self):
        """Test URI source with line range."""
        text = "@source https://example.com/file.txt:100-150 <<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert not result.has_errors
        assert result.records[0].source is not None
        assert result.records[0].source.path == "https://example.com/file.txt"
        assert result.records[0].source.start_line == 100
        assert result.records[0].source.end_line == 150
        assert result.records[0].source.is_uri

    def test_invalid_line_range_end_less_than_start(self):
        """Test E011: Invalid line range (end < start)."""
        text = "@source ./code.py:50-10 <<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert result.has_errors
        errors = [d for d in result.diagnostics if d.code == ErrorCode.E011]
        assert len(errors) == 1
        assert "end line 10 is less than start line 50" in errors[0].message

    def test_source_without_line_range(self):
        """Test @source without line range still works."""
        text = "@source ./code.py <<< good\n"
        result = lint_string(text, check_sources=False, check_canonical=False)

        assert not result.has_errors
        assert result.records[0].source is not None
        assert result.records[0].source.path == "./code.py"
        assert result.records[0].source.start_line is None
        assert result.records[0].source.end_line is None
