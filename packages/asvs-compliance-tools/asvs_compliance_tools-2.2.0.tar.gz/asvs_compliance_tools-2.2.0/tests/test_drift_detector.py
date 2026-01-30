#!/usr/bin/env python3
"""
Unit tests for the ASVS Drift Detector tool.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.drift_detector import (
    Requirement,
    DriftResult,
    RequirementParser,
    DriftDetector,
    DefaultFileReader,
    DefaultUrlFetcher,
    TextFormatter,
    JsonFormatter,
    create_parser,
    main,
    UPSTREAM_ASVS_URL,
    DEFAULT_LOCAL_PATH,
)


# --- Fixtures ---

@pytest.fixture
def sample_local_json():
    """Sample local ASVS JSON format."""
    return json.dumps([
        {
            "chapter_id": "V1",
            "chapter_name": "Encoding",
            "section_id": "V1.2",
            "section_name": "Injection",
            "req_id": "V1.2.1",
            "req_description": "Verify output encoding for HTTP response.",
            "L": "1"
        },
        {
            "chapter_id": "V1",
            "chapter_name": "Encoding",
            "section_id": "V1.2",
            "section_name": "Injection",
            "req_id": "V1.2.2",
            "req_description": "Verify URL encoding for dynamic URLs.",
            "L": "1"
        },
        {
            "chapter_id": "V2",
            "chapter_name": "Validation",
            "section_id": "V2.1",
            "section_name": "Input",
            "req_id": "V2.1.1",
            "req_description": "Verify input validation rules defined.",
            "L": "1"
        },
    ])


@pytest.fixture
def sample_upstream_json():
    """Sample upstream JSON with some drift."""
    return json.dumps([
        {
            "chapter_id": "V1",
            "chapter_name": "Encoding",
            "section_id": "V1.2",
            "section_name": "Injection",
            "req_id": "V1.2.1",
            "req_description": "Verify output encoding for HTTP response - UPDATED.",
            "L": "1"
        },
        {
            "chapter_id": "V1",
            "chapter_name": "Encoding",
            "section_id": "V1.2",
            "section_name": "Injection",
            "req_id": "V1.2.3",
            "req_description": "NEW requirement for JSON encoding.",
            "L": "1"
        },
        {
            "chapter_id": "V2",
            "chapter_name": "Validation",
            "section_id": "V2.1",
            "section_name": "Input",
            "req_id": "V2.1.1",
            "req_description": "Verify input validation rules defined.",
            "L": "1"
        },
    ])


@pytest.fixture
def parser():
    """Create a RequirementParser instance."""
    return RequirementParser()


@pytest.fixture
def mock_file_reader():
    """Create a mock file reader."""
    return Mock()


@pytest.fixture
def mock_url_fetcher():
    """Create a mock URL fetcher."""
    return Mock()


# --- Requirement Tests ---

class TestRequirement:
    """Tests for the Requirement data class."""

    def test_requirement_creation(self):
        """Test creating a requirement."""
        req = Requirement(
            req_id="V1.2.1",
            description="Test description",
            level="1",
            chapter_id="V1",
            chapter_name="Chapter",
            section_id="V1.2",
            section_name="Section",
        )
        assert req.req_id == "V1.2.1"
        assert req.description == "Test description"
        assert req.level == "1"

    def test_requirement_equality(self):
        """Test requirement equality based on req_id."""
        req1 = Requirement(req_id="V1.2.1", description="Desc 1", level="1")
        req2 = Requirement(req_id="V1.2.1", description="Desc 2", level="2")
        req3 = Requirement(req_id="V1.2.2", description="Desc 1", level="1")

        assert req1 == req2
        assert req1 != req3

    def test_requirement_hash(self):
        """Test requirement hashing."""
        req1 = Requirement(req_id="V1.2.1", description="Desc 1", level="1")
        req2 = Requirement(req_id="V1.2.1", description="Desc 2", level="2")

        assert hash(req1) == hash(req2)
        assert len({req1, req2}) == 1


# --- DriftResult Tests ---

class TestDriftResult:
    """Tests for the DriftResult data class."""

    def test_no_drift(self):
        """Test result with no drift."""
        result = DriftResult()
        assert not result.has_drift
        assert result.summary == "No drift detected"

    def test_has_drift_added(self):
        """Test result with added requirements."""
        result = DriftResult(
            added=[Requirement(req_id="V1.2.1", description="New", level="1")]
        )
        assert result.has_drift
        assert "1 added" in result.summary

    def test_has_drift_removed(self):
        """Test result with removed requirements."""
        result = DriftResult(
            removed=[Requirement(req_id="V1.2.1", description="Old", level="1")]
        )
        assert result.has_drift
        assert "1 removed" in result.summary

    def test_has_drift_modified(self):
        """Test result with modified requirements."""
        local = Requirement(req_id="V1.2.1", description="Old", level="1")
        upstream = Requirement(req_id="V1.2.1", description="New", level="1")
        result = DriftResult(modified=[(local, upstream)])
        assert result.has_drift
        assert "1 modified" in result.summary

    def test_summary_multiple_changes(self):
        """Test summary with multiple types of changes."""
        result = DriftResult(
            added=[Requirement(req_id="V1", description="A", level="1")],
            removed=[Requirement(req_id="V2", description="B", level="1")],
            modified=[
                (
                    Requirement(req_id="V3", description="C", level="1"),
                    Requirement(req_id="V3", description="D", level="1"),
                )
            ],
        )
        assert "1 added" in result.summary
        assert "1 removed" in result.summary
        assert "1 modified" in result.summary


# --- RequirementParser Tests ---

class TestRequirementParser:
    """Tests for the RequirementParser class."""

    def test_parse_flat_format(self, parser, sample_local_json):
        """Test parsing flat array format."""
        requirements = parser.parse(sample_local_json)
        assert len(requirements) == 3
        assert requirements[0].req_id == "V1.2.1"
        assert requirements[0].description == "Verify output encoding for HTTP response."
        assert requirements[0].level == "1"

    def test_parse_empty_array(self, parser):
        """Test parsing empty array."""
        requirements = parser.parse("[]")
        assert len(requirements) == 0

    def test_parse_invalid_json(self, parser):
        """Test parsing invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            parser.parse("not valid json")

    def test_parse_unexpected_type(self, parser):
        """Test parsing unexpected JSON type."""
        with pytest.raises(ValueError, match="Unexpected JSON structure"):
            parser.parse('"just a string"')

    def test_parse_skips_invalid_items(self, parser):
        """Test that parser skips items without req_id."""
        content = json.dumps([
            {"req_id": "V1.2.1", "req_description": "Valid", "L": "1"},
            {"description": "No ID", "L": "1"},
            {"req_id": "", "req_description": "Empty ID", "L": "1"},
        ])
        requirements = parser.parse(content)
        assert len(requirements) == 1
        assert requirements[0].req_id == "V1.2.1"

    def test_parse_alternative_field_names(self, parser):
        """Test parsing with alternative field names (Shortcode, Description)."""
        content = json.dumps([
            {"Shortcode": "V1.2.1", "Description": "Test desc", "Level": "1"},
        ])
        requirements = parser.parse(content)
        assert len(requirements) == 1
        assert requirements[0].req_id == "V1.2.1"
        assert requirements[0].description == "Test desc"


