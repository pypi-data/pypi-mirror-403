"""Tests for middleware components."""

import pytest
import time
from unittest.mock import MagicMock

from accuralai_discord.middleware.error_handler import ErrorHandler
from accuralai_discord.middleware.rate_limit import RateLimiter
from accuralai_core.contracts.errors import AccuralAIError
from discord.errors import RateLimited


@pytest.mark.anyio
async def test_rate_limiter_allows_requests() -> None:
    """Test rate limiter allows requests within limit."""
    limiter = RateLimiter(requests_per_minute=10)
    allowed, retry_after = await limiter.check_rate_limit("test:context")
    assert allowed is True
    assert retry_after is None


@pytest.mark.anyio
async def test_rate_limiter_blocks_excess() -> None:
    """Test rate limiter blocks requests exceeding limit."""
    limiter = RateLimiter(requests_per_minute=2)
    context = "test:context"

    # Make 2 requests (should be allowed)
    allowed1, _ = await limiter.check_rate_limit(context)
    allowed2, _ = await limiter.check_rate_limit(context)
    assert allowed1 is True
    assert allowed2 is True

    # Third request should be blocked
    allowed3, retry_after = await limiter.check_rate_limit(context)
    assert allowed3 is False
    assert retry_after is not None


@pytest.mark.anyio
async def test_rate_limiter_reset() -> None:
    """Test resetting rate limiter."""
    limiter = RateLimiter(requests_per_minute=1)
    context = "test:context"

    await limiter.check_rate_limit(context)
    limiter.reset(context)

    # Should be able to make another request after reset
    allowed, _ = await limiter.check_rate_limit(context)
    assert allowed is True


def test_error_handler_format_accuralai_error() -> None:
    """Test formatting AccuralAI errors."""
    error = AccuralAIError("Test error message")
    message = ErrorHandler.format_error(error)
    assert "AI service error" in message
    assert "Test error message" in message


def test_error_handler_format_rate_limit_error() -> None:
    """Test formatting rate limit errors."""
    error = RateLimited(MagicMock(), retry_after=5.0)
    message = ErrorHandler.format_error(error)
    assert "Rate limited" in message
    assert "5.0" in message


def test_error_handler_format_generic_error() -> None:
    """Test formatting generic errors."""
    error = ValueError("Something went wrong")
    message = ErrorHandler.format_error(error)
    assert "unexpected error" in message.lower()

