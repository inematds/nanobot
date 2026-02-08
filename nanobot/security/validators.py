"""Security validators for path traversal, SSRF, and input sanitization."""

import ipaddress
import re
import socket
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


def is_internal_ip(ip_str: str) -> bool:
    """
    Check if an IP address is internal (private, loopback, link-local, or reserved).

    Blocks:
    - Private ranges (10.x, 172.16-31.x, 192.168.x)
    - Loopback (127.x, ::1)
    - Link-local (169.254.x, fe80::)
    - AWS/cloud metadata (169.254.169.254)
    - Unspecified (0.0.0.0, ::)
    """
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # If we can't parse it, treat as internal (fail-secure)

    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


def resolve_dns_safe(hostname: str) -> list[str]:
    """
    Resolve a hostname to IP addresses safely.

    Returns list of resolved IPs. Returns empty list on failure.
    """
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        return list({r[4][0] for r in results})
    except (socket.gaierror, OSError):
        return []


def validate_url_ssrf(url: str) -> tuple[bool, str]:
    """
    Validate a URL for SSRF protection.

    Checks:
    - Only http/https allowed
    - Must have a valid domain
    - Resolved IPs must not be internal
    - Blocks common metadata endpoints
    """
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL: {e}"

    if parsed.scheme not in ("http", "https"):
        return False, f"Only http/https allowed, got '{parsed.scheme or 'none'}'"

    if not parsed.netloc:
        return False, "Missing domain"

    hostname = parsed.hostname
    if not hostname:
        return False, "Missing hostname"

    # Block obvious localhost variants
    blocked_hosts = {
        "localhost",
        "localhost.localdomain",
        "0.0.0.0",
        "[::1]",
        "[::0]",
        "metadata.google.internal",
    }
    if hostname.lower() in blocked_hosts:
        return False, f"Blocked host: {hostname}"

    # Resolve DNS and check all IPs
    ips = resolve_dns_safe(hostname)
    if not ips:
        return False, f"Could not resolve hostname: {hostname}"

    for ip in ips:
        if is_internal_ip(ip):
            return False, f"URL resolves to internal IP: {ip}"

    return True, ""


def resolve_path_secure(path: str, allowed_dir: Path) -> Path:
    """
    Securely resolve a path within an allowed directory.

    Uses Path.resolve() and relative_to() instead of string prefix matching.
    Rejects paths with '..' components before resolution.

    Args:
        path: The path to resolve.
        allowed_dir: The directory the path must stay within.

    Returns:
        The resolved Path.

    Raises:
        PermissionError: If the path escapes allowed_dir.
    """
    allowed = allowed_dir.resolve()

    # Reject raw '..' components before resolution
    raw = Path(path)
    for part in raw.parts:
        if part == "..":
            raise PermissionError(f"Path traversal detected: {path}")

    # Resolve relative paths against allowed_dir, not CWD
    if not raw.is_absolute():
        resolved = (allowed / raw).resolve()
    else:
        resolved = raw.expanduser().resolve()

    # Check that resolved path is within allowed directory
    try:
        resolved.relative_to(allowed)
    except ValueError:
        raise PermissionError(
            f"Path {path} resolves to {resolved}, which is outside allowed directory {allowed}"
        )

    # Also verify all parents are within allowed_dir
    current = resolved
    while current != allowed:
        parent = current.parent
        if parent == current:
            # Reached filesystem root without finding allowed_dir
            raise PermissionError(f"Path {path} is outside allowed directory {allowed}")
        current = parent

    return resolved


def safe_filename(name: str, max_length: int = 200) -> str:
    """
    Convert a string to a safe filename.

    - Normalizes Unicode (NFC)
    - Removes control characters
    - Replaces dangerous characters
    - Blocks '.' and '..' as filenames
    - Limits length

    Args:
        name: The raw filename.
        max_length: Maximum allowed length.

    Returns:
        A sanitized filename string.
    """
    if not name:
        return "_empty"

    # Normalize Unicode
    name = unicodedata.normalize("NFC", name)

    # Remove control characters
    name = "".join(ch for ch in name if unicodedata.category(ch)[0] != "C")

    # Replace unsafe characters (filesystem + shell)
    unsafe = '<>:"/\\|?*\x00'
    for char in unsafe:
        name = name.replace(char, "_")

    # Replace other potentially problematic characters
    name = re.sub(r"[\s]+", "_", name)  # Collapse whitespace to underscore

    # Strip leading/trailing dots and whitespace
    name = name.strip(". ")

    # Block '.' and '..'
    if name in (".", "..", ""):
        return "_safe"

    # Limit length
    if len(name) > max_length:
        name = name[:max_length]

    return name or "_safe"
