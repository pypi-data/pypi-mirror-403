import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class ScanIssue:
    resource: str
    rule_id: str
    message: str
    severity: str

class TerraformScanner:
    """Scans Terraform Plan JSON for ASVS violations."""
    
    def __init__(self, plan_data: dict):
        self.plan = plan_data
        self.issues = []

    def scan(self):
        """Run all registered checks."""
        self.check_s3_public_access()
        self.check_s3_encryption()
        return self.issues

    def check_s3_public_access(self):
        """ASVS V5.3.4: Verify S3 Public Access Block exists."""
        # 1. Find all AWS buckets
        buckets = self._find_resources("aws_s3_bucket")
        # 2. Find all access blocks
        blocks = self._find_resources("aws_s3_bucket_public_access_block")
        
        # simple heuristic mapping
        protected_buckets = set()
        for b in blocks:
            # In plan JSON, values might be unknown/computed, but we check 'address' or 'name' refs
            # This is a simplified check for the starter kit
            values = b.get("values", {})
            bucket_ref = values.get("bucket")
            if bucket_ref:
                protected_buckets.add(bucket_ref)

        for bucket in buckets:
            # If we can't link it easily (e.g. calculated ID), we warn
            # Real production usage needs terraform-json library or graph traversal
            self.issues.append(ScanIssue(
                resource=bucket["address"],
                rule_id="V5.3.4",
                message="Ensure aws_s3_bucket_public_access_block is attached to this bucket.",
                severity="HIGH"
            ))

    def check_s3_encryption(self):
        """ASVS V5.3.3: Verify S3 Encryption."""
        # Modern AWS provider uses aws_s3_bucket_server_side_encryption_configuration
        enc_configs = self._find_resources("aws_s3_bucket_server_side_encryption_configuration")
        if not enc_configs:
             self.issues.append(ScanIssue(
                resource="global",
                rule_id="V5.3.3",
                message="No S3 Server Side Encryption configurations found in plan.",
                severity="HIGH"
            ))

    def _find_resources(self, resource_type):
        resources = []
        # Handle 'resource_changes' from plan JSON
        for rc in self.plan.get("resource_changes", []):
            if rc["type"] == resource_type:
                resources.append(rc)
        return resources

def main(args=None):
    parser = argparse.ArgumentParser(description="ASVS Infrastructure Scanner")
    parser.add_argument("--plan-file", required=True, type=Path, help="Path to terraform show -json output")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parsed = parser.parse_args(args)

    if not parsed.plan_file.exists():
        print(f"Error: Plan file {parsed.plan_file} not found.")
        return 1

    try:
        data = json.loads(parsed.plan_file.read_text())
    except json.JSONDecodeError:
        print("Error: Invalid JSON file.")
        return 1

    scanner = TerraformScanner(data)
    issues = scanner.scan()

    if parsed.format == "json":
        print(json.dumps([asdict(i) for i in issues], indent=2))
    else:
        print("ASVS Infrastructure Scan Report")
        print("=" * 30)
        if not issues:
            print("No issues detected (Note: Logic is heuristic).")
        for i in issues:
            print(f"[{i.severity}] {i.rule_id}: {i.message} ({i.resource})")

    return 1 if issues else 0

if __name__ == "__main__":
    sys.exit(main())