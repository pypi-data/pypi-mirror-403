# File: tests/test_evidence_verifier.py

import pytest
from pathlib import Path
from tools.compliance_gate import EvidenceVerifier

class TestEvidenceVerifier:
    
    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a temporary workspace with some dummy files."""
        # Create a dummy package.json
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"helmet": "^4.0.0", "bcrypt": "^5.0.0"}}', 
            encoding="utf-8"
        )
        # Create a dummy config
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "settings.py").write_text(
            "DEBUG = False\nSECRET_KEY = 'env'", 
            encoding="utf-8"
        )
        return tmp_path

    def test_check_file_exists_success(self, workspace):
        verifier = EvidenceVerifier(workspace)
        passed, msg = verifier.check_file_exists("package.json")
        assert passed is True
        assert "File found" in msg

    def test_check_file_exists_failure(self, workspace):
        verifier = EvidenceVerifier(workspace)
        passed, msg = verifier.check_file_exists("missing.txt")
        assert passed is False
        assert "File not found" in msg

    def test_check_content_match_success(self, workspace):
        """Verify we can find 'helmet' in package.json (simulating ASVS V14.4)."""
        verifier = EvidenceVerifier(workspace)
        passed, msg = verifier.check_file_contains("package.json", r"\"helmet\"")
        assert passed is True

    def test_check_content_match_failure(self, workspace):
        """Verify we fail if a required library is missing."""
        verifier = EvidenceVerifier(workspace)
        # FIX: Changed from check_content_match to check_file_contains
        passed, msg = verifier.check_file_contains("package.json", r"\"react\"")
        assert passed is False

    def test_verify_requirement_integration(self, workspace):
        """Test the full flow for a requirement."""
        verifier = EvidenceVerifier(workspace)
        checks = [
            {"type": "file_exists", "path": "package.json"},
            {"type": "content_match", "path": "config/settings.py", "pattern": "DEBUG = False"}
        ]
        
        results = verifier.verify_requirement("V1.2.3", checks)
        
        assert len(results) == 2
        assert all(r.passed for r in results)
        assert results[0].requirement_id == "V1.2.3"