"""Configuration models for Discord bot."""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


class DiscordBotConfig(BaseModel):
    """Configuration for Discord bot instance."""

    token: str = Field(..., description="Discord bot token")
    personality: str | None = Field(
        default=None,
        description="Short personality description (e.g., 'friendly assistant')",
    )
    system_prompt: str | None = Field(
        default=None,
        description="Full system prompt (overrides personality if provided)",
    )
    conversation_scope: Literal[
        "per-channel", "per-user", "per-thread", "per-channel-user"
    ] = Field(
        default="per-channel",
        description="How to scope conversation context",
    )
    max_history_entries: int = Field(
        default=50,
        ge=1,
        description="Maximum conversation history entries to keep",
    )
    max_history_tokens: int | None = Field(
        default=None,
        ge=1,
        description="Maximum tokens in conversation history (truncates oldest)",
    )
    command_prefix: str = Field(
        default="/",
        description="Prefix for commands (e.g., '/', '!')",
    )
    rate_limit_per_minute: int = Field(
        default=20,
        ge=1,
        description="Rate limit per context per minute",
    )
    accuralai_config_path: str | None = Field(
        default=None,
        description="Path to AccuralAI configuration TOML file",
    )
    accuralai_config_overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="AccuralAI configuration overrides",
    )
    enable_builtin_commands: bool = Field(
        default=True,
        description="Enable built-in commands (/help, /reset, etc.)",
    )
    conversation_ttl_hours: int | None = Field(
        default=None,
        ge=1,
        description="TTL in hours for conversation history (None = no expiry)",
    )
    # Enhanced features
    enable_streaming: bool = Field(
        default=False,
        description="Enable streaming responses with typing indicators",
    )
    enable_tool_calling: bool = Field(
        default=True,
        description="Enable tool/function calling support",
    )
    enable_multimodal: bool = Field(
        default=True,
        description="Enable multi-modal support (images, files)",
    )
    use_embeds: bool = Field(
        default=False,
        description="Use Discord embeds for responses",
    )
    enable_analytics: bool = Field(
        default=True,
        description="Enable analytics and telemetry",
    )
    smart_history: bool = Field(
        default=False,
        description="Enable smart history management (summarization)",
    )
    context_aware: bool = Field(
        default=True,
        description="Include Discord context (roles, permissions) in prompts",
    )
    # Slash command support
    enable_slash_commands: bool = Field(
        default=True,
        description="Enable Discord slash commands (application commands)",
    )
    auto_sync_slash_commands: bool = Field(
        default=True,
        description="Automatically sync slash commands on startup",
    )
    sync_guild_commands: List[int] = Field(
        default_factory=list,
        description="List of guild IDs to sync commands for (empty = global only)",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug logging to console",
    )
