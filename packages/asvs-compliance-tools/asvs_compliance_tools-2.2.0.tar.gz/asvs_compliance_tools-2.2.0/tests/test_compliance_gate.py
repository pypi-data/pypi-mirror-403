"""Unit tests for ASVS Compliance Gate."""

import json
from pathlib import Path

import pytest

from tools.compliance_gate import (
    ComplianceGate,
    ValidationResult,
    GateResult,
    DEFAULT_PLACEHOLDER_PATTERNS,
    REQUIRED_DOCUMENTS_BY_LEVEL,
    resolve_docs_path,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_is_valid_when_all_conditions_met(self):
        """Document is valid when exists, has content, no placeholders."""
        result = ValidationResult(
            document="test.md",
            exists=True,
            has_content=True,
            has_placeholders=False,
        )
        assert result.is_valid is True

    def test_is_invalid_when_missing(self):
        """Document is invalid when it doesn't exist."""
        result = ValidationResult(
            document="test.md",
            exists=False,
            has_content=False,
            has_placeholders=False,
        )
        assert result.is_valid is False

    def test_is_invalid_when_empty(self):
        """Document is invalid when empty."""
        result = ValidationResult(
            document="test.md",
            exists=True,
            has_content=False,
            has_placeholders=False,
        )
        assert result.is_valid is False

    def test_is_invalid_when_has_placeholders(self):
        """Document is invalid when it has placeholder text."""
        result = ValidationResult(
            document="test.md",
            exists=True,
            has_content=True,
            has_placeholders=True,
            placeholder_matches=["[Project Name]"],
        )
        assert result.is_valid is False


class TestGateResult:
    """Tests for GateResult dataclass."""

    def test_to_dict_serialization(self):
        """GateResult can be serialized to dict."""
        result = GateResult(
            passed=True,
            level=2,
            documents_checked=1,
            documents_valid=1,
            document_results=[  # Fixed: changed from results
                ValidationResult(
                    document="test.md",
                    exists=True,
                    has_content=True,
                    has_placeholders=False,
                )
            ],
            errors=[],
        )
        d = result.to_dict()
        assert d["passed"] is True
        assert d["level"] == 2
        # Check nested documents/results structure
        assert len(d["documents"]["results"]) == 1
        assert d["documents"]["results"][0]["is_valid"] is True


class TestComplianceGate:
    """Tests for ComplianceGate class."""

    @pytest.fixture
    def good_doc_content(self):
        """Valid document content without placeholders."""
        return """# Security Decision: Cryptography Strategy

| Field | Value |
| :--- | :--- |
| **Project Name:** | My Actual Project |
| **Document Owner:** | Security Team Lead |
| **Date:** | 2024-01-15 |
| **Status:** | Approved |

## 1. Applicable ASVS Requirements

This document serves as the central inventory for all cryptographic choices.

## 2. Cryptographic Use Cases

| Use Case | Algorithm | Key Length | Justification |
| :--- | :--- | :--- | :--- |
| **Password Storage** | Argon2id | 64MiB mem | GPU-resistant |
"""

    @pytest.fixture
    def placeholder_doc_content(self):
        """Document content with placeholder text."""
        return """# Security Decision: Cryptography Strategy

| Field | Value |
| :--- | :--- |
| **Project Name:** | `[Project Name]` |
| **Document Owner:** | `[e.g., Cryptography Lead]` |
| **Date:** | `YYYY-MM-DD` |

## Some content here to make it long enough for validation.
This is additional content to pass the minimum length requirement.
"""

    @pytest.fixture
    def empty_doc_content(self):
        """Empty or minimal document content."""
        return "# Title\n\nShort."

    @pytest.fixture
    def good_repo(self, tmp_path, good_doc_content):
        """Create a valid repo structure."""
        docs_path = tmp_path / "Decision-Templates"
        docs_path.mkdir()
        (docs_path / "V11-Cryptography-Strategy.md").write_text(
            good_doc_content, encoding="utf-8"
        )
        return docs_path

    @pytest.fixture
    def bad_repo_missing(self, tmp_path):
        """Create a repo structure with missing document."""
        docs_path = tmp_path / "Decision-Templates"
        docs_path.mkdir()
        return docs_path

    @pytest.fixture
    def bad_repo_placeholder(self, tmp_path, placeholder_doc_content):
        """Create a repo structure with placeholder document."""
        docs_path = tmp_path / "Decision-Templates"
        docs_path.mkdir()
        (docs_path / "V11-Cryptography-Strategy.md").write_text(
            placeholder_doc_content, encoding="utf-8"
        )
        return docs_path

    @pytest.fixture
    def bad_repo_empty(self, tmp_path, empty_doc_content):
        """Create a repo structure with empty document."""
        docs_path = tmp_path / "Decision-Templates"
        docs_path.mkdir()
        (docs_path / "V11-Cryptography-Strategy.md").write_text(
            empty_doc_content, encoding="utf-8"
        )
        return docs_path

    def test_get_required_documents_level1(self, tmp_path):
        """Level 1 has no required documents."""
        gate = ComplianceGate(docs_path=tmp_path, level=1)
        assert gate.get_required_documents() == []

    def test_get_required_documents_level2(self, tmp_path):
        """Level 2 requires V11 Cryptography Strategy."""
        gate = ComplianceGate(docs_path=tmp_path, level=2)
        required = gate.get_required_documents()
        assert "V11-Cryptography-Strategy.md" in required

    def test_get_required_documents_level3(self, tmp_path):
        """Level 3 requires at least V11 Cryptography Strategy."""
        gate = ComplianceGate(docs_path=tmp_path, level=3)
        required = gate.get_required_documents()
        assert "V11-Cryptography-Strategy.md" in required

    def test_validate_document_exists_with_content(self, good_repo, good_doc_content):
        """Valid document passes all checks."""
        gate = ComplianceGate(docs_path=good_repo, level=2)
        result = gate.validate_document("V11-Cryptography-Strategy.md")
        assert result.exists is True
        assert result.has_content is True
        assert result.has_placeholders is False
        assert result.is_valid is True

    def test_validate_document_missing(self, bad_repo_missing):
        """Missing document fails existence check."""
        gate = ComplianceGate(docs_path=bad_repo_missing, level=2)
        result = gate.validate_document("V11-Cryptography-Strategy.md")
        assert result.exists is False
        assert result.is_valid is False
        assert "not found" in result.error.lower()

    def test_validate_document_with_placeholders(self, bad_repo_placeholder):
        """Document with placeholders fails placeholder check."""
        gate = ComplianceGate(docs_path=bad_repo_placeholder, level=2)
        result = gate.validate_document("V11-Cryptography-Strategy.md")
        assert result.exists is True
        assert result.has_content is True
        assert result.has_placeholders is True
        assert result.is_valid is False
        assert len(result.placeholder_matches) > 0

    def test_validate_document_empty(self, bad_repo_empty):
        """Empty document fails content check."""
        gate = ComplianceGate(docs_path=bad_repo_empty, level=2)
        result = gate.validate_document("V11-Cryptography-Strategy.md")
        assert result.exists is True
        assert result.has_content is False
        assert result.is_valid is False

    def test_run_passes_with_valid_docs(self, good_repo):
        """Gate passes when all required documents are valid."""
        gate = ComplianceGate(docs_path=good_repo, level=2)
        result = gate.run()
        assert result.passed is True
        assert result.documents_valid == result.documents_checked
        assert len(result.errors) == 0

    def test_run_fails_with_missing_docs(self, bad_repo_missing):
        """Gate fails when required documents are missing."""
        gate = ComplianceGate(docs_path=bad_repo_missing, level=2)
        result = gate.run()
        assert result.passed is False
        assert result.documents_valid == 0
        assert len(result.errors) > 0

    def test_run_fails_with_placeholder_docs(self, bad_repo_placeholder):
        """Gate fails when documents contain placeholder text."""
        gate = ComplianceGate(docs_path=bad_repo_placeholder, level=2)
        result = gate.run()
        assert result.passed is False
        assert len(result.errors) > 0

    def test_run_fails_with_empty_docs(self, bad_repo_empty):
        """Gate fails when documents are empty."""
        gate = ComplianceGate(docs_path=bad_repo_empty, level=2)
        result = gate.run()
        assert result.passed is False

    def test_run_level1_always_passes(self, bad_repo_missing):
        """Level 1 has no requirements, so always passes."""
        gate = ComplianceGate(docs_path=bad_repo_missing, level=1)
        result = gate.run()
        assert result.passed is True
        assert result.documents_checked == 0

    def test_run_nonexistent_path(self, tmp_path):
        """Gate fails gracefully when docs path doesn't exist."""
        gate = ComplianceGate(docs_path=tmp_path / "nonexistent", level=2)
        result = gate.run()
        assert result.passed is False
        assert "not found" in result.errors[0].lower()

    def test_custom_placeholder_patterns(self, tmp_path):
        """Custom placeholder patterns are detected."""
        docs_path = tmp_path / "docs"
        docs_path.mkdir()
        content = """# Document

This has a custom placeholder: {{REPLACE_ME}}

More content here to make it long enough for the minimum length check.
Additional lines of content for validation purposes.
"""
        (docs_path / "V11-Cryptography-Strategy.md").write_text(
            content, encoding="utf-8"
        )

        gate = ComplianceGate(
            docs_path=docs_path,
            level=2,
            placeholder_patterns=[r"\{\{.*?\}\}"],
        )
        result = gate.validate_document("V11-Cryptography-Strategy.md")
        assert result.has_placeholders is True

    def test_custom_required_documents(self, tmp_path):
        """Custom required documents configuration works."""
        docs_path = tmp_path / "docs"
        docs_path.mkdir()
        content = """# Custom Document

This is a valid document with enough content.
More lines to satisfy the minimum content length requirement.
Additional content for testing purposes.
"""
        (docs_path / "Custom-Security-Doc.md").write_text(content, encoding="utf-8")

        gate = ComplianceGate(
            docs_path=docs_path,
            level=2,
            required_documents={1: [], 2: ["Custom-Security-Doc.md"]},
        )
        result = gate.run()
        assert result.passed is True

    def test_json_output_format(self, good_repo):
        """Result can be serialized to valid JSON."""
        gate = ComplianceGate(docs_path=good_repo, level=2)
        result = gate.run()
        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)
        assert parsed["passed"] is True


