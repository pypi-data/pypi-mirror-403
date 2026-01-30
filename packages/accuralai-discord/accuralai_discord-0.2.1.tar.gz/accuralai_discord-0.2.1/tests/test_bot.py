"""Tests for DiscordBot class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from accuralai_discord.bot import DiscordBot
from accuralai_discord.config import DiscordBotConfig


@pytest.fixture
def bot_config() -> DiscordBotConfig:
    """Create a test bot configuration."""
    return DiscordBotConfig(
        token="test_token",
        personality="test assistant",
        conversation_scope="per-channel",
    )


def test_bot_initialization(bot_config: DiscordBotConfig) -> None:
    """Test bot initialization."""
    bot = DiscordBot(config=bot_config)
    assert bot._config == bot_config
    assert bot._command_registry is not None
    assert bot._rate_limiter is not None


def test_bot_add_command(bot_config: DiscordBotConfig) -> None:
    """Test adding custom command."""
    bot = DiscordBot(config=bot_config)
    handler = AsyncMock(return_value="response")

    bot.add_command("test", handler, "Test command")
    assert bot._command_registry.get_handler("test") == handler


def test_bot_command_decorator(bot_config: DiscordBotConfig) -> None:
    """Test command decorator."""
    bot = DiscordBot(config=bot_config)

    @bot.command("test", description="Test command")
    async def test_handler(ctx):
        return "response"

    assert bot._command_registry.get_handler("test") is not None


def test_bot_get_orchestrator_not_initialized(bot_config: DiscordBotConfig) -> None:
    """Test getting orchestrator before initialization."""
    bot = DiscordBot(config=bot_config)
    assert bot.get_orchestrator() is None


@pytest.mark.anyio
async def test_bot_preprocess_hook(bot_config: DiscordBotConfig) -> None:
    """Test preprocess hook registration."""
    bot = DiscordBot(config=bot_config)
    hook_called = False

    @bot.on_message_preprocess
    async def preprocess(message, context):
        nonlocal hook_called
        hook_called = True
        return "modified"

    assert len(bot._preprocess_hooks) == 1


@pytest.mark.anyio
async def test_bot_postprocess_hook(bot_config: DiscordBotConfig) -> None:
    """Test postprocess hook registration."""
    bot = DiscordBot(config=bot_config)

    @bot.on_message_postprocess
    async def postprocess(response, message, context):
        return f"modified: {response}"

    assert len(bot._postprocess_hooks) == 1

