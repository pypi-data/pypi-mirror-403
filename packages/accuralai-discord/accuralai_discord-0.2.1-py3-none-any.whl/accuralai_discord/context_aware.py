"""Enhanced context awareness for Discord bot."""

from __future__ import annotations

from typing import Any, Dict, List

import discord
from accuralai_core.contracts.models import GenerateRequest


def build_discord_context(
    message: discord.Message,
    *,
    include_roles: bool = True,
    include_permissions: bool = True,
    include_channel_info: bool = True,
) -> Dict[str, Any]:
    """
    Build rich Discord context metadata.

    Args:
        message: Discord message
        include_roles: Include user roles
        include_permissions: Include user permissions
        include_channel_info: Include channel information

    Returns:
        Context metadata dictionary
    """
    context: Dict[str, Any] = {
        "user_id": str(message.author.id),
        "user_name": message.author.name,
        "user_display_name": message.author.display_name,
        "channel_id": str(message.channel.id),
        "channel_name": getattr(message.channel, "name", None),
        "guild_id": str(message.guild.id) if message.guild else None,
        "guild_name": message.guild.name if message.guild else None,
        "message_id": str(message.id),
        "is_thread": isinstance(message.channel, discord.Thread),
    }

    if include_channel_info and message.channel:
        if isinstance(message.channel, discord.TextChannel):
            context["channel_type"] = "text"
            context["channel_topic"] = message.channel.topic
            context["channel_nsfw"] = message.channel.nsfw
        elif isinstance(message.channel, discord.Thread):
            context["channel_type"] = "thread"
            context["thread_name"] = message.channel.name
            context["thread_archived"] = message.channel.archived

    if include_roles and message.guild and isinstance(message.author, discord.Member):
        context["user_roles"] = [role.name for role in message.author.roles if role.name != "@everyone"]
        context["user_nick"] = message.author.nick
        context["user_top_role"] = message.author.top_role.name if message.author.top_role else None

    if include_permissions and message.guild and isinstance(message.author, discord.Member):
        channel_perms = message.channel.permissions_for(message.author)
        context["permissions"] = {
            "send_messages": channel_perms.send_messages,
            "read_messages": channel_perms.read_messages,
            "manage_messages": channel_perms.manage_messages,
            "administrator": channel_perms.administrator,
        }

    return context


def enhance_system_prompt_with_context(
    base_prompt: str,
    context: Dict[str, Any],
) -> str:
    """
    Enhance system prompt with Discord context information.

    Args:
        base_prompt: Base system prompt
        context: Discord context metadata

    Returns:
        Enhanced system prompt
    """
    context_lines = []

    if context.get("guild_name"):
        context_lines.append(f"You are in the Discord server: {context['guild_name']}")

    if context.get("channel_name"):
        context_lines.append(f"You are in the channel: #{context['channel_name']}")

    if context.get("user_name"):
        context_lines.append(f"The user you are talking to is: {context['user_display_name'] or context['user_name']}")

    if context.get("user_roles"):
        roles_str = ", ".join(context["user_roles"][:5])  # Limit to 5 roles
        context_lines.append(f"The user has roles: {roles_str}")

    if context_lines:
        context_section = "\n".join(context_lines)
        return f"{base_prompt}\n\nDiscord Context:\n{context_section}"

    return base_prompt


def build_contextual_prompt(
    content: str,
    message: discord.Message,
    *,
    include_mentions: bool = True,
) -> str:
    """
    Build prompt with Discord context.

    Args:
        content: Message content
        message: Discord message
        include_mentions: Include mention information

    Returns:
        Contextual prompt string
    """
    prompt = content

    if include_mentions and message.mentions:
        mention_info = []
        for user in message.mentions:
            if isinstance(user, discord.Member) and user.nick:
                mention_info.append(f"@{user.nick} ({user.name})")
            else:
                mention_info.append(f"@{user.name}")
        if mention_info:
            prompt += f"\n\n(Mentioned users: {', '.join(mention_info)})"

    if message.reference and message.reference.resolved:
        if isinstance(message.reference.resolved, discord.Message):
            ref_content = message.reference.resolved.content[:200]
            prompt = f"Replying to: {ref_content}\n\n{prompt}"

    return prompt

