"""Token bucket rate limiter for nanobot operations."""

import time
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    """Token bucket rate limiter."""

    capacity: float
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)

    def __post_init__(self):
        self.tokens = self.capacity
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def consume(self, tokens: float = 1.0) -> bool:
        """Try to consume tokens. Returns True if allowed, False if rate limited."""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    @property
    def wait_time(self) -> float:
        """Seconds until at least 1 token is available."""
        self._refill()
        if self.tokens >= 1.0:
            return 0.0
        return (1.0 - self.tokens) / self.refill_rate


# Default rate limits per operation type (capacity, refill_rate per second)
DEFAULT_LIMITS: dict[str, tuple[float, float]] = {
    "channel_message": (10.0, 10.0 / 60),      # 10 per minute
    "tool_exec": (5.0, 5.0 / 60),              # 5 per minute
    "web_fetch": (20.0, 20.0 / 60),            # 20 per minute
    "file_write": (30.0, 30.0 / 60),           # 30 per minute
    "subagent_spawn": (3.0, 3.0 / 300),        # 3 per 5 minutes
    "cron_job": (10.0, 10.0 / 3600),           # 10 per hour
}


class RateLimiter:
    """Per-session, per-operation rate limiter."""

    def __init__(self, limits: dict[str, tuple[float, float]] | None = None):
        self._limits = limits or DEFAULT_LIMITS
        # Nested: session_key -> operation -> TokenBucket
        self._buckets: dict[str, dict[str, TokenBucket]] = {}

    def _get_bucket(self, session_key: str, operation: str) -> TokenBucket:
        if session_key not in self._buckets:
            self._buckets[session_key] = {}
        session_buckets = self._buckets[session_key]

        if operation not in session_buckets:
            capacity, rate = self._limits.get(operation, (100.0, 100.0 / 60))
            session_buckets[operation] = TokenBucket(capacity=capacity, refill_rate=rate)

        return session_buckets[operation]

    def check(self, session_key: str, operation: str) -> bool:
        """Check if an operation is allowed. Returns True if allowed."""
        bucket = self._get_bucket(session_key, operation)
        return bucket.consume()

    def wait_time(self, session_key: str, operation: str) -> float:
        """Get seconds until the next operation would be allowed."""
        bucket = self._get_bucket(session_key, operation)
        return bucket.wait_time

    def get_limit_message(self, operation: str) -> str:
        """Get a user-friendly rate limit exceeded message."""
        capacity, rate = self._limits.get(operation, (100.0, 100.0 / 60))
        period = capacity / rate if rate > 0 else 60
        if period >= 3600:
            period_str = f"{period / 3600:.0f} hour(s)"
        elif period >= 60:
            period_str = f"{period / 60:.0f} minute(s)"
        else:
            period_str = f"{period:.0f} second(s)"
        return f"Rate limit exceeded for {operation}: max {capacity:.0f} per {period_str}. Please wait."

    def cleanup_old_sessions(self, max_sessions: int = 1000) -> None:
        """Remove oldest sessions if over limit."""
        if len(self._buckets) <= max_sessions:
            return
        # Simple eviction: remove half
        keys = list(self._buckets.keys())
        for key in keys[: len(keys) // 2]:
            del self._buckets[key]
