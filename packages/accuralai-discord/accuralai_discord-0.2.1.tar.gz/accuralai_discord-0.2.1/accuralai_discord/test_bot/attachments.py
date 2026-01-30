"""Enhanced attachment processing utilities for test bot."""

from __future__ import annotations

import asyncio
import io
from typing import Any, Dict, List, Optional

import discord


# File type categories
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".cs",
    ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".r", ".m",
    ".html", ".css", ".xml", ".json", ".yaml", ".yml", ".toml", ".ini",
    ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd", ".sql", ".md", ".txt"
}
TEXT_EXTENSIONS = {".txt", ".md", ".log", ".csv", ".tsv"}


async def process_attachment(attachment: discord.Attachment) -> Dict[str, Any]:
    """
    Process a Discord attachment and extract useful information.
    
    Args:
        attachment: Discord attachment to process
        
    Returns:
        Dict with processed attachment data
    """
    result = {
        "filename": attachment.filename,
        "size": attachment.size,
        "content_type": attachment.content_type,
        "url": attachment.url,
        "type": "unknown",
        "content": None,
        "preview": None,
    }
    
    # Determine file type
    filename_lower = attachment.filename.lower()
    ext = filename_lower[filename_lower.rfind("."):] if "." in filename_lower else ""
    
    if ext in IMAGE_EXTENSIONS or (attachment.content_type and attachment.content_type.startswith("image/")):
        result["type"] = "image"
        result["preview"] = f"Image: {attachment.filename} ({attachment.size:,} bytes)"
    elif ext in VIDEO_EXTENSIONS or (attachment.content_type and attachment.content_type.startswith("video/")):
        result["type"] = "video"
        result["preview"] = f"Video: {attachment.filename} ({attachment.size:,} bytes)"
    elif ext in CODE_EXTENSIONS:
        result["type"] = "code"
        # Try to read code files (up to 50KB)
        if attachment.size <= 50 * 1024:
            try:
                content_bytes = await attachment.read()
                content = content_bytes.decode("utf-8", errors="replace")
                result["content"] = content
                result["preview"] = f"Code file ({attachment.filename}):\n```{ext[1:] if ext else 'text'}\n{content[:1000]}{'...' if len(content) > 1000 else ''}\n```"
            except Exception as e:
                result["preview"] = f"Code file: {attachment.filename} (could not read: {e})"
        else:
            result["preview"] = f"Code file: {attachment.filename} (too large: {attachment.size:,} bytes)"
    elif ext in TEXT_EXTENSIONS or (attachment.content_type and "text" in attachment.content_type):
        result["type"] = "text"
        # Try to read text files (up to 100KB)
        if attachment.size <= 100 * 1024:
            try:
                content_bytes = await attachment.read()
                content = content_bytes.decode("utf-8", errors="replace")
                result["content"] = content
                result["preview"] = f"Text file ({attachment.filename}):\n{content[:2000]}{'...' if len(content) > 2000 else ''}"
            except Exception as e:
                result["preview"] = f"Text file: {attachment.filename} (could not read: {e})"
        else:
            result["preview"] = f"Text file: {attachment.filename} (too large: {attachment.size:,} bytes)"
    else:
        result["preview"] = f"File: {attachment.filename} ({attachment.size:,} bytes, {attachment.content_type or 'unknown type'})"
    
    return result


async def process_all_attachments(message: discord.Message) -> List[Dict[str, Any]]:
    """
    Process all attachments in a message.
    
    Args:
        message: Discord message with attachments
        
    Returns:
        List of processed attachment data
    """
    if not message.attachments:
        return []
    
    tasks = [process_attachment(att) for att in message.attachments]
    return await asyncio.gather(*tasks)


def format_attachments_summary(attachments: List[Dict[str, Any]]) -> str:
    """
    Format attachments summary for AI context.
    
    Args:
        attachments: List of processed attachment data
        
    Returns:
        Formatted string summary
    """
    if not attachments:
        return ""
    
    lines = ["\n**Attachments:**"]
    for att in attachments:
        lines.append(f"- {att['preview']}")
        if att.get("content"):
            lines.append(f"  Content: {att['content'][:500]}...")
    
    return "\n".join(lines)

