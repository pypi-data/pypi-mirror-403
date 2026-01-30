import json
import pytest
from tools.iac_scanner import TerraformScanner

class TestTerraformScanner:
    @pytest.fixture
    def insecure_plan(self):
        return {
            "resource_changes": [
                {
                    "address": "aws_s3_bucket.bad_bucket",
                    "type": "aws_s3_bucket",
                    "values": {"bucket": "my-bad-bucket"}
                }
            ]
        }

    @pytest.fixture
    def secure_plan(self):
        return {
            "resource_changes": [
                {
                    "address": "aws_s3_bucket.good_bucket",
                    "type": "aws_s3_bucket",
                    "values": {"bucket": "my-good-bucket"}
                },
                {
                    "address": "aws_s3_bucket_server_side_encryption_configuration.good_bucket",
                    "type": "aws_s3_bucket_server_side_encryption_configuration",
                    "values": {"bucket": "my-good-bucket"}
                },
                {
                    "address": "aws_s3_bucket_public_access_block.good_bucket",
                    "type": "aws_s3_bucket_public_access_block",
                    "values": {"bucket": "my-good-bucket"}
                }
            ]
        }

    def test_scan_detects_missing_encryption(self, insecure_plan):
        scanner = TerraformScanner(insecure_plan)
        issues = scanner.scan()
        # Should detect missing encryption config
        assert any(i.rule_id == "V5.3.3" for i in issues)

    def test_scan_warns_on_bucket(self, insecure_plan):
        scanner = TerraformScanner(insecure_plan)
        issues = scanner.scan()
        # Should flag the bucket for manual review of public access
        assert any(i.resource == "aws_s3_bucket.bad_bucket" for i in issues)