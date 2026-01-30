"""Discord application commands (slash commands) support."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

import discord
from discord import app_commands

LOGGER = logging.getLogger("accuralai.discord")


class SlashCommandRegistry:
    """Registry for Discord application commands (slash commands)."""

    def __init__(self) -> None:
        """Initialize slash command registry."""
        self._global_commands: Dict[str, app_commands.Command] = {}
        self._guild_commands: Dict[int, Dict[str, app_commands.Command]] = {}
        self._tree: Optional[app_commands.CommandTree] = None

    def set_tree(self, tree: app_commands.CommandTree) -> None:
        """Set the command tree for this registry."""
        self._tree = tree

    async def register_global_command(
        self,
        name: str,
        description: str,
        handler: Callable,
        *,
        nsfw: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Register a global slash command.

        Args:
            name: Command name (must be lowercase, no spaces)
            description: Command description
            handler: Async handler function (can take interaction and other params)
            nsfw: Whether command is NSFW
            **kwargs: Additional app_commands parameters
        """
        if not self._tree:
            raise RuntimeError("Command tree not initialized. Call set_tree() first.")

        # Use the handler directly if it's already a Command object
        if isinstance(handler, app_commands.Command):
            self._tree.add_command(handler)
            self._global_commands[name] = handler
            LOGGER.info(f"Registered global slash command: {name} (already a Command object)")
            return

        # Create a wrapper that preserves the handler signature
        import inspect
        import functools
        
        # Get the original handler signature
        sig = inspect.signature(handler)
        
        # Create wrapper function that matches the handler signature
        @functools.wraps(handler)
        async def cmd_wrapper(interaction: discord.Interaction, *args, **kwargs) -> None:
            try:
                # Call handler with interaction and any additional params
                result = await handler(interaction, *args, **kwargs)
                if not interaction.response.is_done():
                    if result:
                        if isinstance(result, discord.Embed):
                            await interaction.response.send_message(embed=result)
                        else:
                            # Split string results to respect Discord limits (max 3 messages)
                            from ..utils import split_discord_message
                            result_str = str(result)
                            chunks = split_discord_message(result_str, max_size=2000, max_messages=3)
                            if chunks:
                                # Send first chunk as response, rest as followups
                                await interaction.response.send_message(chunks[0])
                                for chunk in chunks[1:]:
                                    await interaction.followup.send(chunk)
                            else:
                                await interaction.response.send_message(result_str)
                    else:
                        await interaction.response.defer()
            except Exception as e:
                LOGGER.exception(f"Error in slash command {name}")
                if not interaction.response.is_done():
                    try:
                        await interaction.response.send_message(
                            f"❌ Error executing command: {str(e)}", ephemeral=True
                        )
                    except Exception:
                        # Response already sent, try followup
                        try:
                            await interaction.followup.send(
                                f"❌ Error executing command: {str(e)}", ephemeral=True
                            )
                        except Exception:
                            pass

        # Preserve the signature from the original handler
        cmd_wrapper.__signature__ = sig
        
        # Create command using Discord.py decorator pattern
        cmd_obj = app_commands.command(name=name, description=description, nsfw=nsfw, **kwargs)(cmd_wrapper)
        self._tree.add_command(cmd_obj)
        self._global_commands[name] = cmd_obj
        
        LOGGER.info(f"Registered global slash command: {name}")

    async def register_guild_command(
        self,
        guild_id: int,
        name: str,
        description: str,
        handler: Callable,
        *,
        nsfw: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Register a guild-specific slash command.

        Args:
            guild_id: Discord guild ID
            name: Command name (must be lowercase, no spaces)
            description: Command description
            handler: Async handler function
            nsfw: Whether command is NSFW
            **kwargs: Additional app_commands parameters
        """
        if not self._tree:
            raise RuntimeError("Command tree not initialized. Call set_tree() first.")

        guild = discord.Object(id=guild_id)

        @app_commands.command(name=name, description=description, nsfw=nsfw, **kwargs)
        async def cmd_wrapper(interaction: discord.Interaction) -> None:
            try:
                result = await handler(interaction)
                if not interaction.response.is_done():
                    if result:
                        if isinstance(result, str):
                            await interaction.response.send_message(result)
                        elif isinstance(result, discord.Embed):
                            await interaction.response.send_message(embed=result)
                        else:
                            await interaction.response.send_message(str(result))
                    else:
                        await interaction.response.defer()
            except Exception as e:
                LOGGER.exception(f"Error in guild slash command {name}")
                if not interaction.response.is_done():
                    try:
                        await interaction.response.send_message(
                            f"❌ Error executing command: {str(e)}", ephemeral=True
                        )
                    except Exception:
                        # Response already sent, try followup
                        try:
                            await interaction.followup.send(
                                f"❌ Error executing command: {str(e)}", ephemeral=True
                            )
                        except Exception:
                            pass

        self._tree.add_command(cmd_wrapper, guild=guild)
        if guild_id not in self._guild_commands:
            self._guild_commands[guild_id] = {}
        self._guild_commands[guild_id][name] = cmd_wrapper
        LOGGER.info(f"Registered guild slash command {name} for guild {guild_id}")

    async def sync_commands(
        self, *, guild: Optional[discord.Guild] = None, force: bool = False
    ) -> None:
        """
        Sync commands with Discord.

        Args:
            guild: Guild to sync commands for (None = sync global commands)
            force: Force sync even if commands haven't changed
        """
        if not self._tree:
            raise RuntimeError("Command tree not initialized.")

        try:
            if guild:
                synced = await self._tree.sync(guild=guild)
                LOGGER.info(
                    f"Synced {len(synced)} commands to guild {guild.id} ({guild.name})"
                )
            else:
                synced = await self._tree.sync()
                LOGGER.info(f"Synced {len(synced)} global commands")
        except Exception as e:
            LOGGER.error(f"Failed to sync commands: {e}", exc_info=True)

    def get_global_commands(self) -> Dict[str, app_commands.Command]:
        """Get all registered global commands."""
        return dict(self._global_commands)

    def get_guild_commands(self, guild_id: int) -> Dict[str, app_commands.Command]:
        """Get all registered commands for a guild."""
        return dict(self._guild_commands.get(guild_id, {}))

    async def unregister_global_command(self, name: str) -> None:
        """Unregister a global command."""
        if name in self._global_commands:
            if self._tree:
                self._tree.remove_command(name)
            del self._global_commands[name]
            LOGGER.info(f"Unregistered global slash command: {name}")

    async def unregister_guild_command(self, guild_id: int, name: str) -> None:
        """Unregister a guild-specific command."""
        if guild_id in self._guild_commands and name in self._guild_commands[guild_id]:
            if self._tree:
                guild = discord.Object(id=guild_id)
                self._tree.remove_command(name, guild=guild)
            del self._guild_commands[guild_id][name]
            LOGGER.info(f"Unregistered guild slash command {name} for guild {guild_id}")


def slash_command(
    name: str,
    description: str,
    *,
    guild_id: Optional[int] = None,
    nsfw: bool = False,
    **kwargs: Any,
):
    """
    Decorator for registering slash commands.

    Args:
        name: Command name
        description: Command description
        guild_id: Guild ID for guild-specific command (None for global)
        nsfw: Whether command is NSFW
        **kwargs: Additional app_commands parameters

    Example:
        @slash_command("ping", "Ping the bot")
        async def ping_handler(interaction: discord.Interaction):
            return "Pong!"
    """

    def decorator(func: Callable) -> Callable:
        func._slash_command_name = name
        func._slash_command_description = description
        func._slash_command_guild_id = guild_id
        func._slash_command_nsfw = nsfw
        func._slash_command_kwargs = kwargs
        return func

    return decorator

