"""Unit tests for the export_requirements module."""

import csv
import hashlib
import io
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from tools.export_requirements import (
    CsvExporter,
    DefaultFileReader,
    IntegrityVerifier,
    JiraJsonExporter,
    Requirement,
    RequirementsLoader,
    create_parser,
    find_source_file,
    get_exporter,
    main,
)


class TestRequirement:
    """Tests for the Requirement dataclass."""

    def test_from_dict_valid(self):
        """Test creating a Requirement from valid data."""
        data = {
            "chapter_id": "V1",
            "chapter_name": "Encoding",
            "section_id": "V1.1",
            "section_name": "Architecture",
            "req_id": "V1.1.1",
            "req_description": "Test requirement",
            "L": "2",
        }
        req = Requirement.from_dict(data)
        
        assert req.chapter_id == "V1"
        assert req.chapter_name == "Encoding"
        assert req.section_id == "V1.1"
        assert req.section_name == "Architecture"
        assert req.req_id == "V1.1.1"
        assert req.req_description == "Test requirement"
        assert req.level == "2"

    def test_from_dict_missing_field(self):
        """Test that missing fields raise ValueError."""
        data = {
            "chapter_id": "V1",
            "chapter_name": "Encoding",
        }
        with pytest.raises(ValueError, match="Missing required field"):
            Requirement.from_dict(data)


class TestIntegrityVerifier:
    """Tests for the IntegrityVerifier class."""

    def test_compute_hash(self, sample_json_file):
        """Test computing SHA-256 hash of a file."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        
        content = sample_json_file.read_text(encoding="utf-8")
        expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        computed_hash = verifier.compute_hash(sample_json_file)
        assert computed_hash == expected_hash

    def test_verify_without_expected_hash(self, sample_json_file):
        """Test verification without expected hash always returns True."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        
        is_valid, computed = verifier.verify(sample_json_file, None)
        assert is_valid is True
        assert len(computed) == 64  # SHA-256 hex digest length

    def test_verify_with_correct_hash(self, sample_json_file):
        """Test verification with correct hash."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        
        content = sample_json_file.read_text(encoding="utf-8")
        expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        is_valid, computed = verifier.verify(sample_json_file, expected)
        assert is_valid is True
        assert computed == expected

    def test_verify_with_incorrect_hash(self, sample_json_file):
        """Test verification with incorrect hash fails."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        
        is_valid, computed = verifier.verify(sample_json_file, "invalid_hash")
        assert is_valid is False


