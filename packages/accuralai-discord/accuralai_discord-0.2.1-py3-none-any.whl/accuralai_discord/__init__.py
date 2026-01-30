"""AccuralAI Discord Bot Package - High-level abstraction for AI-powered Discord bots."""

from .bot import DiscordBot
from .config import DiscordBotConfig
from .tools import ToolRegistry, ToolExecutor
from .analytics import BotAnalytics
from .streaming import StreamingResponse, stream_response
from .embeds import create_response_embed, create_error_embed, create_info_embed
from .multimodal import enhance_request_with_attachments, extract_attachments
from .context_aware import build_discord_context, enhance_system_prompt_with_context

__all__ = [
    "DiscordBot",
    "DiscordBotConfig",
    "ToolRegistry",
    "ToolExecutor",
    "BotAnalytics",
    "StreamingResponse",
    "stream_response",
    "create_response_embed",
    "create_error_embed",
    "create_info_embed",
    "enhance_request_with_attachments",
    "extract_attachments",
    "build_discord_context",
    "enhance_system_prompt_with_context",
]

