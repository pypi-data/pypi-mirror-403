"""Multi-modal support for Discord bot (images, files, attachments)."""

from __future__ import annotations

import base64
import io
from typing import Any, Dict, List

import discord
from accuralai_core.contracts.models import GenerateRequest


def extract_image_data(attachment: discord.Attachment) -> Dict[str, Any]:
    """
    Extract image data from Discord attachment.

    Args:
        attachment: Discord attachment

    Returns:
        Dict with image data for AI processing
    """
    # Note: This is a placeholder - actual implementation would download and encode
    return {
        "type": "image_url",
        "image_url": {
            "url": attachment.url,
        },
    }


def extract_attachments(message: discord.Message) -> List[Dict[str, Any]]:
    """
    Extract attachment data from Discord message.

    Args:
        message: Discord message

    Returns:
        List of attachment data dicts
    """
    attachments = []
    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            attachments.append(extract_image_data(attachment))
    return attachments


def enhance_request_with_attachments(
    request: GenerateRequest,
    message: discord.Message,
) -> GenerateRequest:
    """
    Enhance GenerateRequest with attachment data.

    Args:
        request: Original request
        message: Discord message with attachments

    Returns:
        Enhanced request with attachment data
    """
    attachments = extract_attachments(message)
    if attachments:
        # Add attachments to metadata or history
        metadata = request.metadata.copy()
        metadata["discord_attachments"] = attachments

        # If history exists, add attachments to last user message
        history = list(request.history)
        if history and history[-1].get("role") == "user":
            history[-1] = {**history[-1], "attachments": attachments}

        return request.model_copy(update={"metadata": metadata, "history": history})

    return request


async def download_attachment(attachment: discord.Attachment) -> bytes:
    """
    Download attachment content.

    Args:
        attachment: Discord attachment

    Returns:
        Attachment content as bytes
    """
    return await attachment.read()


def format_attachment_info(attachment: discord.Attachment) -> str:
    """
    Format attachment info for text representation.

    Args:
        attachment: Discord attachment

    Returns:
        Formatted string describing attachment
    """
    return f"[Attachment: {attachment.filename}, {attachment.size} bytes, {attachment.content_type}]"

