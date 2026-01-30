#!/usr/bin/env python3
"""
ASVS Verification Suite - Light DAST for Security Controls
ASVS V3.5.1, V2.1, V14.4: Automated verification of common security controls

This tool performs automated checks against a target web application to verify
the presence of essential security controls including:
- CSRF token validation
- Security headers
- Password policy enforcement
- Cookie security attributes

Usage:
    asvs test https://example.com
    asvs test https://example.com --json
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from urllib.parse import urljoin, urlparse
import socket
import ipaddress

class TestResult(Enum):
    """Result status for individual security tests."""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"

class UrlValidator:
    """Security controls for target URL validation."""
    
    # Block loopback, link-local, and private ranges by default
    BLOCKED_RANGES = [
        "127.0.0.0/8",
        "169.254.0.0/16",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "::1/128",
        "fc00::/7"
    ]

    @staticmethod
    def is_safe_url(url: str, allow_local: bool = False) -> bool:
        """
        Validate URL against SSRF protections.
        Returns True if safe, False otherwise.
        """
        if allow_local:
            return True

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return False

            # Resolve hostname to IP
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)

            # Check against blocked ranges
            for cidr in UrlValidator.BLOCKED_RANGES:
                if ip in ipaddress.ip_network(cidr):
                    print(f"Security Warning: Target resolves to restricted IP {ip}")
                    return False
            
            return True
        except Exception as e:
            print(f"URL Validation Error: {e}")
            return False

@dataclass
class SecurityTest:
    """Result of a single security test."""
    name: str
    asvs_id: str
    description: str
    result: TestResult
    details: str = ""
    recommendation: str = ""


@dataclass
class VerificationReport:
    """Complete verification report for a target."""
    target_url: str
    tests: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def add_test(self, test: SecurityTest) -> None:
        """Add a test result to the report."""
        self.tests.append(test)

    def compute_summary(self) -> None:
        """Compute summary statistics."""
        self.summary = {
            "total": len(self.tests),
            "passed": sum(1 for t in self.tests if t.result == TestResult.PASS),
            "failed": sum(1 for t in self.tests if t.result == TestResult.FAIL),
            "skipped": sum(1 for t in self.tests if t.result == TestResult.SKIP),
            "errors": sum(1 for t in self.tests if t.result == TestResult.ERROR),
        }

    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        self.compute_summary()
        return {
            "target_url": self.target_url,
            "summary": self.summary,
            "tests": [
                {
                    "name": t.name,
                    "asvs_id": t.asvs_id,
                    "description": t.description,
                    "result": t.result.value,
                    "details": t.details,
                    "recommendation": t.recommendation,
                }
                for t in self.tests
            ],
        }

    def has_failures(self) -> bool:
        """Check if any tests failed."""
        return any(t.result == TestResult.FAIL for t in self.tests)


class SecurityHeaderChecker:
    """
    Checks for presence and correctness of security headers.
    ASVS V8.1, V14.4: HTTP Security Headers
    """

    REQUIRED_HEADERS = {
        "Strict-Transport-Security": {
            "asvs_id": "V14.4.4",
            "description": "HSTS header enforces HTTPS connections",
            "recommendation": "Add Strict-Transport-Security: max-age=31536000; includeSubDomains",
        },
        "X-Content-Type-Options": {
            "asvs_id": "V14.4.1",
            "description": "Prevents MIME type sniffing",
            "expected": "nosniff",
            "recommendation": "Add X-Content-Type-Options: nosniff",
        },
        "X-Frame-Options": {
            "asvs_id": "V8.1.1",
            "description": "Prevents clickjacking attacks",
            "expected": ["DENY", "SAMEORIGIN"],
            "recommendation": "Add X-Frame-Options: DENY",
        },
        "Content-Security-Policy": {
            "asvs_id": "V14.4.3",
            "description": "CSP prevents XSS and data injection attacks",
            "recommendation": "Add a Content-Security-Policy header",
        },
    }

    OPTIONAL_HEADERS = {
        "Referrer-Policy": {
            "asvs_id": "V14.4.5",
            "description": "Controls referrer information leakage",
            "recommendation": "Add Referrer-Policy: strict-origin-when-cross-origin",
        },
        "Permissions-Policy": {
            "asvs_id": "V14.4.6",
            "description": "Restricts browser feature access",
            "recommendation": "Add Permissions-Policy to restrict unused features",
        },
    }

    def check_headers(self, headers: dict) -> list:
        """Check all security headers and return test results."""
        results = []

        # Check required headers
        for header, config in self.REQUIRED_HEADERS.items():
            result = self._check_single_header(headers, header, config, required=True)
            results.append(result)

        # Check optional headers (informational)
        for header, config in self.OPTIONAL_HEADERS.items():
            result = self._check_single_header(headers, header, config, required=False)
            results.append(result)

        return results

    def _check_single_header(
        self, headers: dict, header_name: str, config: dict, required: bool
    ) -> SecurityTest:
        """Check a single header."""
        # Case-insensitive header lookup
        header_value = None
        for key, value in headers.items():
            if key.lower() == header_name.lower():
                header_value = value
                break

        if header_value is None:
            return SecurityTest(
                name=f"Security Header: {header_name}",
                asvs_id=config["asvs_id"],
                description=config["description"],
                result=TestResult.FAIL if required else TestResult.SKIP,
                details=f"Header '{header_name}' is missing",
                recommendation=config["recommendation"],
            )

        # Check expected value if specified
        expected = config.get("expected")
        if expected:
            if isinstance(expected, list):
                valid = any(header_value.upper().startswith(e) for e in expected)
            else:
                valid = header_value.lower() == expected.lower()

            if not valid:
                return SecurityTest(
                    name=f"Security Header: {header_name}",
                    asvs_id=config["asvs_id"],
                    description=config["description"],
                    result=TestResult.FAIL,
                    details=f"Header value '{header_value}' does not match expected",
                    recommendation=config["recommendation"],
                )

        return SecurityTest(
            name=f"Security Header: {header_name}",
            asvs_id=config["asvs_id"],
            description=config["description"],
            result=TestResult.PASS,
            details=f"Header present with value: {header_value}",
        )


class CookieSecurityChecker:
    """
    Checks cookie security attributes.
    ASVS V3.4: Cookie Security
    """

    def check_cookies(self, cookies: list) -> list:
        """Check all cookies for security attributes."""
        results = []

        if not cookies:
            results.append(SecurityTest(
                name="Cookie Security: Session Cookies",
                asvs_id="V3.4.1",
                description="No cookies found to analyze",
                result=TestResult.SKIP,
                details="No Set-Cookie headers in response",
            ))
            return results

        for cookie in cookies:
            results.extend(self._check_single_cookie(cookie))

        return results

    def _check_single_cookie(self, cookie_string: str) -> list:
        """Check a single cookie for security attributes."""
        results = []
        parts = cookie_string.split(";")
        cookie_name = parts[0].split("=")[0].strip() if parts else "Unknown"

        # Normalize attributes to lowercase for checking
        attrs_lower = [p.strip().lower() for p in parts[1:]]

        # Check HttpOnly
        has_httponly = any("httponly" in attr for attr in attrs_lower)
        results.append(SecurityTest(
            name=f"Cookie Security: HttpOnly ({cookie_name})",
            asvs_id="V3.4.2",
            description="HttpOnly prevents JavaScript access to cookie",
            result=TestResult.PASS if has_httponly else TestResult.FAIL,
            details="HttpOnly attribute present" if has_httponly else "Missing HttpOnly attribute",
            recommendation="" if has_httponly else "Add HttpOnly flag to sensitive cookies",
        ))

        # Check Secure
        has_secure = any("secure" in attr for attr in attrs_lower)
        results.append(SecurityTest(
            name=f"Cookie Security: Secure ({cookie_name})",
            asvs_id="V3.4.3",
            description="Secure flag ensures cookie is only sent over HTTPS",
            result=TestResult.PASS if has_secure else TestResult.FAIL,
            details="Secure attribute present" if has_secure else "Missing Secure attribute",
            recommendation="" if has_secure else "Add Secure flag to all cookies",
        ))

        # Check SameSite
        has_samesite = any("samesite" in attr for attr in attrs_lower)
        samesite_value = None
        for attr in attrs_lower:
            if "samesite" in attr:
                if "=" in attr:
                    samesite_value = attr.split("=")[1].strip()
                break

        if has_samesite and samesite_value in ["strict", "lax"]:
            result = TestResult.PASS
            details = f"SameSite={samesite_value}"
        elif has_samesite and samesite_value == "none":
            result = TestResult.FAIL
            details = "SameSite=None allows cross-site requests"
        else:
            result = TestResult.FAIL
            details = "Missing SameSite attribute"

        results.append(SecurityTest(
            name=f"Cookie Security: SameSite ({cookie_name})",
            asvs_id="V3.4.4",
            description="SameSite prevents CSRF via cross-site cookie sending",
            result=result,
            details=details,
            recommendation="" if result == TestResult.PASS else "Add SameSite=Strict or SameSite=Lax",
        ))

        return results


class CSRFChecker:
    """
    Checks for CSRF protection mechanisms.
    ASVS V3.5.1: Anti-forgery tokens
    """

    CSRF_INDICATORS = [
        # Common CSRF token input names
        r'name=["\']?_?csrf[_-]?token["\']?',
        r'name=["\']?csrfmiddlewaretoken["\']?',  # Django style
        r'name=["\']?authenticity[_-]?token["\']?',
        r'name=["\']?_token["\']?',
        r'name=["\']?_csrf["\']?',
        r'name=["\']?__RequestVerificationToken["\']?',
        # Common CSRF meta tags
        r'<meta\s+name=["\']?csrf[_-]?token["\']?',
        r'<meta\s+name=["\']?_csrf["\']?',
    ]

    CSRF_COOKIE_NAMES = [
        "csrf", "xsrf", "_csrf", "csrftoken", "xsrf-token", "_xsrf"
    ]

    def check_csrf_protection(
        self, html_content: str, cookies: list, headers: dict
    ) -> SecurityTest:
        """Check for CSRF protection mechanisms."""
        findings = []

        # Check for CSRF token in HTML forms
        for pattern in self.CSRF_INDICATORS:
            if re.search(pattern, html_content, re.IGNORECASE):
                findings.append("CSRF token found in HTML")
                break

        # Check for CSRF cookie
        for cookie in cookies:
            cookie_name = cookie.split("=")[0].strip().lower()
            if any(csrf_name in cookie_name for csrf_name in self.CSRF_COOKIE_NAMES):
                findings.append(f"CSRF cookie found: {cookie_name}")
                break

        # Check for CSRF header requirement indicators
        csrf_header_patterns = [
            r'X-CSRF-Token',
            r'X-XSRF-TOKEN',
            r'X-Requested-With',
        ]
        for pattern in csrf_header_patterns:
            if re.search(pattern, html_content, re.IGNORECASE):
                findings.append(f"CSRF header reference found: {pattern}")
                break

        if findings:
            return SecurityTest(
                name="CSRF Protection",
                asvs_id="V3.5.1",
                description="Anti-forgery tokens protect against CSRF attacks",
                result=TestResult.PASS,
                details="; ".join(findings),
            )
        else:
            return SecurityTest(
                name="CSRF Protection",
                asvs_id="V3.5.1",
                description="Anti-forgery tokens protect against CSRF attacks",
                result=TestResult.FAIL,
                details="No CSRF protection mechanisms detected",
                recommendation="Implement CSRF tokens using Synchronizer Token or Double Submit Cookie pattern",
            )


class PasswordPolicyChecker:
    """
    Checks password policy indicators.
    ASVS V2.1: Password Security
    """

    def check_password_fields(self, html_content: str) -> list:
        """Analyze password fields for security indicators."""
        results = []

        # Find password inputs
        password_inputs = re.findall(
            r'<input[^>]*type=["\']password["\'][^>]*>',
            html_content,
            re.IGNORECASE
        )

        if not password_inputs:
            results.append(SecurityTest(
                name="Password Field Analysis",
                asvs_id="V2.1.1",
                description="No password fields found to analyze",
                result=TestResult.SKIP,
                details="Page does not contain password input fields",
            ))
            return results

        for i, field in enumerate(password_inputs):
            # Check for autocomplete attribute
            has_autocomplete_off = re.search(
                r'autocomplete=["\'](?:off|new-password|current-password)["\']',
                field,
                re.IGNORECASE
            )

            # Check for minlength attribute
            minlength_match = re.search(r'minlength=["\']?(\d+)["\']?', field, re.IGNORECASE)
            minlength = int(minlength_match.group(1)) if minlength_match else 0

            # Check for pattern attribute (complexity)
            has_pattern = re.search(r'pattern=["\'][^"\']+["\']', field, re.IGNORECASE)

            # Evaluate password field security
            issues = []
            if not has_autocomplete_off:
                issues.append("Missing autocomplete attribute")
            if minlength < 12:
                issues.append(f"Minlength ({minlength}) below recommended 12 characters")

            if issues:
                results.append(SecurityTest(
                    name=f"Password Field #{i+1}",
                    asvs_id="V2.1.1",
                    description="Password field security attributes",
                    result=TestResult.FAIL,
                    details="; ".join(issues),
                    recommendation="Set minlength>=12 and appropriate autocomplete attribute",
                ))
            else:
                results.append(SecurityTest(
                    name=f"Password Field #{i+1}",
                    asvs_id="V2.1.1",
                    description="Password field security attributes",
                    result=TestResult.PASS,
                    details="Password field has appropriate security attributes",
                ))

        return results


class VerificationSuite:
    """
    Main verification suite that orchestrates all security checks.
    """

    def __init__(self, target_url: str, timeout: int = 10, allow_local: bool = False):
        self.target_url = target_url
        self.timeout = timeout
        if not UrlValidator.is_safe_url(target_url, allow_local):
            raise ValueError(f"Target URL '{target_url}' is not allowed (SSRF Protection). Use --allow-local to override.")
        self.header_checker = SecurityHeaderChecker()
        self.cookie_checker = CookieSecurityChecker()
        self.csrf_checker = CSRFChecker()
        self.password_checker = PasswordPolicyChecker()

    def run_verification(self, response_data: Optional[dict] = None) -> VerificationReport:
        """
        Run all verification checks.

        Args:
            response_data: Optional dict with 'headers', 'cookies', 'content' keys.
                          If None, will attempt to fetch from target_url.
        """
        report = VerificationReport(target_url=self.target_url)

        if response_data is None:
            response_data = self._fetch_target()

        if response_data is None:
            report.add_test(SecurityTest(
                name="Target Connectivity",
                asvs_id="N/A",
                description="Unable to connect to target",
                result=TestResult.ERROR,
                details=f"Could not fetch {self.target_url}",
                recommendation="Verify the target URL is accessible",
            ))
            return report

        headers = response_data.get("headers", {})
        cookies = response_data.get("cookies", [])
        content = response_data.get("content", "")

        # Run all checks
        report.tests.extend(self.header_checker.check_headers(headers))
        report.tests.extend(self.cookie_checker.check_cookies(cookies))
        report.add_test(self.csrf_checker.check_csrf_protection(content, cookies, headers))
        report.tests.extend(self.password_checker.check_password_fields(content))

        report.compute_summary()
        return report

    def _fetch_target(self) -> Optional[dict]:
        """Fetch target URL and return response data."""
        try:
            import requests
            response = requests.get(
                self.target_url,
                timeout=self.timeout,
                allow_redirects=True,
                verify=True,
            )
            return {
                "headers": dict(response.headers),
                "cookies": response.headers.get_list("Set-Cookie") if hasattr(response.headers, 'get_list') else [
                    f"{k}={v}" for k, v in response.cookies.items()
                ],
                "content": response.text,
                "status_code": response.status_code,
            }
        except ImportError:
            print("Warning: 'requests' library not installed. Install with: pip install requests")
            return None
        except Exception as e:
            print(f"Error fetching target: {e}")
            return None


def format_text_report(report: VerificationReport) -> str:
    """Format report as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("ASVS Verification Suite Report")
    lines.append("=" * 60)
    lines.append(f"Target: {report.target_url}")
    lines.append("")

    report.compute_summary()
    lines.append("Summary:")
    lines.append(f"  Total Tests: {report.summary['total']}")
    lines.append(f"  Passed: {report.summary['passed']}")
    lines.append(f"  Failed: {report.summary['failed']}")
    lines.append(f"  Skipped: {report.summary['skipped']}")
    lines.append(f"  Errors: {report.summary['errors']}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("Test Results:")
    lines.append("-" * 60)

    for test in report.tests:
        status_icon = {
            TestResult.PASS: "[PASS]",
            TestResult.FAIL: "[FAIL]",
            TestResult.SKIP: "[SKIP]",
            TestResult.ERROR: "[ERROR]",
        }.get(test.result, "[????]")

        lines.append(f"\n{status_icon} {test.name}")
        lines.append(f"  ASVS: {test.asvs_id}")
        lines.append(f"  Description: {test.description}")
        if test.details:
            lines.append(f"  Details: {test.details}")
        if test.recommendation:
            lines.append(f"  Recommendation: {test.recommendation}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def main(args=None):
    """Main entry point for the verification suite CLI."""
    parser = argparse.ArgumentParser(
        description="ASVS Verification Suite - Light DAST for Security Controls",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  asvs test https://example.com
  asvs test https://example.com --json
  asvs test --help

Supported checks:
  - Security headers (HSTS, CSP, X-Frame-Options, etc.)
  - Cookie security attributes (HttpOnly, Secure, SameSite)
  - CSRF protection mechanisms
  - Password field security attributes
        """,
    )

    parser.add_argument(
        "--target-url",
        required=True,
        help="Target URL to verify (e.g., https://example.com)",
    )

    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)",
    )

    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        default=True,
        help="Exit with code 1 if any tests fail (default: True)",
    )

    parser.add_argument(
        "--no-fail-on-issues",
        action="store_false",
        dest="fail_on_issues",
        help="Always exit with code 0 regardless of test results",
    )

    parser.add_argument(
        "--allow-local",
        action="store_true",
        help="Allow scanning of local/private network addresses (SSRF protection disabled)",
    )

    parsed = parser.parse_args(args)

    # Validate URL
    parsed_url = urlparse(parsed.target_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        print(f"Error: Invalid URL: {parsed.target_url}")
        return 1

    try:
        suite = VerificationSuite(parsed.target_url, timeout=parsed.timeout, allow_local=parsed.allow_local)
        report = suite.run_verification()
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    # Output report
    if parsed.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_text_report(report))

    # Exit code based on results
    if parsed.fail_on_issues and report.has_failures():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
