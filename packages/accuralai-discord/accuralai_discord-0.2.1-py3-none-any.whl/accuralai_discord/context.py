"""Conversation context management for Discord messages."""

from __future__ import annotations

from typing import Literal

import discord

ConversationScope = Literal[
    "per-channel", "per-user", "per-thread", "per-channel-user"
]


def generate_context_key(
    scope: ConversationScope,
    guild_id: int | None,
    channel_id: int,
    user_id: int | None = None,
    thread_id: int | None = None,
) -> str:
    """
    Generate a context key for conversation memory based on scope.

    Args:
        scope: Conversation scope type
        guild_id: Discord guild/server ID (None for DMs)
        channel_id: Discord channel ID
        user_id: Discord user ID (required for per-user scopes)
        thread_id: Discord thread ID (required for per-thread scopes)

    Returns:
        Context key string for cache lookup

    Examples:
        >>> generate_context_key("per-channel", 123, 456)
        'discord:guild:123:channel:456'
        >>> generate_context_key("per-user", 123, 456, user_id=789)
        'discord:guild:123:user:789'
    """
    if guild_id is None:
        # Direct messages - use channel ID as user ID in DMs
        if scope == "per-user":
            return f"discord:dm:user:{channel_id}"
        return f"discord:dm:channel:{channel_id}"

    if scope == "per-channel":
        return f"discord:guild:{guild_id}:channel:{channel_id}"
    elif scope == "per-user":
        if user_id is None:
            raise ValueError("user_id required for per-user scope")
        return f"discord:guild:{guild_id}:user:{user_id}"
    elif scope == "per-thread":
        if thread_id is not None:
            return f"discord:guild:{guild_id}:thread:{thread_id}"
        # Fallback to channel if not in thread
        return f"discord:guild:{guild_id}:channel:{channel_id}"
    elif scope == "per-channel-user":
        if user_id is None:
            raise ValueError("user_id required for per-channel-user scope")
        return f"discord:guild:{guild_id}:channel:{channel_id}:user:{user_id}"
    else:
        raise ValueError(f"Unknown conversation scope: {scope}")


def extract_context_from_message(
    message: discord.Message,
    scope: ConversationScope,
) -> tuple[str, dict[str, int | None]]:
    """
    Extract context key and metadata from a Discord message.

    Args:
        message: Discord message object
        scope: Conversation scope type

    Returns:
        Tuple of (context_key, metadata_dict)
    """
    guild_id = message.guild.id if message.guild else None
    channel_id = message.channel.id
    user_id = message.author.id
    thread_id = None

    # Check if message is in a thread
    if isinstance(message.channel, discord.Thread):
        thread_id = message.channel.id

    context_key = generate_context_key(
        scope=scope,
        guild_id=guild_id,
        channel_id=channel_id,
        user_id=user_id,
        thread_id=thread_id,
    )

    metadata = {
        "guild_id": guild_id,
        "channel_id": channel_id,
        "user_id": user_id,
        "thread_id": thread_id,
    }

    return context_key, metadata

