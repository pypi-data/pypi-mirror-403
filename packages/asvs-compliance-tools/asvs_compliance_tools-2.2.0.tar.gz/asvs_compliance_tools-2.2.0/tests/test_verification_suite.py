"""
Unit tests for the ASVS Verification Suite.
Tests security header, cookie, CSRF, and password policy checkers.
"""

import pytest
from tools.verification_suite import (
    SecurityHeaderChecker,
    CookieSecurityChecker,
    CSRFChecker,
    PasswordPolicyChecker,
    VerificationSuite,
    VerificationReport,
    SecurityTest,
    TestResult,
    UrlValidator,
    format_text_report,
)

class TestUrlValidator:
    def test_public_ip_allowed(self):
        assert UrlValidator.is_safe_url("https://8.8.8.8") is True

    def test_localhost_blocked(self):
        # Mocking socket resolution would be ideal, but for now we test logic
        # Assuming the environment resolves localhost to 127.0.0.1
        assert UrlValidator.is_safe_url("http://localhost") is False
        assert UrlValidator.is_safe_url("http://127.0.0.1") is False

    def test_allow_local_override(self):
        assert UrlValidator.is_safe_url("http://localhost", allow_local=True) is True


class TestSecurityHeaderChecker:
    """Tests for SecurityHeaderChecker class."""

    @pytest.fixture
    def checker(self):
        return SecurityHeaderChecker()

    def test_all_required_headers_present(self, checker):
        """Test that all required headers pass when present."""
        headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": "default-src 'self'",
        }
        results = checker.check_headers(headers)
        required_results = [r for r in results if r.asvs_id in ["V14.4.4", "V14.4.1", "V8.1.1", "V14.4.3"]]
        assert all(r.result == TestResult.PASS for r in required_results)

    def test_missing_hsts_header(self, checker):
        """Test that missing HSTS header fails."""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        }
        results = checker.check_headers(headers)
        hsts_result = next(r for r in results if "Strict-Transport-Security" in r.name)
        assert hsts_result.result == TestResult.FAIL

    def test_wrong_content_type_options_value(self, checker):
        """Test that wrong X-Content-Type-Options value fails."""
        headers = {
            "X-Content-Type-Options": "sniff",  # Wrong value
        }
        results = checker.check_headers(headers)
        result = next(r for r in results if "X-Content-Type-Options" in r.name)
        assert result.result == TestResult.FAIL

    def test_frame_options_sameorigin_passes(self, checker):
        """Test that SAMEORIGIN for X-Frame-Options passes."""
        headers = {
            "X-Frame-Options": "SAMEORIGIN",
        }
        results = checker.check_headers(headers)
        result = next(r for r in results if "X-Frame-Options" in r.name)
        assert result.result == TestResult.PASS

    def test_case_insensitive_header_lookup(self, checker):
        """Test that header lookup is case-insensitive."""
        headers = {
            "strict-transport-security": "max-age=31536000",  # lowercase
            "x-content-type-options": "nosniff",  # lowercase
        }
        results = checker.check_headers(headers)
        hsts_result = next(r for r in results if "Strict-Transport-Security" in r.name)
        assert hsts_result.result == TestResult.PASS

    def test_optional_headers_skip_when_missing(self, checker):
        """Test that missing optional headers return SKIP."""
        headers = {}
        results = checker.check_headers(headers)
        referrer_result = next(r for r in results if "Referrer-Policy" in r.name)
        assert referrer_result.result == TestResult.SKIP