class TestRequirementsLoader:
    """Tests for the RequirementsLoader class."""

    def test_load_valid_json(self, sample_json_file, sample_requirements_data):
        """Test loading valid JSON file."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        loader = RequirementsLoader(reader, verifier)
        
        requirements = loader.load(sample_json_file)
        
        assert len(requirements) == 3
        assert requirements[0].req_id == "V1.1.1"
        assert requirements[1].req_id == "V1.2.1"
        assert requirements[2].req_id == "V2.1.1"

    def test_load_with_hash_verification_pass(self, sample_json_file):
        """Test loading with correct hash verification."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        loader = RequirementsLoader(reader, verifier)
        
        content = sample_json_file.read_text(encoding="utf-8")
        expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        requirements = loader.load(sample_json_file, expected_hash)
        assert len(requirements) == 3

    def test_load_with_hash_verification_fail(self, sample_json_file):
        """Test loading with incorrect hash raises error."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        loader = RequirementsLoader(reader, verifier)
        
        with pytest.raises(ValueError, match="Integrity check failed"):
            loader.load(sample_json_file, "bad_hash")

    def test_load_invalid_json(self, invalid_json_file):
        """Test loading invalid JSON raises error."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        loader = RequirementsLoader(reader, verifier)
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            loader.load(invalid_json_file)

    def test_filter_by_level_1(self, sample_json_file):
        """Test filtering for L1 only includes L1 requirements."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        loader = RequirementsLoader(reader, verifier)
        
        requirements = loader.load(sample_json_file)
        filtered = loader.filter_by_level(requirements, "1")
        
        assert len(filtered) == 1
        assert filtered[0].level == "1"
        assert filtered[0].req_id == "V1.1.1"

    def test_filter_by_level_2(self, sample_json_file):
        """Test filtering for L2 includes L1 and L2 requirements."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        loader = RequirementsLoader(reader, verifier)
        
        requirements = loader.load(sample_json_file)
        filtered = loader.filter_by_level(requirements, "2")
        
        assert len(filtered) == 2
        levels = {req.level for req in filtered}
        assert levels == {"1", "2"}

    def test_filter_by_level_3(self, sample_json_file):
        """Test filtering for L3 includes all requirements."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        loader = RequirementsLoader(reader, verifier)
        
        requirements = loader.load(sample_json_file)
        filtered = loader.filter_by_level(requirements, "3")
        
        assert len(filtered) == 3

    def test_filter_invalid_level(self, sample_json_file):
        """Test filtering with invalid level raises error."""
        reader = DefaultFileReader()
        verifier = IntegrityVerifier(reader)
        loader = RequirementsLoader(reader, verifier)
        
        requirements = loader.load(sample_json_file)
        
        with pytest.raises(ValueError, match="Invalid level"):
            loader.filter_by_level(requirements, "4")


class TestCsvExporter:
    """Tests for the CsvExporter class."""

    def test_export_csv_headers(self, sample_requirements_data):
        """Test that CSV export includes correct headers."""
        requirements = [Requirement.from_dict(d) for d in sample_requirements_data]
        exporter = CsvExporter()
        
        output = exporter.export(requirements)
        reader = csv.reader(io.StringIO(output))
        headers = next(reader)
        
        expected = ["Issue Key", "Summary", "Description", "Labels", "Chapter", "Section"]
        assert headers == expected

    def test_export_csv_rows(self, sample_requirements_data):
        """Test that CSV export includes all requirements."""
        requirements = [Requirement.from_dict(d) for d in sample_requirements_data]
        exporter = CsvExporter()
        
        output = exporter.export(requirements)
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        
        assert len(rows) == 4  # 1 header + 3 data rows
        assert rows[1][0] == "V1.1.1"
        assert rows[2][0] == "V1.2.1"
        assert rows[3][0] == "V2.1.1"

    def test_export_csv_labels(self, sample_requirements_data):
        """Test that CSV export includes correct labels."""
        requirements = [Requirement.from_dict(d) for d in sample_requirements_data]
        exporter = CsvExporter()
        
        output = exporter.export(requirements)
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        
        assert "asvs,security,L1,V1" == rows[1][3]
        assert "asvs,security,L2,V1" == rows[2][3]
        assert "asvs,security,L3,V2" == rows[3][3]


class TestJiraJsonExporter:
    """Tests for the JiraJsonExporter class."""

    def test_export_jira_json_structure(self, sample_requirements_data):
        """Test that Jira JSON export has correct structure."""
        requirements = [Requirement.from_dict(d) for d in sample_requirements_data]
        exporter = JiraJsonExporter()
        
        output = exporter.export(requirements)
        data = json.loads(output)
        
        assert "issues" in data
        assert len(data["issues"]) == 3

    def test_export_jira_json_issue_fields(self, sample_requirements_data):
        """Test that Jira JSON issues have correct fields."""
        requirements = [Requirement.from_dict(d) for d in sample_requirements_data]
        exporter = JiraJsonExporter()
        
        output = exporter.export(requirements)
        data = json.loads(output)
        issue = data["issues"][0]
        
        assert "summary" in issue
        assert "description" in issue
        assert "labels" in issue
        assert "customFields" in issue
        assert "asvsId" in issue["customFields"]
        assert issue["customFields"]["asvsId"] == "V1.1.1"

    def test_export_jira_json_labels(self, sample_requirements_data):
        """Test that Jira JSON labels are correct."""
        requirements = [Requirement.from_dict(d) for d in sample_requirements_data]
        exporter = JiraJsonExporter()
        
        output = exporter.export(requirements)
        data = json.loads(output)
        issue = data["issues"][0]
        
        expected_labels = ["asvs", "security", "L1", "v1"]
        assert issue["labels"] == expected_labels


class TestGetExporter:
    """Tests for the get_exporter factory function."""

    def test_get_csv_exporter(self):
        """Test getting CSV exporter."""
        exporter = get_exporter("csv")
        assert isinstance(exporter, CsvExporter)

    def test_get_jira_json_exporter(self):
        """Test getting Jira JSON exporter."""
        exporter = get_exporter("jira-json")
        assert isinstance(exporter, JiraJsonExporter)

    def test_get_unknown_exporter(self):
        """Test getting unknown exporter raises error."""
        with pytest.raises(ValueError, match="Unknown format"):
            get_exporter("xml")


class TestFindSourceFile:
    """Tests for the find_source_file function."""

    def test_find_l1_source(self, project_root):
        """Test finding L1 source file."""
        path = find_source_file("1", project_root)
        assert path.name == "ASVS-L1-Baseline.json"
        assert path.exists()

    def test_find_l2_source(self, project_root):
        """Test finding L2 source file."""
        path = find_source_file("2", project_root)
        assert path.name == "ASVS-L2-Standard.json"
        assert path.exists()

    def test_find_l3_source(self, project_root):
        """Test finding L3 source file."""
        path = find_source_file("3", project_root)
        assert path.name == "ASVS-5.0-en.json"
        assert path.exists()

    def test_find_invalid_level(self, project_root):
        """Test finding source for invalid level."""
        with pytest.raises(ValueError, match="Invalid level"):
            find_source_file("4", project_root)


class TestCreateParser:
    """Tests for the argument parser."""

    def test_default_values(self):
        """Test default argument values."""
        parser = create_parser()
        args = parser.parse_args([])
        
        assert args.level == "2"
        assert args.format == "csv"
        assert args.source is None
        assert args.output is None
        assert args.verify_hash is None
        assert args.show_hash is False

    def test_level_argument(self):
        """Test level argument parsing."""
        parser = create_parser()
        args = parser.parse_args(["--level", "1"])
        assert args.level == "1"

    def test_format_argument(self):
        """Test format argument parsing."""
        parser = create_parser()
        args = parser.parse_args(["--format", "jira-json"])
        assert args.format == "jira-json"


class TestMain:
    """Integration tests for the main function."""

    def test_main_help(self, capsys):
        """Test main with --help exits cleanly."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_main_show_hash(self, project_root, capsys):
        """Test main with --show-hash."""
        result = main([
            "--level", "1",
            "--show-hash",
            "--base-path", str(project_root),
        ])
        
        assert result == 0
        captured = capsys.readouterr()
        assert len(captured.out.split()[0]) == 64  # SHA-256 hex length

    def test_main_csv_export(self, project_root, capsys):
        """Test main with CSV export."""
        result = main([
            "--level", "1",
            "--format", "csv",
            "--base-path", str(project_root),
        ])
        
        assert result == 0
        captured = capsys.readouterr()
        assert "Issue Key" in captured.out
        assert "ASVS" in captured.out

    def test_main_jira_json_export(self, project_root, capsys):
        """Test main with Jira JSON export."""
        result = main([
            "--level", "1",
            "--format", "jira-json",
            "--base-path", str(project_root),
        ])
        
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "issues" in data

    def test_main_with_output_file(self, project_root, tmp_path):
        """Test main with output file."""
        output_file = tmp_path / "output.csv"
        
        result = main([
            "--level", "1",
            "--format", "csv",
            "--output", str(output_file),
            "--base-path", str(project_root),
        ])
        
        assert result == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Issue Key" in content

    def test_main_invalid_source(self, capsys):
        """Test main with non-existent source file."""
        result = main([
            "--source", "/nonexistent/file.json",
        ])
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err
