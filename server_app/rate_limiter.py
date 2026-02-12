"""Per-user rate limiting using a sliding window."""

import time


class RateLimiter:
    def __init__(self, max_messages: int = 5, window_seconds: float = 1.0):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self._timestamps: list[float] = []

    def is_allowed(self) -> bool:
        """Check if a message is allowed under the rate limit.

        Returns True if allowed (and records the timestamp).
        Returns False if rate limited.
        """
        now = time.monotonic()
        cutoff = now - self.window_seconds

        # Remove expired timestamps
        self._timestamps = [t for t in self._timestamps if t > cutoff]

        if len(self._timestamps) >= self.max_messages:
            return False

        self._timestamps.append(now)
        return True