class TestCookieSecurityChecker:
    """Tests for CookieSecurityChecker class."""

    @pytest.fixture
    def checker(self):
        return CookieSecurityChecker()

    def test_secure_cookie_all_attributes(self, checker):
        """Test cookie with all security attributes passes."""
        cookies = ["session=abc123; HttpOnly; Secure; SameSite=Strict"]
        results = checker.check_cookies(cookies)
        assert all(r.result == TestResult.PASS for r in results)

    def test_missing_httponly(self, checker):
        """Test cookie without HttpOnly fails."""
        cookies = ["session=abc123; Secure; SameSite=Strict"]
        results = checker.check_cookies(cookies)
        httponly_result = next(r for r in results if "HttpOnly" in r.name)
        assert httponly_result.result == TestResult.FAIL

    def test_missing_secure(self, checker):
        """Test cookie without Secure flag fails."""
        cookies = ["session=abc123; HttpOnly; SameSite=Strict"]
        results = checker.check_cookies(cookies)
        secure_result = next(r for r in results if "Secure" in r.name and "SameSite" not in r.name)
        assert secure_result.result == TestResult.FAIL

    def test_samesite_none_fails(self, checker):
        """Test SameSite=None fails (allows cross-site)."""
        cookies = ["session=abc123; HttpOnly; Secure; SameSite=None"]
        results = checker.check_cookies(cookies)
        samesite_result = next(r for r in results if "SameSite" in r.name)
        assert samesite_result.result == TestResult.FAIL

    def test_samesite_lax_passes(self, checker):
        """Test SameSite=Lax passes."""
        cookies = ["session=abc123; HttpOnly; Secure; SameSite=Lax"]
        results = checker.check_cookies(cookies)
        samesite_result = next(r for r in results if "SameSite" in r.name)
        assert samesite_result.result == TestResult.PASS

    def test_no_cookies_skips(self, checker):
        """Test that no cookies returns SKIP."""
        results = checker.check_cookies([])
        assert len(results) == 1
        assert results[0].result == TestResult.SKIP

    def test_multiple_cookies(self, checker):
        """Test multiple cookies are all checked."""
        cookies = [
            "session=abc; HttpOnly; Secure; SameSite=Strict",
            "prefs=xyz; HttpOnly; Secure; SameSite=Lax",
        ]
        results = checker.check_cookies(cookies)
        # 3 checks per cookie (HttpOnly, Secure, SameSite)
        assert len(results) == 6


class TestCSRFChecker:
    """Tests for CSRFChecker class."""

    @pytest.fixture
    def checker(self):
        return CSRFChecker()

    def test_csrf_token_in_form(self, checker):
        """Test detection of CSRF token in HTML form."""
        html = '''
        <form method="POST">
            <input type="hidden" name="csrf_token" value="abc123">
            <input type="submit">
        </form>
        '''
        result = checker.check_csrf_protection(html, [], {})
        assert result.result == TestResult.PASS

    def test_csrf_token_django_style(self, checker):
        """Test detection of Django-style CSRF token."""
        html = '''
        <form method="POST">
            <input type="hidden" name="csrfmiddlewaretoken" value="abc123">
        </form>
        '''
        result = checker.check_csrf_protection(html, [], {})
        assert result.result == TestResult.PASS

    def test_csrf_token_rails_style(self, checker):
        """Test detection of Rails-style authenticity token."""
        html = '''
        <form method="POST">
            <input type="hidden" name="authenticity_token" value="abc123">
        </form>
        '''
        result = checker.check_csrf_protection(html, [], {})
        assert result.result == TestResult.PASS

    def test_csrf_meta_tag(self, checker):
        """Test detection of CSRF token in meta tag."""
        html = '''
        <head>
            <meta name="csrf-token" content="abc123">
        </head>
        '''
        result = checker.check_csrf_protection(html, [], {})
        assert result.result == TestResult.PASS

    def test_csrf_cookie_present(self, checker):
        """Test detection of CSRF cookie."""
        html = "<html></html>"
        cookies = ["csrftoken=abc123; Path=/"]
        result = checker.check_csrf_protection(html, cookies, {})
        assert result.result == TestResult.PASS

    def test_xsrf_token_cookie(self, checker):
        """Test detection of XSRF-TOKEN cookie."""
        html = "<html></html>"
        cookies = ["XSRF-TOKEN=abc123; Path=/"]
        result = checker.check_csrf_protection(html, cookies, {})
        assert result.result == TestResult.PASS

    def test_no_csrf_protection_fails(self, checker):
        """Test that missing CSRF protection fails."""
        html = '''
        <form method="POST">
            <input type="text" name="username">
            <input type="submit">
        </form>
        '''
        result = checker.check_csrf_protection(html, [], {})
        assert result.result == TestResult.FAIL

    def test_csrf_header_reference(self, checker):
        """Test detection of CSRF header reference in JavaScript."""
        html = '''
        <script>
            headers: {'X-CSRF-Token': token}
        </script>
        '''
        result = checker.check_csrf_protection(html, [], {})
        assert result.result == TestResult.PASS


