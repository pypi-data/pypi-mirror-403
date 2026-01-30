"""Utility functions for Discord/AccuralAI integration."""

from __future__ import annotations

import re
from typing import Any


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a text string.

    Uses a simple approximation: ~4 characters per token.
    This matches the default tokenizer approach in AccuralAI.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    # Simple approximation: ~4 chars per token
    return len(text) // 4 + 1


def clean_discord_message(content: str) -> str:
    """
    Clean Discord message content for AI processing.

    Removes mentions, channel references, etc. while preserving meaning.

    Args:
        content: Raw Discord message content

    Returns:
        Cleaned message content
    """
    # Remove user mentions (<@123456789>)
    content = re.sub(r"<@!?\d+>", "[user]", content)
    # Remove channel mentions (<#123456789>)
    content = re.sub(r"<#\d+>", "[channel]", content)
    # Remove role mentions (<@&123456789>)
    content = re.sub(r"<@&\d+>", "[role]", content)
    # Remove custom emoji (<:name:123456789>)
    content = re.sub(r"<:\w+:\d+>", "", content)
    # Remove animated emoji (<a:name:123456789>)
    content = re.sub(r"<a:\w+:\d+>", "", content)

    return content.strip()


def build_system_prompt(
    personality: str | None = None,
    system_prompt: str | None = None,
    available_tools: list[dict[str, Any]] | None = None,
) -> str | None:
    """
    Build system prompt from personality or explicit prompt.

    Args:
        personality: Short personality description
        system_prompt: Full system prompt (takes precedence)
        available_tools: List of available tools to mention in the prompt

    Returns:
        System prompt string or None
    """
    base_prompt = None
    if system_prompt:
        base_prompt = system_prompt
    elif personality:
        base_prompt = f"You are a {personality}. Be helpful, concise, and engaging."
    else:
        base_prompt = "You are a helpful AI assistant."
    
    # Add Discord message length limit instructions
    if base_prompt:
        discord_limit_note = (
            "\n\nIMPORTANT: Discord has a 2000 character limit per message. "
            "You MUST keep responses under 2000 characters per message. "
            "If needed, responses can be split across up to 3 messages (6000 characters total maximum). "
            "Do not exceed 3 messages total - if your response would be longer, prioritize the most important information and truncate. "
            "Always try to stay within a single message when possible."
        )
        base_prompt += discord_limit_note
    
    # Add tool information if tools are available
    if available_tools and base_prompt:
        tool_descriptions = []
        for tool in available_tools:
            func_info = tool.get("function", {})
            tool_name = func_info.get("name", "")
            tool_desc = func_info.get("description", "")
            if tool_name and tool_desc:
                tool_descriptions.append(f"- {tool_name}: {tool_desc}")
        
        if tool_descriptions:
            tools_section = "\n\nYou have access to the following tools/functions:\n" + "\n".join(tool_descriptions)
            tools_section += "\n\nCRITICAL: When users ask you to perform actions that match these tools, you MUST call the appropriate tool function. Do not just acknowledge the request - actually use the tool. If a user asks you to sync commands, sync guild commands, update commands, refresh commands, reload commands, or make commands available, you MUST call the sync_commands function immediately. Do not explain that you will do it - just call the function."
            base_prompt += tools_section
    
    return base_prompt


def split_discord_message(text: str, max_size: int = 2000, max_messages: int = 3) -> list[str]:
    """
    Split text into Discord message chunks.
    
    Enforces Discord's 2000 character limit per message and a maximum of 3 messages
    (6000 characters total). If text exceeds the limit, it will be truncated.

    Args:
        text: Text to split
        max_size: Maximum characters per chunk (Discord limit is 2000)
        max_messages: Maximum number of messages to split into (default: 3)

    Returns:
        List of text chunks (up to max_messages, truncated if necessary)
    """
    if len(text) <= max_size:
        return [text]
    
    max_total = max_size * max_messages
    if len(text) > max_total:
        # Truncate to max_total characters, trying to cut at a sentence boundary
        truncated = text[:max_total]
        # Try to find last sentence boundary
        last_sentence = max(
            truncated.rfind(". "),
            truncated.rfind("! "),
            truncated.rfind("? "),
            truncated.rfind(".\n"),
            truncated.rfind("!\n"),
            truncated.rfind("?\n"),
        )
        if last_sentence > max_total * 0.8:  # Only use boundary if not too close to start
            text = truncated[:last_sentence + 1]
        else:
            text = truncated

    chunks = []
    current_chunk = ""

    # Split by paragraphs first
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_size:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                chunks.append(current_chunk)
                if len(chunks) >= max_messages:
                    return chunks
            current_chunk = para

            # If single paragraph is too long, split by sentences
            if len(current_chunk) > max_size:
                sentences = re.split(r"(?<=[.!?])\s+", current_chunk)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= max_size:
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                            if len(chunks) >= max_messages:
                                return chunks
                        current_chunk = sentence

    if current_chunk and len(chunks) < max_messages:
        chunks.append(current_chunk)

    return chunks


def format_discord_code_block(code: str, language: str = "") -> str:
    """
    Format text as Discord code block.

    Args:
        code: Code/text to format
        language: Language identifier (optional)

    Returns:
        Formatted code block string
    """
    return f"```{language}\n{code}\n```"


def extract_mentions(content: str) -> list[str]:
    """
    Extract user mentions from Discord message.

    Args:
        content: Message content

    Returns:
        List of user IDs mentioned
    """
    return re.findall(r"<@!?(\d+)>", content)