class TestPlaceholderPatterns:
    """Tests for default placeholder pattern detection."""

    @pytest.fixture
    def gate(self, tmp_path):
        """Create a gate for pattern testing."""
        docs_path = tmp_path / "docs"
        docs_path.mkdir()
        return ComplianceGate(docs_path=docs_path, level=2)

    def test_detects_project_name_placeholder(self, gate, tmp_path):
        """Detects [Project Name] placeholder."""
        content = "# Doc\n\n[Project Name] is a placeholder.\n" + "x" * 100
        doc_path = tmp_path / "docs" / "V11-Cryptography-Strategy.md"
        doc_path.write_text(content, encoding="utf-8")
        result = gate.validate_document("V11-Cryptography-Strategy.md")
        assert result.has_placeholders is True

    def test_detects_eg_placeholder(self, gate, tmp_path):
        """Detects [e.g., ...] placeholder."""
        content = "# Doc\n\nSome text [e.g., example here].\n" + "x" * 100
        doc_path = tmp_path / "docs" / "V11-Cryptography-Strategy.md"
        doc_path.write_text(content, encoding="utf-8")
        result = gate.validate_document("V11-Cryptography-Strategy.md")
        assert result.has_placeholders is True

    def test_detects_date_placeholder(self, gate, tmp_path):
        """Detects YYYY-MM-DD placeholder."""
        content = "# Doc\n\nDate: YYYY-MM-DD\n" + "x" * 100
        doc_path = tmp_path / "docs" / "V11-Cryptography-Strategy.md"
        doc_path.write_text(content, encoding="utf-8")
        result = gate.validate_document("V11-Cryptography-Strategy.md")
        assert result.has_placeholders is True

    def test_detects_backtick_placeholder(self, gate, tmp_path):
        """Detects `[placeholder]` pattern."""
        content = "# Doc\n\nValue: `[Some Value]`\n" + "x" * 100
        doc_path = tmp_path / "docs" / "V11-Cryptography-Strategy.md"
        doc_path.write_text(content, encoding="utf-8")
        result = gate.validate_document("V11-Cryptography-Strategy.md")
        assert result.has_placeholders is True

    def test_no_false_positive_on_real_content(self, gate, tmp_path):
        """Real content without placeholders passes."""
        content = """# Cryptography Strategy

| Field | Value |
| :--- | :--- |
| **Project Name:** | Acme Corp API |
| **Date:** | 2024-03-15 |

## Implementation Details

We use AES-256-GCM for encryption with keys stored in AWS KMS.
Password hashing uses Argon2id with appropriate parameters.
"""
        doc_path = tmp_path / "docs" / "V11-Cryptography-Strategy.md"
        doc_path.write_text(content, encoding="utf-8")
        result = gate.validate_document("V11-Cryptography-Strategy.md")
        assert result.has_placeholders is False