class TestPasswordPolicyChecker:
    """Tests for PasswordPolicyChecker class."""

    @pytest.fixture
    def checker(self):
        return PasswordPolicyChecker()

    def test_secure_password_field(self, checker):
        """Test password field with good security attributes."""
        html = '''
        <input type="password" name="password" minlength="12" 
               autocomplete="new-password" required>
        '''
        results = checker.check_password_fields(html)
        assert len(results) == 1
        assert results[0].result == TestResult.PASS

    def test_weak_minlength(self, checker):
        """Test password field with weak minlength fails."""
        html = '''
        <input type="password" name="password" minlength="6" 
               autocomplete="new-password">
        '''
        results = checker.check_password_fields(html)
        assert results[0].result == TestResult.FAIL
        assert "Minlength" in results[0].details

    def test_missing_autocomplete(self, checker):
        """Test password field without autocomplete attribute."""
        html = '''
        <input type="password" name="password" minlength="12">
        '''
        results = checker.check_password_fields(html)
        assert results[0].result == TestResult.FAIL
        assert "autocomplete" in results[0].details

    def test_no_password_fields_skips(self, checker):
        """Test that page without password fields returns SKIP."""
        html = '''
        <form>
            <input type="text" name="username">
            <input type="email" name="email">
        </form>
        '''
        results = checker.check_password_fields(html)
        assert len(results) == 1
        assert results[0].result == TestResult.SKIP

    def test_multiple_password_fields(self, checker):
        """Test multiple password fields are all checked."""
        html = '''
        <input type="password" name="password" minlength="12" autocomplete="new-password">
        <input type="password" name="confirm" minlength="12" autocomplete="new-password">
        '''
        results = checker.check_password_fields(html)
        assert len(results) == 2


class TestVerificationReport:
    """Tests for VerificationReport class."""

    def test_report_initialization(self):
        """Test report initializes correctly."""
        report = VerificationReport(target_url="https://example.com")
        assert report.target_url == "https://example.com"
        assert report.tests == []

    def test_add_test(self):
        """Test adding tests to report."""
        report = VerificationReport(target_url="https://example.com")
        test = SecurityTest(
            name="Test",
            asvs_id="V1.1",
            description="Test description",
            result=TestResult.PASS,
        )
        report.add_test(test)
        assert len(report.tests) == 1

    def test_compute_summary(self):
        """Test summary computation."""
        report = VerificationReport(target_url="https://example.com")
        report.add_test(SecurityTest("T1", "V1", "D1", TestResult.PASS))
        report.add_test(SecurityTest("T2", "V2", "D2", TestResult.PASS))
        report.add_test(SecurityTest("T3", "V3", "D3", TestResult.FAIL))
        report.add_test(SecurityTest("T4", "V4", "D4", TestResult.SKIP))

        report.compute_summary()
        assert report.summary["total"] == 4
        assert report.summary["passed"] == 2
        assert report.summary["failed"] == 1
        assert report.summary["skipped"] == 1

    def test_has_failures(self):
        """Test failure detection."""
        report = VerificationReport(target_url="https://example.com")
        report.add_test(SecurityTest("T1", "V1", "D1", TestResult.PASS))
        assert not report.has_failures()

        report.add_test(SecurityTest("T2", "V2", "D2", TestResult.FAIL))
        assert report.has_failures()

    def test_to_dict(self):
        """Test dictionary conversion."""
        report = VerificationReport(target_url="https://example.com")
        report.add_test(SecurityTest("Test", "V1.1", "Desc", TestResult.PASS, "Details"))

        data = report.to_dict()
        assert data["target_url"] == "https://example.com"
        assert len(data["tests"]) == 1
        assert data["tests"][0]["result"] == "pass"


