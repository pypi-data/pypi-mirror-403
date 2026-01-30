"""Command registry and routing system."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

import discord


@dataclass
class CommandContext:
    """Context passed to command handlers."""

    message: discord.Message | None  # None for slash commands
    args: list[str]
    user: discord.User | discord.Member
    channel: discord.TextChannel | discord.DMChannel | discord.Thread | None  # None for some edge cases
    guild: discord.Guild | None


CommandHandler = Callable[[CommandContext], Awaitable[str | None]]


class CommandRegistry:
    """Registry for bot commands."""

    def __init__(self, prefix: str = "/") -> None:
        """
        Initialize command registry.

        Args:
            prefix: Command prefix (e.g., '/', '!')
        """
        self._prefix = prefix
        self._commands: Dict[str, CommandHandler] = {}
        self._descriptions: Dict[str, str] = {}

    def register(
        self,
        name: str,
        handler: CommandHandler,
        description: str | None = None,
    ) -> None:
        """
        Register a command handler.

        Args:
            name: Command name (with or without prefix)
            handler: Async handler function
            description: Optional command description
        """
        # Normalize command name
        name = name.lstrip(self._prefix)
        self._commands[name] = handler
        if description:
            self._descriptions[name] = description

    def unregister(self, name: str) -> None:
        """
        Unregister a command.

        Args:
            name: Command name
        """
        name = name.lstrip(self._prefix)
        self._commands.pop(name, None)
        self._descriptions.pop(name, None)

    def get_handler(self, name: str) -> Optional[CommandHandler]:
        """
        Get handler for a command.

        Args:
            name: Command name

        Returns:
            Command handler or None
        """
        name = name.lstrip(self._prefix)
        return self._commands.get(name)

    def parse_command(self, content: str) -> tuple[str | None, list[str]]:
        """
        Parse command from message content.

        Args:
            content: Message content

        Returns:
            Tuple of (command_name, args) or (None, []) if not a command
        """
        content = content.strip()
        if not content.startswith(self._prefix):
            return None, []

        parts = content[len(self._prefix) :].split(None, 1)
        command_name = parts[0] if parts else None
        args = parts[1].split() if len(parts) > 1 else []

        return command_name, args

    def get_all_commands(self) -> Dict[str, str]:
        """
        Get all registered commands with descriptions.

        Returns:
            Dict mapping command names to descriptions
        """
        return dict(self._descriptions)

    @property
    def prefix(self) -> str:
        """Get command prefix."""
        return self._prefix

