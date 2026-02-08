"""Tests for rate limiting."""

import time
import pytest

from nanobot.security.ratelimit import TokenBucket, RateLimiter


class TestTokenBucket:
    """Test token bucket algorithm."""

    def test_initial_capacity(self):
        bucket = TokenBucket(capacity=5.0, refill_rate=1.0)
        assert bucket.consume() is True

    def test_consume_all(self):
        bucket = TokenBucket(capacity=3.0, refill_rate=0.0)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False  # Depleted

    def test_refill(self):
        bucket = TokenBucket(capacity=1.0, refill_rate=100.0)  # Very fast refill
        assert bucket.consume() is True
        assert bucket.consume() is False  # Depleted
        time.sleep(0.02)  # Wait for refill
        assert bucket.consume() is True  # Should have refilled

    def test_no_exceed_capacity(self):
        bucket = TokenBucket(capacity=2.0, refill_rate=100.0)
        time.sleep(0.1)  # Wait for lots of refill
        # Should still only have capacity tokens
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False

    def test_wait_time_when_empty(self):
        bucket = TokenBucket(capacity=1.0, refill_rate=1.0)
        bucket.consume()  # Deplete
        wait = bucket.wait_time
        assert wait > 0

    def test_wait_time_when_available(self):
        bucket = TokenBucket(capacity=5.0, refill_rate=1.0)
        wait = bucket.wait_time
        assert wait == 0.0


class TestRateLimiter:
    """Test per-session rate limiter."""

    def test_allows_under_limit(self):
        limiter = RateLimiter({"test_op": (5.0, 5.0 / 60)})
        assert limiter.check("session1", "test_op") is True

    def test_blocks_over_limit(self):
        limiter = RateLimiter({"test_op": (2.0, 0.0)})  # 2 tokens, no refill
        assert limiter.check("session1", "test_op") is True
        assert limiter.check("session1", "test_op") is True
        assert limiter.check("session1", "test_op") is False  # Blocked

    def test_separate_sessions(self):
        limiter = RateLimiter({"test_op": (1.0, 0.0)})
        assert limiter.check("session1", "test_op") is True
        assert limiter.check("session1", "test_op") is False  # Session 1 blocked
        assert limiter.check("session2", "test_op") is True  # Session 2 OK

    def test_separate_operations(self):
        limiter = RateLimiter({
            "op_a": (1.0, 0.0),
            "op_b": (1.0, 0.0),
        })
        assert limiter.check("session1", "op_a") is True
        assert limiter.check("session1", "op_a") is False  # op_a blocked
        assert limiter.check("session1", "op_b") is True  # op_b still OK

    def test_limit_message(self):
        limiter = RateLimiter({"test_op": (10.0, 10.0 / 60)})
        msg = limiter.get_limit_message("test_op")
        assert "rate limit" in msg.lower()
        assert "10" in msg

    def test_unknown_operation_uses_default(self):
        limiter = RateLimiter({"known_op": (1.0, 0.0)})
        # Unknown operation should still work with generous default
        assert limiter.check("session1", "unknown_op") is True

    def test_cleanup_old_sessions(self):
        limiter = RateLimiter({"op": (1.0, 0.0)})
        # Create many sessions
        for i in range(200):
            limiter.check(f"session_{i}", "op")
        limiter.cleanup_old_sessions(max_sessions=100)
        assert len(limiter._buckets) <= 100
