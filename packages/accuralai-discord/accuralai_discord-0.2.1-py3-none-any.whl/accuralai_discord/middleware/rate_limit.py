"""Rate limiting middleware."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict

# Rate limiting is handled internally, no Discord import needed

LOGGER = logging.getLogger("accuralai.discord")


@dataclass
class RateLimitWindow:
    """Tracks rate limit window for a context."""

    requests: list[float] = field(default_factory=list)
    limit: int = 20
    window_seconds: int = 60

    def check(self) -> tuple[bool, float | None]:
        """
        Check if request is allowed.

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        now = time.time()
        # Remove requests outside window
        cutoff = now - self.window_seconds
        self.requests = [req_time for req_time in self.requests if req_time > cutoff]

        if len(self.requests) >= self.limit:
            # Calculate retry after
            oldest = min(self.requests)
            retry_after = self.window_seconds - (now - oldest)
            LOGGER.debug(
                f"Rate limit exceeded: {len(self.requests)}/{self.limit} requests, "
                f"retry after {retry_after:.1f}s"
            )
            return False, max(0, retry_after)

        self.requests.append(now)
        LOGGER.debug(f"Rate limit check passed: {len(self.requests)}/{self.limit} requests")
        return True, None


class RateLimiter:
    """Rate limiter using sliding window algorithm."""

    def __init__(self, requests_per_minute: int = 20) -> None:
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute per context
        """
        self._requests_per_minute = requests_per_minute
        self._windows: Dict[str, RateLimitWindow] = defaultdict(
            lambda: RateLimitWindow(
                limit=requests_per_minute,
                window_seconds=60,
            )
        )

    async def check_rate_limit(self, context_key: str) -> tuple[bool, float | None]:
        """
        Check if request is allowed for context.

        Args:
            context_key: Context key for rate limiting

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        window = self._windows[context_key]
        return window.check()

    def reset(self, context_key: str | None = None) -> None:
        """
        Reset rate limit for a context or all contexts.

        Args:
            context_key: Context to reset (None = reset all)
        """
        if context_key is None:
            self._windows.clear()
        else:
            self._windows.pop(context_key, None)

