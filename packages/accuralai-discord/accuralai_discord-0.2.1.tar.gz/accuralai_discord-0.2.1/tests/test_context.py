"""Tests for context management."""

import pytest

from accuralai_discord.context import extract_context_from_message, generate_context_key


def test_generate_context_key_per_channel() -> None:
    """Test per-channel context key generation."""
    key = generate_context_key("per-channel", guild_id=123, channel_id=456)
    assert key == "discord:guild:123:channel:456"


def test_generate_context_key_per_user() -> None:
    """Test per-user context key generation."""
    key = generate_context_key(
        "per-user", guild_id=123, channel_id=456, user_id=789
    )
    assert key == "discord:guild:123:user:789"


def test_generate_context_key_per_thread() -> None:
    """Test per-thread context key generation."""
    key = generate_context_key(
        "per-thread", guild_id=123, channel_id=456, thread_id=999
    )
    assert key == "discord:guild:123:thread:999"


def test_generate_context_key_per_channel_user() -> None:
    """Test per-channel-user context key generation."""
    key = generate_context_key(
        "per-channel-user",
        guild_id=123,
        channel_id=456,
        user_id=789,
    )
    assert key == "discord:guild:123:channel:456:user:789"


def test_generate_context_key_per_user_requires_user_id() -> None:
    """Test that per-user scope requires user_id."""
    with pytest.raises(ValueError, match="user_id required"):
        generate_context_key("per-user", guild_id=123, channel_id=456)


def test_generate_context_key_dm_per_user() -> None:
    """Test DM context key for per-user scope."""
    key = generate_context_key("per-user", guild_id=None, channel_id=456)
    assert key == "discord:dm:user:456"


def test_generate_context_key_dm_per_channel() -> None:
    """Test DM context key for per-channel scope."""
    key = generate_context_key("per-channel", guild_id=None, channel_id=456)
    assert key == "discord:dm:channel:456"