class TestRegressionBypassAttempts:
    """Regression tests for bypass attempts (Abuser Stories)."""

    def test_empty_file_bypass_fails(self, tmp_path):
        """Empty file (0 bytes) fails validation."""
        docs_path = tmp_path / "docs"
        docs_path.mkdir()
        (docs_path / "V11-Cryptography-Strategy.md").write_text("", encoding="utf-8")

        gate = ComplianceGate(docs_path=docs_path, level=2)
        result = gate.run()
        assert result.passed is False

    def test_whitespace_only_file_fails(self, tmp_path):
        """Whitespace-only file fails validation."""
        docs_path = tmp_path / "docs"
        docs_path.mkdir()
        (docs_path / "V11-Cryptography-Strategy.md").write_text(
            "   \n\n\t\t\n   ", encoding="utf-8"
        )

        gate = ComplianceGate(docs_path=docs_path, level=2)
        result = gate.run()
        assert result.passed is False

    def test_placeholder_only_file_fails(self, tmp_path):
        """File with only placeholder text fails validation."""
        docs_path = tmp_path / "docs"
        docs_path.mkdir()
        content = """# [Project Name]

[e.g., Description here]

Date: YYYY-MM-DD

More placeholder content `[value]` to make it long enough.
"""
        (docs_path / "V11-Cryptography-Strategy.md").write_text(
            content, encoding="utf-8"
        )

        gate = ComplianceGate(docs_path=docs_path, level=2)
        result = gate.run()
        assert result.passed is False

    def test_partial_placeholder_replacement_fails(self, tmp_path):
        """File with some placeholders remaining fails."""
        docs_path = tmp_path / "docs"
        docs_path.mkdir()
        content = """# My Real Project

This is real content about cryptography.

But the date is still: YYYY-MM-DD

And some values are still `[not filled in]` which is a problem.
We need more content here to pass the length check.
"""
        (docs_path / "V11-Cryptography-Strategy.md").write_text(
            content, encoding="utf-8"
        )

        gate = ComplianceGate(docs_path=docs_path, level=2)
        result = gate.run()
        assert result.passed is False