class TestVerificationSuite:
    """Tests for VerificationSuite class."""

    def test_suite_initialization(self):
        """Test suite initializes correctly."""
        suite = VerificationSuite("https://example.com", timeout=5)
        assert suite.target_url == "https://example.com"
        assert suite.timeout == 5

    def test_run_verification_with_mock_data(self):
        """Test verification with mock response data."""
        suite = VerificationSuite("https://example.com")

        mock_response = {
            "headers": {
                "Strict-Transport-Security": "max-age=31536000",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Content-Security-Policy": "default-src 'self'",
            },
            "cookies": ["session=abc; HttpOnly; Secure; SameSite=Strict"],
            "content": '''
                <html>
                    <form method="POST">
                        <input type="hidden" name="csrf_token" value="xyz">
                        <input type="password" minlength="12" autocomplete="new-password">
                    </form>
                </html>
            ''',
        }

        report = suite.run_verification(response_data=mock_response)

        assert report.target_url == "https://example.com"
        assert len(report.tests) > 0
        # All required security controls are present
        report.compute_summary()
        assert report.summary["failed"] == 0

    def test_run_verification_insecure_target(self):
        """Test verification against insecure mock target."""
        # FIX: Added allow_local=True to bypass SSRF check for fake URL
        suite = VerificationSuite("https://insecure.example.com", allow_local=True)

        mock_response = {
            "headers": {},  # No security headers
            "cookies": ["session=abc"],  # No security attributes
            "content": '''
                <form method="POST">
                    <input type="password" name="pw">
                </form>
            ''',
        }

        report = suite.run_verification(response_data=mock_response)

        assert report.has_failures()
        report.compute_summary()
        assert report.summary["failed"] > 0


class TestTextReportFormat:
    """Tests for text report formatting."""

    def test_format_text_report(self):
        """Test text report formatting."""
        report = VerificationReport(target_url="https://example.com")
        report.add_test(SecurityTest(
            name="Test Header",
            asvs_id="V14.4.4",
            description="Test description",
            result=TestResult.PASS,
            details="Header present",
        ))
        report.add_test(SecurityTest(
            name="Test Cookie",
            asvs_id="V3.4.1",
            description="Cookie check",
            result=TestResult.FAIL,
            details="Missing Secure",
            recommendation="Add Secure flag",
        ))

        output = format_text_report(report)

        assert "ASVS Verification Suite Report" in output
        assert "https://example.com" in output
        assert "[PASS]" in output
        assert "[FAIL]" in output
        assert "Test Header" in output
        assert "Test Cookie" in output
        assert "Add Secure flag" in output


class TestIntegration:
    """Integration tests for the full verification flow."""

    def test_full_secure_site_verification(self):
        """Test full verification of a secure site mock."""
        suite = VerificationSuite("https://secure.example.com", allow_local=True)

        # Note: CSRF cookies intentionally don't have HttpOnly because
        # JavaScript needs to read them to send in headers.
        # Only session cookies should have HttpOnly.
        mock_response = {
            "headers": {
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": "camera=(), microphone=()",
            },
            "cookies": [
                # Session cookie: HttpOnly to prevent XSS access
                "session=abc123; HttpOnly; Secure; SameSite=Strict; Path=/",
            ],
            "content": '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="csrf-token" content="xyz789">
            </head>
            <body>
                <form method="POST" action="/login">
                    <input type="text" name="username" autocomplete="username">
                    <input type="password" name="password" minlength="12" 
                           autocomplete="current-password" required>
                    <input type="hidden" name="_csrf" value="xyz789">
                    <button type="submit">Login</button>
                </form>
            </body>
            </html>
            ''',
        }

        report = suite.run_verification(response_data=mock_response)
        report.compute_summary()

        # All checks should pass for a secure site
        assert report.summary["failed"] == 0, f"Failures: {[t.name for t in report.tests if t.result == TestResult.FAIL]}"

    def test_full_insecure_site_verification(self):
        """Test full verification of an insecure site mock."""
        suite = VerificationSuite("https://insecure.example.com", allow_local=True)

        mock_response = {
            "headers": {
                "Server": "Apache/2.4.1",  # Leaking server info
                # Missing all security headers
            },
            "cookies": [
                "PHPSESSID=abc123",  # No security attributes
            ],
            "content": '''
            <html>
            <body>
                <form method="POST" action="/login">
                    <input type="text" name="username">
                    <input type="password" name="password">
                    <button type="submit">Login</button>
                </form>
            </body>
            </html>
            ''',
        }

        report = suite.run_verification(response_data=mock_response)
        report.compute_summary()

        # Multiple checks should fail for an insecure site
        assert report.summary["failed"] >= 5, f"Expected at least 5 failures, got {report.summary['failed']}"
        assert report.has_failures()
