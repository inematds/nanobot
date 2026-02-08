"""Tests for SSRF prevention in web tools."""

import pytest

from nanobot.security.validators import validate_url_ssrf, is_internal_ip


class TestSSRFValidation:
    """Test SSRF URL validation."""

    def test_public_url_allowed(self):
        ok, msg = validate_url_ssrf("https://www.google.com")
        assert ok is True, f"Public URL should be allowed: {msg}"

    def test_http_allowed(self):
        ok, msg = validate_url_ssrf("http://www.example.com")
        assert ok is True, f"HTTP should be allowed: {msg}"

    def test_ftp_blocked(self):
        ok, _ = validate_url_ssrf("ftp://files.example.com/doc")
        assert ok is False

    def test_file_scheme_blocked(self):
        ok, _ = validate_url_ssrf("file:///etc/passwd")
        assert ok is False

    def test_no_scheme_blocked(self):
        ok, _ = validate_url_ssrf("example.com")
        assert ok is False

    def test_empty_url_blocked(self):
        ok, _ = validate_url_ssrf("")
        assert ok is False


class TestSSRFLocalhostBlocking:
    """Test that localhost variants are blocked."""

    def test_localhost_string(self):
        ok, _ = validate_url_ssrf("http://localhost/admin")
        assert ok is False

    def test_localhost_localdomain(self):
        ok, _ = validate_url_ssrf("http://localhost.localdomain/")
        assert ok is False

    def test_ipv4_loopback(self):
        ok, _ = validate_url_ssrf("http://127.0.0.1/")
        assert ok is False

    def test_ipv6_loopback(self):
        ok, _ = validate_url_ssrf("http://[::1]/")
        assert ok is False

    def test_zero_ip(self):
        ok, _ = validate_url_ssrf("http://0.0.0.0/")
        assert ok is False


class TestSSRFInternalIPBlocking:
    """Test that internal/cloud metadata IPs are blocked."""

    def test_aws_metadata(self):
        ok, _ = validate_url_ssrf("http://169.254.169.254/latest/meta-data/")
        assert ok is False

    def test_private_10_range(self):
        assert is_internal_ip("10.0.0.1") is True

    def test_private_172_range(self):
        assert is_internal_ip("172.16.0.1") is True

    def test_private_192_range(self):
        assert is_internal_ip("192.168.0.1") is True

    def test_google_metadata(self):
        ok, _ = validate_url_ssrf("http://metadata.google.internal/")
        assert ok is False


class TestSSRFPublicIPsAllowed:
    """Test that legitimate public IPs are not blocked."""

    def test_google_dns(self):
        assert is_internal_ip("8.8.8.8") is False

    def test_cloudflare_dns(self):
        assert is_internal_ip("1.1.1.1") is False

    def test_public_ip(self):
        assert is_internal_ip("93.184.216.34") is False