# --- DriftDetector Tests ---

class TestDriftDetector:
    """Tests for the DriftDetector class."""

    def test_compute_hash(self, mock_file_reader, mock_url_fetcher, parser):
        """Test hash computation."""
        detector = DriftDetector(mock_file_reader, mock_url_fetcher, parser)
        hash1 = detector.compute_hash("test content")
        hash2 = detector.compute_hash("test content")
        hash3 = detector.compute_hash("different content")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16

    def test_load_local(self, mock_file_reader, mock_url_fetcher, parser, sample_local_json):
        """Test loading local file."""
        mock_file_reader.read.return_value = sample_local_json
        detector = DriftDetector(mock_file_reader, mock_url_fetcher, parser)

        requirements, content_hash = detector.load_local(Path("test.json"))

        assert len(requirements) == 3
        assert len(content_hash) == 16
        mock_file_reader.read.assert_called_once()

    def test_fetch_upstream(self, mock_file_reader, mock_url_fetcher, parser, sample_upstream_json):
        """Test fetching upstream."""
        mock_url_fetcher.fetch.return_value = sample_upstream_json
        detector = DriftDetector(mock_file_reader, mock_url_fetcher, parser)

        requirements, content_hash = detector.fetch_upstream("http://test.url")

        assert len(requirements) == 3
        mock_url_fetcher.fetch.assert_called_once_with("http://test.url")

    def test_compare_no_drift(self, mock_file_reader, mock_url_fetcher, parser):
        """Test comparison with no drift."""
        detector = DriftDetector(mock_file_reader, mock_url_fetcher, parser)

        local = [
            Requirement(req_id="V1.2.1", description="Desc", level="1"),
            Requirement(req_id="V1.2.2", description="Desc2", level="1"),
        ]
        upstream = [
            Requirement(req_id="V1.2.1", description="Desc", level="1"),
            Requirement(req_id="V1.2.2", description="Desc2", level="1"),
        ]

        result = detector.compare(local, upstream)

        assert not result.has_drift
        assert len(result.added) == 0
        assert len(result.removed) == 0
        assert len(result.modified) == 0

    def test_compare_added_requirements(self, mock_file_reader, mock_url_fetcher, parser):
        """Test detecting added requirements."""
        detector = DriftDetector(mock_file_reader, mock_url_fetcher, parser)

        local = [Requirement(req_id="V1.2.1", description="Desc", level="1")]
        upstream = [
            Requirement(req_id="V1.2.1", description="Desc", level="1"),
            Requirement(req_id="V1.2.2", description="New", level="1"),
        ]

        result = detector.compare(local, upstream)

        assert result.has_drift
        assert len(result.added) == 1
        assert result.added[0].req_id == "V1.2.2"

    def test_compare_removed_requirements(self, mock_file_reader, mock_url_fetcher, parser):
        """Test detecting removed requirements."""
        detector = DriftDetector(mock_file_reader, mock_url_fetcher, parser)

        local = [
            Requirement(req_id="V1.2.1", description="Desc", level="1"),
            Requirement(req_id="V1.2.2", description="Old", level="1"),
        ]
        upstream = [Requirement(req_id="V1.2.1", description="Desc", level="1")]

        result = detector.compare(local, upstream)

        assert result.has_drift
        assert len(result.removed) == 1
        assert result.removed[0].req_id == "V1.2.2"

    def test_compare_modified_requirements(self, mock_file_reader, mock_url_fetcher, parser):
        """Test detecting modified requirements."""
        detector = DriftDetector(mock_file_reader, mock_url_fetcher, parser)

        local = [Requirement(req_id="V1.2.1", description="Old desc", level="1")]
        upstream = [Requirement(req_id="V1.2.1", description="New desc", level="1")]

        result = detector.compare(local, upstream)

        assert result.has_drift
        assert len(result.modified) == 1
        assert result.modified[0][0].description == "Old desc"
        assert result.modified[0][1].description == "New desc"

    def test_compare_level_change(self, mock_file_reader, mock_url_fetcher, parser):
        """Test detecting level changes."""
        detector = DriftDetector(mock_file_reader, mock_url_fetcher, parser)

        local = [Requirement(req_id="V1.2.1", description="Desc", level="1")]
        upstream = [Requirement(req_id="V1.2.1", description="Desc", level="2")]

        result = detector.compare(local, upstream)

        assert result.has_drift
        assert len(result.modified) == 1

    def test_detect_with_upstream_content(
        self, mock_file_reader, mock_url_fetcher, parser, sample_local_json, sample_upstream_json
    ):
        """Test detect with provided upstream content."""
        mock_file_reader.read.return_value = sample_local_json
        detector = DriftDetector(mock_file_reader, mock_url_fetcher, parser)

        result = detector.detect(
            Path("local.json"),
            upstream_content=sample_upstream_json,
        )

        assert result.has_drift
        assert len(result.added) == 1
        assert len(result.removed) == 1
        assert len(result.modified) == 1
        mock_url_fetcher.fetch.assert_not_called()


