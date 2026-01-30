"""Command system for Discord bot."""

from .builtin import BuiltinCommands
from .registry import CommandRegistry, CommandHandler, CommandContext
from .slash import SlashCommandRegistry, slash_command

__all__ = [
    "CommandRegistry",
    "CommandHandler",
    "CommandContext",
    "BuiltinCommands",
    "SlashCommandRegistry",
    "slash_command",
]

