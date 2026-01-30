"""Tests for command system."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from accuralai_discord.commands.registry import CommandContext, CommandRegistry


@pytest.fixture
def mock_message() -> MagicMock:
    """Create a mock Discord message."""
    message = MagicMock()
    message.author = MagicMock()
    message.author.id = 123
    message.channel = MagicMock()
    message.channel.id = 456
    message.guild = MagicMock()
    message.guild.id = 789
    return message


@pytest.mark.anyio
async def test_register_command() -> None:
    """Test registering a command."""
    registry = CommandRegistry(prefix="/")
    handler = AsyncMock(return_value="response")

    registry.register("test", handler, "Test command")
    assert registry.get_handler("test") == handler


@pytest.mark.anyio
async def test_parse_command() -> None:
    """Test parsing command from message content."""
    registry = CommandRegistry(prefix="/")
    cmd_name, args = registry.parse_command("/test arg1 arg2")
    assert cmd_name == "test"
    assert args == ["arg1", "arg2"]


@pytest.mark.anyio
async def test_parse_command_no_prefix() -> None:
    """Test parsing non-command message."""
    registry = CommandRegistry(prefix="/")
    cmd_name, args = registry.parse_command("regular message")
    assert cmd_name is None
    assert args == []


@pytest.mark.anyio
async def test_get_all_commands() -> None:
    """Test getting all registered commands."""
    registry = CommandRegistry(prefix="/")
    registry.register("cmd1", AsyncMock(), "Description 1")
    registry.register("cmd2", AsyncMock(), "Description 2")

    commands = registry.get_all_commands()
    assert "cmd1" in commands
    assert "cmd2" in commands
    assert commands["cmd1"] == "Description 1"


@pytest.mark.anyio
async def test_command_context(mock_message: MagicMock) -> None:
    """Test CommandContext creation."""
    ctx = CommandContext(
        message=mock_message,
        args=["arg1", "arg2"],
        user=mock_message.author,
        channel=mock_message.channel,
        guild=mock_message.guild,
    )

    assert ctx.args == ["arg1", "arg2"]
    assert ctx.user == mock_message.author
    assert ctx.channel == mock_message.channel