# --- Formatter Tests ---

class TestTextFormatter:
    """Tests for the TextFormatter class."""

    def test_format_no_drift(self):
        """Test formatting result with no drift."""
        formatter = TextFormatter()
        result = DriftResult(local_count=10, upstream_count=10, local_hash="abc", upstream_hash="abc")

        output = formatter.format(result)

        assert "No drift detected" in output
        assert "IN SYNC" in output
        assert "10" in output

    def test_format_with_drift(self):
        """Test formatting result with drift."""
        formatter = TextFormatter()
        result = DriftResult(
            added=[Requirement(req_id="V1.2.1", description="Added req", level="1")],
            removed=[Requirement(req_id="V1.2.2", description="Removed req", level="1")],
            modified=[
                (
                    Requirement(req_id="V1.2.3", description="Old", level="1"),
                    Requirement(req_id="V1.2.3", description="New", level="1"),
                )
            ],
            local_hash="abc",
            upstream_hash="def",
        )

        output = formatter.format(result)

        assert "DRIFT DETECTED" in output
        assert "ADDED" in output
        assert "REMOVED" in output
        assert "MODIFIED" in output
        assert "V1.2.1" in output
        assert "V1.2.2" in output
        assert "V1.2.3" in output


class TestJsonFormatter:
    """Tests for the JsonFormatter class."""

    def test_format_no_drift(self):
        """Test JSON formatting with no drift."""
        formatter = JsonFormatter()
        result = DriftResult(local_count=10, upstream_count=10, local_hash="abc", upstream_hash="abc")

        output = formatter.format(result)
        data = json.loads(output)

        assert data["status"] == "in_sync"
        assert data["local"]["count"] == 10
        assert len(data["added"]) == 0

    def test_format_with_drift(self):
        """Test JSON formatting with drift."""
        formatter = JsonFormatter()
        result = DriftResult(
            added=[Requirement(req_id="V1.2.1", description="Added", level="1")],
            local_hash="abc",
            upstream_hash="def",
        )

        output = formatter.format(result)
        data = json.loads(output)

        assert data["status"] == "drift"
        assert len(data["added"]) == 1
        assert data["added"][0]["id"] == "V1.2.1"


