"""Error and output sanitization to prevent credential leakage."""

import re

# Patterns that match sensitive data in error messages and outputs
_SENSITIVE_PATTERNS = [
    # API keys and tokens (generic patterns)
    (re.compile(r"(sk-[a-zA-Z0-9]{20,})"), "[REDACTED_API_KEY]"),
    (re.compile(r"(key-[a-zA-Z0-9]{20,})"), "[REDACTED_API_KEY]"),
    (re.compile(r"(token[=:\s]+['\"]?[a-zA-Z0-9_\-]{20,}['\"]?)"), "[REDACTED_TOKEN]"),
    (re.compile(r"(Bearer\s+[a-zA-Z0-9_\-\.]{20,})"), "Bearer [REDACTED]"),
    (re.compile(r"(X-Subscription-Token[=:\s]+['\"]?[a-zA-Z0-9_\-]{10,}['\"]?)"), "X-Subscription-Token: [REDACTED]"),
    # AWS-style keys
    (re.compile(r"(AKIA[0-9A-Z]{16})"), "[REDACTED_AWS_KEY]"),
    # Common secret patterns
    (re.compile(r"(api_key[=:\s]+['\"]?[a-zA-Z0-9_\-]{10,}['\"]?)", re.I), "[REDACTED_API_KEY]"),
    (re.compile(r"(api_secret[=:\s]+['\"]?[a-zA-Z0-9_\-]{10,}['\"]?)", re.I), "[REDACTED_SECRET]"),
    (re.compile(r"(password[=:\s]+['\"]?[^\s'\"]{6,}['\"]?)", re.I), "[REDACTED_PASSWORD]"),
]


def sanitize_error(error: str | Exception) -> str:
    """
    Sanitize an error message by removing sensitive data.

    Strips API keys, tokens, passwords, and other secrets from error text.
    """
    text = str(error)
    for pattern, replacement in _SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def sanitize_tool_result(result: str, max_length: int = 50000) -> str:
    """
    Sanitize a tool execution result.

    - Removes sensitive patterns
    - Truncates to max_length
    """
    result = sanitize_error(result)

    if len(result) > max_length:
        result = result[:max_length] + f"\n... (truncated, {len(result) - max_length} more chars)"

    return result
