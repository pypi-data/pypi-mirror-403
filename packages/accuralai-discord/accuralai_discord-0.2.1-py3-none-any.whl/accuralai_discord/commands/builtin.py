"""Built-in command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import CommandContext, CommandHandler

if TYPE_CHECKING:
    from ..bot import DiscordBot


class BuiltinCommands:
    """Built-in command handlers for Discord bot."""

    def __init__(self, bot: "DiscordBot") -> None:
        """
        Initialize built-in commands.

        Args:
            bot: DiscordBot instance
        """
        self._bot = bot

    async def help_command(self, ctx: CommandContext) -> str:
        """Handle /help command."""
        commands = self._bot._command_registry.get_all_commands()
        if not commands:
            return "No commands available."

        lines = ["**Available Commands:**"]
        for cmd_name, description in sorted(commands.items()):
            prefix = self._bot._command_registry.prefix
            lines.append(f"`{prefix}{cmd_name}` - {description}")

        return "\n".join(lines)

    async def reset_command(self, ctx: CommandContext) -> str:
        """Handle /reset command."""
        from ..context import extract_context_from_message, generate_context_key
        import discord
        
        # Handle both message-based (prefix) and interaction-based (slash) commands
        if ctx.message:
            context_key, _ = extract_context_from_message(
                ctx.message,
                self._bot._config.conversation_scope,
            )
        else:
            # Extract context from interaction (slash command)
            guild_id = ctx.guild.id if ctx.guild else None
            channel_id = ctx.channel.id if ctx.channel else None
            user_id = ctx.user.id if ctx.user else None
            thread_id = None
            
            # Check if channel is a thread
            if ctx.channel and isinstance(ctx.channel, discord.Thread):
                thread_id = ctx.channel.id
            
            if channel_id is None:
                return "❌ Error: Could not determine channel context."
            
            context_key = generate_context_key(
                scope=self._bot._config.conversation_scope,
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                thread_id=thread_id,
            )
        
        # Check if memory is initialized
        if self._bot._memory is None:
            response = "⚠️ Conversation memory not initialized yet. History will be cleared once the bot is fully ready."
        else:
            await self._bot._memory.clear_history(context_key)
            response = "Conversation history cleared!"
        
        # Sync commands to guild if in a guild
        if ctx.guild and self._bot._slash_registry:
            try:
                await self._bot.sync_slash_commands(guild=ctx.guild)
                response += "\n✅ Commands synced to this guild!"
            except Exception as e:
                # Log error but don't fail the reset command
                import logging
                logger = logging.getLogger("accuralai.discord")
                error_msg = str(e)
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    response += "\n⚠️ Command sync rate limited - commands will sync automatically when rate limit clears."
                    logger.warning(f"Command sync rate limited: {e}")
                else:
                    logger.debug(f"Failed to sync commands: {e}")
        
        return response

    async def personality_command(self, ctx: CommandContext) -> str:
        """Handle /personality command."""
        if not ctx.args:
            # Show current personality
            current = (
                self._bot._config.system_prompt
                or self._bot._config.personality
                or "default"
            )
            return f"Current personality: **{current}**"

        # Update personality (requires admin/bot owner in future)
        new_personality = " ".join(ctx.args)
        self._bot._config.personality = new_personality
        self._bot._config.system_prompt = None  # Clear explicit prompt
        return f"Personality updated to: **{new_personality}**"

    async def status_command(self, ctx: CommandContext) -> str:
        """Handle /status command."""
        lines = ["**Bot Status:**"]
        lines.append(f"Conversation scope: `{self._bot._config.conversation_scope}`")
        lines.append(
            f"Max history entries: `{self._bot._config.max_history_entries}`"
        )
        lines.append(
            f"Rate limit: `{self._bot._config.rate_limit_per_minute}/min`"
        )

        # Check orchestrator health
        try:
            orchestrator = self._bot.get_orchestrator()
            if orchestrator:
                lines.append("Orchestrator: ✅ Ready")
            else:
                lines.append("Orchestrator: ❌ Not initialized")
        except Exception:
            lines.append("Orchestrator: ❌ Error")

        return "\n".join(lines)