# --- CLI Tests ---

class TestCLI:
    """Tests for the CLI interface."""

    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert parser is not None

    def test_parse_defaults(self):
        """Test default argument values."""
        parser = create_parser()
        args = parser.parse_args([])

        assert args.local is None
        assert args.format == "text"
        assert args.upstream_url == UPSTREAM_ASVS_URL
        assert args.offline is False

    def test_parse_custom_args(self):
        """Test custom argument parsing."""
        parser = create_parser()
        args = parser.parse_args([
            "--local", "custom.json",
            "--format", "json",
            "--offline",
        ])

        assert args.local == Path("custom.json")
        assert args.format == "json"
        assert args.offline is True

    def test_main_file_not_found(self, tmp_path):
        """Test main with non-existent file."""
        result = main(["--local", str(tmp_path / "nonexistent.json")])
        assert result == 1

    def test_main_offline_mode(self, tmp_path, sample_local_json):
        """Test main in offline mode."""
        local_file = tmp_path / "local.json"
        local_file.write_text(sample_local_json)

        result = main(["--local", str(local_file), "--offline"])
        assert result == 0

    def test_main_with_upstream_file(self, tmp_path, sample_local_json, sample_upstream_json):
        """Test main with local upstream file."""
        local_file = tmp_path / "local.json"
        local_file.write_text(sample_local_json)

        upstream_file = tmp_path / "upstream.json"
        upstream_file.write_text(sample_upstream_json)

        result = main([
            "--local", str(local_file),
            "--upstream-file", str(upstream_file),
        ])
        assert result == 1

    def test_main_json_output(self, tmp_path, sample_local_json, capsys):
        """Test main with JSON output format."""
        local_file = tmp_path / "local.json"
        local_file.write_text(sample_local_json)

        result = main(["--local", str(local_file), "--offline", "--format", "json"])

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "status" in data
        assert result == 0

    def test_main_help(self, capsys):
        """Test main with --help."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0


# --- DefaultUrlFetcher Tests ---

class TestDefaultUrlFetcher:
    """Tests for the DefaultUrlFetcher class."""

    def test_fetch_connection_error(self):
        """Test fetch with invalid URL."""
        fetcher = DefaultUrlFetcher(timeout=1)
        with pytest.raises(ConnectionError):
            fetcher.fetch("http://invalid.nonexistent.url.test/asvs.json")


# --- DefaultFileReader Tests ---

class TestDefaultFileReader:
    """Tests for the DefaultFileReader class."""

    def test_read_file(self, tmp_path):
        """Test reading a file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")

        reader = DefaultFileReader()
        content = reader.read(test_file)

        assert content == "test content"

    def test_read_nonexistent_file(self, tmp_path):
        """Test reading non-existent file."""
        reader = DefaultFileReader()
        with pytest.raises(FileNotFoundError):
            reader.read(tmp_path / "nonexistent.txt")


# --- Integration Tests ---

class TestIntegration:
    """Integration tests for the drift detector."""

    def test_full_workflow_no_drift(self, tmp_path):
        """Test full workflow with identical files."""
        content = json.dumps([
            {"req_id": "V1.2.1", "req_description": "Test", "L": "1"},
        ])

        local_file = tmp_path / "local.json"
        local_file.write_text(content)

        upstream_file = tmp_path / "upstream.json"
        upstream_file.write_text(content)

        result = main([
            "--local", str(local_file),
            "--upstream-file", str(upstream_file),
            "--format", "text",
        ])

        assert result == 0

    def test_full_workflow_with_drift(self, tmp_path):
        """Test full workflow with drift detected."""
        local_content = json.dumps([
            {"req_id": "V1.2.1", "req_description": "Old", "L": "1"},
        ])
        upstream_content = json.dumps([
            {"req_id": "V1.2.1", "req_description": "New", "L": "1"},
        ])

        local_file = tmp_path / "local.json"
        local_file.write_text(local_content)

        upstream_file = tmp_path / "upstream.json"
        upstream_file.write_text(upstream_content)

        result = main([
            "--local", str(local_file),
            "--upstream-file", str(upstream_file),
        ])

        assert result == 1
