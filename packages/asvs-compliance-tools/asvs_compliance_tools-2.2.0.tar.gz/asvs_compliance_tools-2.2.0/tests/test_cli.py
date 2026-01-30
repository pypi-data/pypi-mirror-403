"""Unit tests for the unified ASVS CLI."""

import pytest
from pathlib import Path

from tools.cli import create_parser, main


class TestCreateParser:
    """Tests for the argument parser creation."""

    def test_parser_creation(self):
        """Test that parser is created successfully."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "asvs"

    def test_version_argument(self):
        """Test --version argument."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_no_command_returns_none(self):
        """Test that no command sets command to None."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.command is None


class TestVerifyCommand:
    """Tests for 'asvs verify' command."""

    def test_verify_defaults(self):
        """Test verify command default values."""
        parser = create_parser()
        args = parser.parse_args(["verify"])
        assert args.command == "verify"
        assert args.level == 2
        assert args.docs_path is None
        assert args.evidence is None
        assert args.json is False
        assert args.strict is False

    def test_verify_with_level(self):
        """Test verify command with --level."""
        parser = create_parser()
        args = parser.parse_args(["verify", "--level", "3"])
        assert args.level == 3

    def test_verify_with_docs_path(self):
        """Test verify command with --docs-path."""
        parser = create_parser()
        args = parser.parse_args(["verify", "--docs-path", "/tmp/docs"])
        assert args.docs_path == Path("/tmp/docs")

    def test_verify_with_evidence(self):
        """Test verify command with --evidence."""
        parser = create_parser()
        args = parser.parse_args(["verify", "--evidence", "evidence.yml"])
        assert args.evidence == Path("evidence.yml")

    def test_verify_with_json_flag(self):
        """Test verify command with --json flag."""
        parser = create_parser()
        args = parser.parse_args(["verify", "--json"])
        assert args.json is True

    def test_verify_with_strict_flag(self):
        """Test verify command with --strict flag."""
        parser = create_parser()
        args = parser.parse_args(["verify", "--strict"])
        assert args.strict is True

    def test_verify_short_options(self):
        """Test verify command with short options."""
        parser = create_parser()
        args = parser.parse_args(["verify", "-l", "1", "-d", "/tmp/docs"])
        assert args.level == 1
        assert args.docs_path == Path("/tmp/docs")


class TestScanCommand:
    """Tests for 'asvs scan' command."""

    def test_scan_with_plan_file(self):
        """Test scan command with plan file."""
        parser = create_parser()
        args = parser.parse_args(["scan", "plan.json"])
        assert args.command == "scan"
        assert args.plan_file == Path("plan.json")

    def test_scan_with_json_flag(self):
        """Test scan command with --json flag."""
        parser = create_parser()
        args = parser.parse_args(["scan", "plan.json", "--json"])
        assert args.json is True


class TestTestCommand:
    """Tests for 'asvs test' command."""

    def test_test_with_url(self):
        """Test test command with URL."""
        parser = create_parser()
        args = parser.parse_args(["test", "https://example.com"])
        assert args.command == "test"
        assert args.url == "https://example.com"

    def test_test_with_allow_local(self):
        """Test test command with --allow-local flag."""
        parser = create_parser()
        args = parser.parse_args(["test", "http://localhost", "--allow-local"])
        assert args.allow_local is True

    def test_test_with_timeout(self):
        """Test test command with --timeout."""
        parser = create_parser()
        args = parser.parse_args(["test", "https://example.com", "--timeout", "30"])
        assert args.timeout == 30


class TestExportCommand:
    """Tests for 'asvs export' command."""

    def test_export_defaults(self):
        """Test export command default values."""
        parser = create_parser()
        args = parser.parse_args(["export"])
        assert args.command == "export"
        assert args.level == "2"
        assert args.format == "csv"
        assert args.output is None

    def test_export_with_level(self):
        """Test export command with --level."""
        parser = create_parser()
        args = parser.parse_args(["export", "--level", "3"])
        assert args.level == "3"

    def test_export_with_format(self):
        """Test export command with --format."""
        parser = create_parser()
        args = parser.parse_args(["export", "--format", "jira-json"])
        assert args.format == "jira-json"

    def test_export_with_output(self):
        """Test export command with --output."""
        parser = create_parser()
        args = parser.parse_args(["export", "--output", "reqs.csv"])
        assert args.output == Path("reqs.csv")

    def test_export_short_options(self):
        """Test export command with short options."""
        parser = create_parser()
        args = parser.parse_args(["export", "-l", "1", "-f", "csv", "-o", "out.csv"])
        assert args.level == "1"
        assert args.format == "csv"
        assert args.output == Path("out.csv")


class TestDriftCommand:
    """Tests for 'asvs drift' command."""

    def test_drift_defaults(self):
        """Test drift command default values."""
        parser = create_parser()
        args = parser.parse_args(["drift"])
        assert args.command == "drift"
        assert args.local is None
        assert args.offline is False
        assert args.json is False

    def test_drift_with_local(self):
        """Test drift command with --local."""
        parser = create_parser()
        args = parser.parse_args(["drift", "--local", "asvs.json"])
        assert args.local == Path("asvs.json")

    def test_drift_with_offline(self):
        """Test drift command with --offline."""
        parser = create_parser()
        args = parser.parse_args(["drift", "--offline"])
        assert args.offline is True


class TestInitCommand:
    """Tests for 'asvs init' command."""

    def test_init_defaults(self):
        """Test init command default values."""
        parser = create_parser()
        args = parser.parse_args(["init"])
        assert args.command == "init"
        assert args.interactive is True

    def test_init_with_interactive(self):
        """Test init command with --interactive."""
        parser = create_parser()
        args = parser.parse_args(["init", "--interactive"])
        assert args.interactive is True


class TestMainFunction:
    """Tests for the main CLI entry point."""

    def test_main_no_command_shows_help(self, capsys):
        """Test that no command shows help and returns 0."""
        result = main([])
        assert result == 0
        captured = capsys.readouterr()
        assert "OWASP ASVS Compliance Engine" in captured.out

    def test_main_help(self):
        """Test main with --help exits cleanly."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_main_verify_help(self):
        """Test verify --help exits cleanly."""
        with pytest.raises(SystemExit) as exc_info:
            main(["verify", "--help"])
        assert exc_info.value.code == 0

    def test_main_export_help(self):
        """Test export --help exits cleanly."""
        with pytest.raises(SystemExit) as exc_info:
            main(["export", "--help"])
        assert exc_info.value.code == 0


