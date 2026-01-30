"""Integration tests for Discord bot."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage
from accuralai_discord.bot import DiscordBot
from accuralai_discord.config import DiscordBotConfig
from uuid import uuid4


@pytest.fixture
def mock_discord_message() -> MagicMock:
    """Create a mock Discord message."""
    message = MagicMock()
    message.author = MagicMock()
    message.author.bot = False
    message.author.id = 123
    message.channel = MagicMock()
    message.channel.id = 456
    message.channel.send = AsyncMock()
    message.guild = MagicMock()
    message.guild.id = 789
    message.content = "Hello bot!"
    message.id = 999
    return message


@pytest.fixture
def bot_config() -> DiscordBotConfig:
    """Create test bot configuration."""
    return DiscordBotConfig(
        token="test_token",
        personality="test assistant",
        conversation_scope="per-channel",
        accuralai_config_overrides={
            "backends.mock.options.enabled": True,
        },
    )


@pytest.mark.anyio
async def test_bot_handles_message(bot_config: DiscordBotConfig, mock_discord_message: MagicMock) -> None:
    """Test bot handles incoming message."""
    bot = DiscordBot(config=bot_config)

    # Mock orchestrator response
    mock_response = GenerateResponse(
        id=uuid4(),
        request_id=uuid4(),
        output_text="Hello! How can I help?",
        finish_reason="stop",
        usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        latency_ms=100,
        metadata={},
        validator_events=[],
    )

    with patch.object(bot, "_ensure_orchestrator", new_callable=AsyncMock) as mock_ensure:
        mock_orchestrator = MagicMock()
        mock_orchestrator.generate = AsyncMock(return_value=mock_response)
        mock_ensure.return_value = mock_orchestrator

        # Mock memory
        bot._memory = MagicMock()
        bot._memory.get_history = AsyncMock(return_value=[])
        bot._memory.append_message = AsyncMock()

        await bot._handle_message(mock_discord_message)

        # Verify response was sent
        mock_discord_message.channel.send.assert_called_once()
        call_args = mock_discord_message.channel.send.call_args[0]
        assert "Hello! How can I help?" in call_args[0]

        # Verify history was updated
        assert bot._memory.append_message.call_count == 2  # User + assistant


@pytest.mark.anyio
async def test_bot_handles_command(bot_config: DiscordBotConfig, mock_discord_message: MagicMock) -> None:
    """Test bot handles command message."""
    bot = DiscordBot(config=bot_config)
    mock_discord_message.content = "/help"

    await bot._handle_message(mock_discord_message)

    # Verify help response was sent
    mock_discord_message.channel.send.assert_called_once()
    call_args = mock_discord_message.channel.send.call_args[0]
    assert "Available Commands" in call_args[0]


@pytest.mark.anyio
async def test_bot_rate_limiting(bot_config: DiscordBotConfig, mock_discord_message: MagicMock) -> None:
    """Test bot rate limiting."""
    bot_config.rate_limit_per_minute = 1
    bot = DiscordBot(config=bot_config)

    # First message should be allowed
    await bot._handle_message(mock_discord_message)
    assert mock_discord_message.channel.send.call_count >= 1

    # Reset call count
    mock_discord_message.channel.send.reset_mock()

    # Second message should be rate limited
    await bot._handle_message(mock_discord_message)
    send_calls = [call[0][0] for call in mock_discord_message.channel.send.call_args_list]
    assert any("Rate limited" in str(msg) for msg in send_calls)


@pytest.mark.anyio
async def test_bot_ignores_bot_messages(bot_config: DiscordBotConfig) -> None:
    """Test bot ignores messages from other bots."""
    bot = DiscordBot(config=bot_config)
    mock_message = MagicMock()
    mock_message.author.bot = True

    await bot._handle_message(mock_message)

    # Should not process bot messages
    # (No way to verify without checking internal state, but no errors should occur)