class TestResolveDocsPath:
    """Tests for resolve_docs_path function."""

    def test_returns_user_path_when_provided(self, tmp_path):
        """When user provides a path, return it directly."""
        user_path = tmp_path / "custom-docs"
        user_path.mkdir()
        result = resolve_docs_path(user_path)
        assert result == user_path

    def test_returns_user_path_even_if_not_exists(self, tmp_path):
        """When user provides a path, return it even if it doesn't exist."""
        user_path = tmp_path / "nonexistent"
        result = resolve_docs_path(user_path)
        assert result == user_path

    def test_auto_detects_docs_directory(self, tmp_path, monkeypatch):
        """Auto-detect ./docs directory when no path provided."""
        monkeypatch.chdir(tmp_path)
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        result = resolve_docs_path(None)
        assert result == Path("docs")

    def test_auto_detects_product_specific_files(self, tmp_path, monkeypatch):
        """Auto-detect ./03-Product-Specific-Files when docs doesn't exist."""
        monkeypatch.chdir(tmp_path)
        product_dir = tmp_path / "03-Product-Specific-Files"
        product_dir.mkdir()
        result = resolve_docs_path(None)
        assert result == Path("03-Product-Specific-Files")

    def test_prefers_docs_over_product_specific(self, tmp_path, monkeypatch):
        """Prefer ./docs over ./03-Product-Specific-Files."""
        monkeypatch.chdir(tmp_path)
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        product_dir = tmp_path / "03-Product-Specific-Files"
        product_dir.mkdir()
        result = resolve_docs_path(None)
        assert result == Path("docs")

    def test_falls_back_to_current_directory(self, tmp_path, monkeypatch):
        """Fall back to current directory when no candidates found."""
        monkeypatch.chdir(tmp_path)
        result = resolve_docs_path(None)
        assert result == Path(".")