class TestVerifyIntegration:
    """Integration tests for verify command."""

    def test_verify_with_good_repo(self, project_root):
        """Test verify command with valid fixture."""
        docs_path = project_root / "tests" / "fixtures" / "good_repo" / "Decision-Templates"
        result = main([
            "verify",
            "--docs-path", str(docs_path),
            "--level", "2",
        ])
        assert result == 0

    def test_verify_with_missing_docs(self, tmp_path):
        """Test verify command with missing docs."""
        result = main([
            "verify",
            "--docs-path", str(tmp_path / "nonexistent"),
            "--level", "2",
        ])
        assert result == 1

    def test_verify_json_output(self, project_root, capsys):
        """Test verify command with JSON output."""
        docs_path = project_root / "tests" / "fixtures" / "good_repo" / "Decision-Templates"
        result = main([
            "verify",
            "--docs-path", str(docs_path),
            "--level", "2",
            "--json",
        ])
        assert result == 0
        captured = capsys.readouterr()
        assert '"passed": true' in captured.out


class TestExportIntegration:
    """Integration tests for export command."""

    def test_export_csv(self, project_root, capsys):
        """Test export command with CSV output."""
        result = main([
            "export",
            "--level", "1",
            "--format", "csv",
        ])
        assert result == 0
        captured = capsys.readouterr()
        assert "Issue Key" in captured.out

    def test_export_jira_json(self, project_root, capsys):
        """Test export command with Jira JSON output."""
        result = main([
            "export",
            "--level", "1",
            "--format", "jira-json",
        ])
        assert result == 0
        captured = capsys.readouterr()
        assert '"issues"' in captured.out


class TestDriftIntegration:
    """Integration tests for drift command."""

    def test_drift_offline(self, project_root, capsys):
        """Test drift command in offline mode."""
        result = main([
            "drift",
            "--offline",
        ])
        assert result == 0
        captured = capsys.readouterr()
        assert "ASVS Drift Detection Report" in captured.out
