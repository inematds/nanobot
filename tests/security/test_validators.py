"""Tests for security validators: paths, IPs, filenames."""

import pytest
from pathlib import Path

from nanobot.security.validators import (
    is_internal_ip,
    resolve_path_secure,
    safe_filename,
    validate_url_ssrf,
)


# ========================================================================
# is_internal_ip
# ========================================================================


class TestIsInternalIP:
    """Test internal IP detection."""

    def test_loopback_v4(self):
        assert is_internal_ip("127.0.0.1") is True

    def test_loopback_v6(self):
        assert is_internal_ip("::1") is True

    def test_private_10(self):
        assert is_internal_ip("10.0.0.1") is True

    def test_private_172(self):
        assert is_internal_ip("172.16.0.1") is True

    def test_private_192(self):
        assert is_internal_ip("192.168.1.1") is True

    def test_link_local(self):
        assert is_internal_ip("169.254.169.254") is True

    def test_unspecified(self):
        assert is_internal_ip("0.0.0.0") is True

    def test_public_ip(self):
        assert is_internal_ip("8.8.8.8") is False

    def test_public_ip_cloudflare(self):
        assert is_internal_ip("1.1.1.1") is False

    def test_invalid_ip_treated_as_internal(self):
        assert is_internal_ip("not-an-ip") is True

    def test_multicast(self):
        assert is_internal_ip("224.0.0.1") is True


# ========================================================================
# resolve_path_secure
# ========================================================================


class TestResolvePathSecure:
    """Test secure path resolution."""

    def test_simple_relative_path(self, tmp_path):
        (tmp_path / "file.txt").touch()
        result = resolve_path_secure("file.txt", tmp_path)
        assert result == tmp_path / "file.txt"

    def test_subdirectory(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "file.txt").touch()
        result = resolve_path_secure("sub/file.txt", tmp_path)
        assert result == sub / "file.txt"

    def test_traversal_blocked(self, tmp_path):
        with pytest.raises(PermissionError, match="traversal"):
            resolve_path_secure("../etc/passwd", tmp_path)

    def test_absolute_path_outside_blocked(self, tmp_path):
        with pytest.raises(PermissionError, match="outside"):
            resolve_path_secure("/etc/passwd", tmp_path)

    def test_dotdot_in_middle_blocked(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        with pytest.raises(PermissionError, match="traversal"):
            resolve_path_secure("sub/../../etc/passwd", tmp_path)

    def test_allowed_dir_itself(self, tmp_path):
        result = resolve_path_secure(".", tmp_path)
        assert result == tmp_path


# ========================================================================
# safe_filename
# ========================================================================


class TestSafeFilename:
    """Test filename sanitization."""

    def test_normal_name(self):
        assert safe_filename("hello.txt") == "hello.txt"

    def test_dangerous_chars_replaced(self):
        result = safe_filename('file<>:"/\\|?*.txt')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_dot_blocked(self):
        assert safe_filename(".") == "_safe"

    def test_dotdot_blocked(self):
        assert safe_filename("..") == "_safe"

    def test_empty_string(self):
        assert safe_filename("") == "_empty"

    def test_length_limit(self):
        long_name = "a" * 300
        result = safe_filename(long_name, max_length=50)
        assert len(result) <= 50

    def test_unicode_normalized(self):
        # e-acute as composed vs decomposed
        result = safe_filename("caf\u00e9")
        assert "caf" in result

    def test_whitespace_collapsed(self):
        result = safe_filename("hello   world   test")
        assert "   " not in result


# ========================================================================
# validate_url_ssrf
# ========================================================================


class TestValidateUrlSSRF:
    """Test SSRF URL validation."""

    def test_valid_https(self):
        ok, _ = validate_url_ssrf("https://example.com/page")
        assert ok is True

    def test_ftp_blocked(self):
        ok, msg = validate_url_ssrf("ftp://example.com/file")
        assert ok is False
        assert "http" in msg.lower()

    def test_missing_scheme(self):
        ok, _ = validate_url_ssrf("example.com")
        assert ok is False

    def test_localhost_blocked(self):
        ok, msg = validate_url_ssrf("http://localhost/admin")
        assert ok is False
        assert "localhost" in msg.lower() or "Blocked" in msg

    def test_127_blocked(self):
        ok, msg = validate_url_ssrf("http://127.0.0.1/")
        assert ok is False

    def test_metadata_ip_blocked(self):
        ok, msg = validate_url_ssrf("http://169.254.169.254/latest/meta-data/")
        assert ok is False

    def test_ipv6_loopback_blocked(self):
        ok, msg = validate_url_ssrf("http://[::1]/")
        assert ok is False

    def test_empty_url(self):
        ok, _ = validate_url_ssrf("")
        assert ok is False

    def test_missing_domain(self):
        ok, _ = validate_url_ssrf("http://")
        assert ok is False
