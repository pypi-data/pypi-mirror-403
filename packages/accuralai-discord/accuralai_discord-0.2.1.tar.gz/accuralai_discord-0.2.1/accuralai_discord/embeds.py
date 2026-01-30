"""Rich embed support for Discord bot responses."""

from __future__ import annotations

from typing import Any, Dict, Optional

import discord
from accuralai_core.contracts.models import GenerateResponse


def create_response_embed(
    response: GenerateResponse,
    *,
    title: Optional[str] = None,
    color: Optional[int] = None,
    show_metadata: bool = False,
) -> discord.Embed:
    """
    Create Discord embed from AI response.

    Args:
        response: AI response
        title: Optional embed title
        color: Optional embed color (hex integer)
        show_metadata: Show response metadata (tokens, latency, etc.)

    Returns:
        Discord embed object
    """
    embed = discord.Embed(
        title=title or "AI Response",
        description=response.output_text[:4096],  # Discord embed limit
        color=color or discord.Color.blurple(),
    )

    if show_metadata:
        usage = response.usage
        embed.add_field(
            name="Tokens",
            value=f"Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}",
            inline=True,
        )
        embed.add_field(
            name="Latency",
            value=f"{response.latency_ms}ms",
            inline=True,
        )
        if response.metadata.get("cache_status"):
            embed.add_field(
                name="Cache",
                value=response.metadata["cache_status"],
                inline=True,
            )

    return embed


def create_error_embed(
    error: str,
    *,
    title: str = "Error",
    color: Optional[int] = None,
) -> discord.Embed:
    """
    Create error embed.

    Args:
        error: Error message
        title: Embed title
        color: Embed color

    Returns:
        Discord embed object
    """
    return discord.Embed(
        title=title,
        description=error[:4096],
        color=color or discord.Color.red(),
    )


def create_info_embed(
    title: str,
    description: str,
    *,
    fields: Optional[Dict[str, Any]] = None,
    color: Optional[int] = None,
) -> discord.Embed:
    """
    Create informational embed.

    Args:
        title: Embed title
        description: Embed description
        fields: Optional dict of field names to values
        color: Embed color

    Returns:
        Discord embed object
    """
    embed = discord.Embed(
        title=title,
        description=description[:4096],
        color=color or discord.Color.blue(),
    )

    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=str(value)[:1024], inline=True)

    return embed


def split_embed_content(text: str, max_length: int = 4096) -> list[str]:
    """
    Split text into chunks that fit in Discord embed description.

    Args:
        text: Text to split
        max_length: Maximum length per chunk

    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    for para in text.split("\n\n"):
        if len(current_chunk) + len(para) + 2 <= max_length:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

