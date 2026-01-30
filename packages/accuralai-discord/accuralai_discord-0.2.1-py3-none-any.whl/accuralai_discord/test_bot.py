"""Test bot for AccuralAI Discord package.

This script demonstrates how to use the accuralai-discord package
with a simple test bot that can be configured via environment variables.

Usage:
    export DISCORD_BOT_TOKEN="your_token_here"
    export ACCURALAI_CONFIG_PATH="path/to/config.toml"  # Optional
    python -m accuralai_discord.test_bot
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from discord import app_commands

from accuralai_discord import DiscordBot, DiscordBotConfig
from accuralai_discord.test_bot.attachments import process_all_attachments, format_attachments_summary
from accuralai_discord.test_bot.web_search import search_web, format_search_results
from accuralai_discord.test_bot.codebase_search import (
    WebCodebaseSearch,
    format_codebase_results,
    format_combined_results,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
LOGGER = logging.getLogger("accuralai.discord.test")


def load_env_config() -> dict:
    """Load configuration from environment variables."""
    config = {}

    # Required: Bot token
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        LOGGER.error("DISCORD_BOT_TOKEN environment variable is required")
        sys.exit(1)
    # Strip quotes that Windows CMD/PowerShell might add
    token = token.strip('"').strip("'")
    if not token:
        LOGGER.error("DISCORD_BOT_TOKEN is empty after stripping quotes")
        sys.exit(1)
    config["token"] = token

    # Optional: AccuralAI config path
    accuralai_config = os.getenv("ACCURALAI_CONFIG_PATH")
    if accuralai_config:
        # Strip quotes that Windows CMD/PowerShell might add
        accuralai_config = accuralai_config.strip('"').strip("'")
        # Expand user path (e.g., ~/config.toml)
        accuralai_config = os.path.expanduser(accuralai_config)
        # Make absolute path if relative
        if not os.path.isabs(accuralai_config):
            accuralai_config = os.path.abspath(accuralai_config)
        config["accuralai_config_path"] = accuralai_config
        LOGGER.info(f"Using AccuralAI config: {accuralai_config}")

    # Optional: Personality
    personality = os.getenv("DISCORD_BOT_PERSONALITY")
    if personality:
        config["personality"] = personality
    else:
        # Default personality with enhanced capabilities description
        config["personality"] = (
            "helpful AI assistant specialized in AccuralAI. "
            "You have access to search tools including web search and codebase search for AccuralAI documentation. "
            "Use search_codebase to find information in the AccuralAI codebase, documentation, README files, and code. "
            "Use search_web for current information, news, or general knowledge not in the codebase. "
            "Use search_all to search both simultaneously. "
            "Always search for relevant information before answering questions about AccuralAI or technical topics."
        )

    # Optional: Conversation scope
    scope = os.getenv("DISCORD_BOT_SCOPE", "per-channel")
    if scope in ["per-channel", "per-user", "per-thread", "per-channel-user"]:
        config["conversation_scope"] = scope

    # Optional: Feature flags
    config["enable_streaming"] = os.getenv("DISCORD_ENABLE_STREAMING", "false").lower() == "true"
    config["enable_tool_calling"] = os.getenv("DISCORD_ENABLE_TOOLS", "true").lower() == "true"
    config["enable_multimodal"] = os.getenv("DISCORD_ENABLE_MULTIMODAL", "true").lower() == "true"
    config["use_embeds"] = os.getenv("DISCORD_USE_EMBEDS", "false").lower() == "true"
    config["enable_analytics"] = os.getenv("DISCORD_ENABLE_ANALYTICS", "true").lower() == "true"
    config["smart_history"] = os.getenv("DISCORD_SMART_HISTORY", "false").lower() == "true"
    config["context_aware"] = os.getenv("DISCORD_CONTEXT_AWARE", "true").lower() == "true"
    config["debug"] = os.getenv("DISCORD_DEBUG", "false").lower() == "true"

    # Optional: Rate limiting
    rate_limit = os.getenv("DISCORD_RATE_LIMIT")
    if rate_limit:
        try:
            config["rate_limit_per_minute"] = int(rate_limit)
        except ValueError:
            LOGGER.warning(f"Invalid rate limit value: {rate_limit}, using default")

    # Optional: History settings
    max_history = os.getenv("DISCORD_MAX_HISTORY")
    if max_history:
        try:
            config["max_history_entries"] = int(max_history)
        except ValueError:
            LOGGER.warning(f"Invalid max history value: {max_history}, using default")

    # Optional: Bot user ID (for mention filtering - only used if specified)
    # If not set, bot will check if it's mentioned by comparing with client.user.id
    bot_user_id = os.getenv("DISCORD_BOT_USER_ID")
    if bot_user_id:
        bot_user_id = bot_user_id.strip('"').strip("'")
        try:
            config["bot_user_id"] = int(bot_user_id)
            LOGGER.info(f"Using bot user ID from env: {bot_user_id}")
        except ValueError:
            LOGGER.warning(f"Invalid bot user ID: {bot_user_id}, will use client.user.id instead")

    return config


def _safe_calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        # Only allow basic math operations
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic math operations allowed"
        result = eval(expression)  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


async def _sync_guild_commands_handler(context: dict, bot: DiscordBot) -> str:
    """Handler for syncing guild commands (requires admin permissions)."""
    message = context.get("message")
    guild = context.get("guild")
    user = context.get("user")
    
    if not message or not guild:
        return "❌ This command can only be used in a server."
    
    # Check if user has admin permissions
    if isinstance(user, discord.Member):
        if not user.guild_permissions.administrator:
            return "❌ You need administrator permissions to sync commands."
    else:
        # If user is not a Member (e.g., User in DM), try to get member
        try:
            member = guild.get_member(user.id) if user else None
            if not member or not member.guild_permissions.administrator:
                return "❌ You need administrator permissions to sync commands."
        except Exception:
            return "❌ Could not verify permissions. Please ensure you're a server administrator."
    
    try:
        await bot.sync_slash_commands(guild=guild)
        return f"✅ Commands synced to **{guild.name}**! Commands should appear immediately. Try typing `/` to see them."
    except Exception as e:
        LOGGER.error(f"Failed to sync commands: {e}", exc_info=True)
        return f"❌ Failed to sync commands: {str(e)}"


def _create_sync_handler(bot: DiscordBot):
    """Create a sync handler function bound to the bot instance."""
    async def sync_handler(context: dict) -> str:
        return await _sync_guild_commands_handler(context, bot)
    return sync_handler


def setup_test_tools(bot: DiscordBot, codebase_searcher: WebCodebaseSearch | None = None) -> None:
    """Register example tools for testing."""
    if not bot._config.enable_tool_calling:
        return

    # Example: Echo tool
    async def echo_handler(message: str, context: dict) -> str:
        """Echo back a message."""
        return f"Echo: {message}"
    
    bot.add_tool(
        name="echo",
        description="Echo back a message",
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message to echo"}
            },
            "required": ["message"],
        },
        handler=echo_handler,
    )

    # Example: Calculator tool
    async def calculate_handler(expression: str, context: dict) -> str:
        """Perform a simple calculation."""
        return _safe_calculate(expression)
    
    bot.add_tool(
        name="calculate",
        description="Perform a simple calculation",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2')",
                }
            },
            "required": ["expression"],
        },
        handler=calculate_handler,
    )

    # Web search tool
    async def web_search_handler(query: str, context: dict) -> str:
        """Search the web for information."""
        if not query or len(query.strip()) < 3:
            return "Error: Search query must be at least 3 characters."
        
        try:
            # Get config path from bot's config
            config_path = bot._config.accuralai_config_path if hasattr(bot, '_config') else None
            results = await search_web(query, max_results=5, config_path=config_path)
            return format_search_results(results)
        except Exception as e:
            LOGGER.error(f"Web search error: {e}", exc_info=True)
            return f"Error searching web: {str(e)}"
    
    bot.add_tool(
        name="search_web",
        description="Search the internet for current information, news, general knowledge, or anything not in the codebase. Use this when you need information that might have changed recently or isn't in the AccuralAI documentation.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (at least 3 characters)",
                }
            },
            "required": ["query"],
        },
        handler=web_search_handler,
    )

    # Codebase search tool
    if codebase_searcher:
        async def codebase_search_handler(query: str, context: dict) -> str:
            """Search AccuralAI codebase and generate AI summary from retrieved context."""
            if not query or len(query.strip()) < 2:
                return "Error: Search query must be at least 2 characters."
            
            try:
                # Retrieve relevant chunks using embeddings (increased for better recall)
                results = await codebase_searcher.search_codebase(query, max_results=15)
                
                if not results:
                    return "No relevant information found in the codebase for your query."
                
                # Build context from retrieved chunks with package information
                context_chunks = []
                for i, result in enumerate(results, 1):
                    path = result.get("path", "unknown")
                    snippet = result.get("snippet", result.get("full_content", ""))
                    file_type = result.get("type", "unknown")
                    score = result.get("score", 0)
                    
                    # Extract package name from path (e.g., packages/accuralai-ollama/...)
                    package_name = "unknown"
                    path_parts = path.replace("\\", "/").split("/")
                    if "packages" in path_parts:
                        packages_idx = path_parts.index("packages")
                        if packages_idx + 1 < len(path_parts):
                            package_name = path_parts[packages_idx + 1]
                    
                    # Use full content if snippet is short
                    content = snippet if len(snippet) > 300 else result.get("full_content", snippet)
                    
                    context_chunks.append(
                        f"[Document {i} - Package: {package_name} | File: {path} ({file_type}) | Relevance: {score:.3f}]\n"
                        f"{content}\n"
                    )
                
                context_text = "\n\n".join(context_chunks)
                
                # Generate AI response based on context
                bot_instance = context.get("bot")
                if bot_instance and hasattr(bot_instance, "_orchestrator") and bot_instance._orchestrator:
                    # Build prompt for synthesis
                    synthesis_prompt = (
                        f"Based on the following codebase context, answer the user's question: {query}\n\n"
                        f"Context from codebase:\n{context_text}\n\n"
                        f"Provide a clear, comprehensive answer based on the context above. "
                        f"Cite specific files or sections when relevant. If the context doesn't fully answer the question, "
                        f"say so and suggest what additional information might be needed."
                    )
                    
                    try:
                        # Generate response using bot's orchestrator
                        from accuralai_core.contracts.models import GenerateRequest
                        from uuid import uuid4
                        
                        request = GenerateRequest(
                            id=uuid4(),
                            prompt=synthesis_prompt,
                            system_prompt="You are a helpful AI assistant answering questions about the AccuralAI codebase based on retrieved documentation and code context.",
                        )
                        
                        response = await bot_instance._orchestrator.generate(request)
                        return response.output_text if response.output_text else "Unable to generate response."
                    except Exception as e:
                        LOGGER.error(f"Error generating AI summary: {e}", exc_info=True)
                        # Fallback to formatted results
                        return format_codebase_results(results)
                else:
                    # Fallback: return formatted results if bot instance not available
                    return format_codebase_results(results)
                    
            except Exception as e:
                LOGGER.error(f"Codebase search error: {e}", exc_info=True)
                return f"Error searching codebase: {str(e)}"
        
        bot.add_tool(
            name="search_codebase",
            description="Search AccuralAI codebase, documentation, README files, markdown files, Python code, and configuration files. Use this to find information about how AccuralAI works, its architecture, packages, configuration, or implementation details. This searches local documentation and code.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for AccuralAI documentation/codebase (at least 2 characters)",
                    }
                },
                "required": ["query"],
            },
            handler=codebase_search_handler,
        )

        # Combined search tool
        async def combined_search_handler(query: str, context: dict) -> str:
            """Search both codebase and web, then generate AI summary from retrieved context."""
            if not query or len(query.strip()) < 2:
                return "Error: Search query must be at least 2 characters."
            
            try:
                # Search both sources
                results = await codebase_searcher.search_all(query, codebase_max=3, web_max=3)
                
                codebase_results = results.get("codebase", [])
                web_results = results.get("web", [])
                
                if not codebase_results and not web_results:
                    return "No relevant information found in codebase or web for your query."
                
                # Build context from both sources
                context_parts = []
                
                if codebase_results:
                    context_parts.append("**Codebase Context:**\n")
                    for i, result in enumerate(codebase_results, 1):
                        path = result.get("path", "unknown")
                        snippet = result.get("snippet", result.get("full_content", ""))
                        context_parts.append(f"[Codebase {i} - {path}]\n{snippet}\n")
                
                if web_results and not web_results[0].get("error"):
                    context_parts.append("\n**Web Search Context:**\n")
                    for i, result in enumerate(web_results, 1):
                        title = result.get("title", "Unknown")
                        snippet = result.get("snippet", result.get("content", ""))
                        url = result.get("url", "")
                        context_parts.append(f"[Web {i} - {title}]\n{snippet}\n{url}\n")
                
                context_text = "\n".join(context_parts)
                
                # Generate AI response based on context
                bot_instance = context.get("bot")
                if bot_instance and hasattr(bot_instance, "_orchestrator") and bot_instance._orchestrator:
                    # Build prompt for synthesis
                    synthesis_prompt = (
                        f"Based on the following context from codebase and web search, answer the user's question: {query}\n\n"
                        f"{context_text}\n\n"
                        f"Provide a clear, comprehensive answer based on the context above. "
                        f"Distinguish between information from the codebase vs web sources when relevant. "
                        f"If the context doesn't fully answer the question, say so and suggest what additional information might be needed."
                    )
                    
                    try:
                        # Generate response using bot's orchestrator
                        from accuralai_core.contracts.models import GenerateRequest
                        from uuid import uuid4
                        
                        request = GenerateRequest(
                            id=uuid4(),
                            prompt=synthesis_prompt,
                            system_prompt="You are a helpful AI assistant answering questions based on retrieved context from both the AccuralAI codebase and web search results.",
                        )
                        
                        response = await bot_instance._orchestrator.generate(request)
                        return response.output_text if response.output_text else "Unable to generate response."
                    except Exception as e:
                        LOGGER.error(f"Error generating AI summary: {e}", exc_info=True)
                        # Fallback to formatted results
                        return format_combined_results(codebase_results, web_results)
                else:
                    # Fallback: return formatted results if bot instance not available
                    return format_combined_results(codebase_results, web_results)
                    
            except Exception as e:
                LOGGER.error(f"Combined search error: {e}", exc_info=True)
                return f"Error searching: {str(e)}"
        
        bot.add_tool(
            name="search_all",
            description="Search both AccuralAI codebase/documentation AND the web simultaneously. Use this when you're not sure whether the information is in the codebase or needs to be found online. Returns results from both sources.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for both codebase and web (at least 2 characters)",
                    }
                },
                "required": ["query"],
            },
            handler=combined_search_handler,
        )

    # Sync guild commands tool
    bot.add_tool(
        name="sync_commands",
        description="Syncs Discord slash commands to the current guild/server. USE THIS FUNCTION when users ask to: sync commands, sync guild commands, update commands, refresh commands, reload commands, sync slash commands, or make commands available. This function will make new or updated slash commands appear immediately in Discord. IMPORTANT: You must actually CALL this function, not just acknowledge the request. Requires administrator permissions.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=_create_sync_handler(bot),
    )

    tools_list = ["echo", "calculate", "search_web", "sync_commands"]
    if codebase_searcher:
        tools_list.extend(["search_codebase", "search_all"])
    LOGGER.info(f"Registered test tools: {', '.join(tools_list)}")


async def print_analytics_periodically(bot: DiscordBot) -> None:
    """Periodically print analytics (every 5 minutes)."""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        analytics = bot.get_analytics()
        if analytics:
            summary = analytics.get_summary()
            LOGGER.info("Analytics Summary:")
            LOGGER.info(f"  Uptime: {summary['uptime_hours']:.2f} hours")
            LOGGER.info(f"  Total Messages: {summary['total_messages']}")
            LOGGER.info(f"  AI Responses: {summary['total_ai_responses']}")
            LOGGER.info(f"  Cache Hit Rate: {summary['cache_hit_rate']:.2%}")
            LOGGER.info(f"  Avg Latency: {summary['average_latency_ms']}ms")


def main() -> None:
    """Main entry point for test bot."""
    LOGGER.info("Starting AccuralAI Discord Test Bot...")

    # Load configuration
    config_dict = load_env_config()
    config = DiscordBotConfig(**config_dict)

    # Print configuration
    LOGGER.info("Configuration:")
    LOGGER.info(f"  Personality: {config.personality or 'default'}")
    LOGGER.info(f"  Conversation Scope: {config.conversation_scope}")
    LOGGER.info(f"  Tool Calling: {config.enable_tool_calling}")
    LOGGER.info(f"  Multi-Modal: {config.enable_multimodal}")
    LOGGER.info(f"  Context Aware: {config.context_aware}")
    LOGGER.info(f"  Analytics: {config.enable_analytics}")
    LOGGER.info(f"  Debug Logging: {config.debug}")
    # Note about mention filtering
    if config_dict.get("bot_user_id"):
        LOGGER.info(f"  Bot User ID: {config_dict['bot_user_id']} (mention-only mode enabled)")
    else:
        LOGGER.info("  Mention-only mode: Bot will only respond when mentioned")

    # Initialize codebase searcher
    # Find the root of the AccuralAI repository
    # Assuming test_bot.py is in packages/accuralai-discord/accuralai_discord/
    current_file = Path(__file__).resolve()
    # Go up to repository root: packages/accuralai-discord/accuralai_discord/test_bot.py -> repo root
    repo_root = current_file.parent.parent.parent.parent
    LOGGER.info(f"Using repository root: {repo_root}")
    
    codebase_searcher = WebCodebaseSearch(repo_root)

    # Create bot
    bot = DiscordBot(config=config)

    # Add mention-only filtering hook
    # The bot only responds when it is mentioned in the message
    @bot.on_message_preprocess
    async def mention_only_filter(message: discord.Message, context: dict) -> str | None:
        """
        Only process messages where the bot is mentioned.
        
        Returns:
            Message content if bot is mentioned, None otherwise
        """
        LOGGER.debug(f"Mention-only filter called for message from {message.author.id}: '{message.content[:50]}...'")
        # Wait for bot client to be ready
        if not bot._client or not bot._client.user:
            # If bot isn't ready yet, we can't check mentions, so skip
            LOGGER.debug("Bot client not ready, skipping message")
            return None
        
        # Get bot user ID (from config or client.user.id)
        bot_user_id = config_dict.get("bot_user_id")
        if not bot_user_id:
            bot_user_id = bot._client.user.id
        
        # Check if bot is mentioned in the message
        bot_mentioned = False
        if message.mentions:
            # Check if bot is in the mentions list
            bot_mentioned = any(user.id == bot_user_id for user in message.mentions)
        
        # Also check message content for mention pattern (in case mentions aren't parsed)
        if not bot_mentioned and message.content:
            import re
            mention_pattern = r"<@!?(\d+)>"
            mentioned_user_ids = re.findall(mention_pattern, message.content)
            bot_mentioned = str(bot_user_id) in mentioned_user_ids
        
        # Only process if bot is mentioned
        if not bot_mentioned:
            LOGGER.debug(
                f"Ignoring message from {message.author.id} ({message.author.name}): "
                f"bot not mentioned"
            )
            return None  # Don't process this message
        
        LOGGER.debug(
            f"Processing message from {message.author.id} ({message.author.name}): "
            f"bot mentioned"
        )
        
        # Return content to continue processing
        return message.content

    # Setup test tools with codebase searcher
    setup_test_tools(bot, codebase_searcher)

    # Add custom command example
    @bot.command("/test", description="Test command")
    async def test_command(ctx):
        return "Test command executed successfully! ✅"

    # Add custom command for analytics
    @bot.command("/analytics", description="Show bot analytics")
    async def analytics_command(ctx):
        analytics = bot.get_analytics()
        if not analytics:
            return "Analytics not enabled."

        summary = analytics.get_summary()
        lines = [
            "**Bot Analytics:**",
            f"Uptime: {summary['uptime_hours']:.2f} hours",
            f"Total Messages: {summary['total_messages']}",
            f"Total Commands: {summary['total_commands']}",
            f"AI Responses: {summary['total_ai_responses']}",
            f"Total Tokens: {summary['total_tokens']}",
            f"Cache Hit Rate: {summary['cache_hit_rate']:.2%}",
            f"Average Latency: {summary['average_latency_ms']}ms",
            f"Errors: {summary['total_errors']}",
        ]

        if summary.get("top_users"):
            lines.append("\n**Top Users:**")
            for user_id, count in summary["top_users"].items():
                lines.append(f"  <@{user_id}>: {count} interactions")

        return "\n".join(lines)

    # Add attachment processing command
    @bot.command("/process-attachments", description="Process and analyze message attachments")
    async def process_attachments_command(ctx):
        if not ctx.message.attachments:
            return "No attachments found in this message."
        
        try:
            attachments = await process_all_attachments(ctx.message)
            summary = format_attachments_summary(attachments)
            return f"**Processed {len(attachments)} attachment(s):**{summary}"
        except Exception as e:
            return f"❌ Error processing attachments: {str(e)}"

    # Add web search slash command
    @app_commands.command(name="search", description="Search the web using Google Search")
    @app_commands.describe(query="Search query", max_results="Maximum number of results (1-10)")
    async def search_command(interaction: discord.Interaction, query: str, max_results: app_commands.Range[int, 1, 10] = 5) -> None:
        """Web search slash command."""
        await interaction.response.defer()
        
        try:
            # Get config path from bot's config
            config_path = bot._config.accuralai_config_path if hasattr(bot, '_config') else None
            results = await search_web(query, max_results=max_results, config_path=config_path)
            formatted = format_search_results(results)
            
            # Split if too long
            # Use utility function to split messages with 3-message limit (6000 chars total)
            from .utils import split_discord_message
            chunks = split_discord_message(formatted, max_size=2000, max_messages=3)
            for current_chunk in chunks:
                await interaction.followup.send(current_chunk)
        except Exception as e:
            await interaction.followup.send(f"❌ Search error: {str(e)}", ephemeral=True)
    
    # Register the command
    if bot._slash_registry and bot._slash_registry._tree:
        bot._slash_registry._tree.add_command(search_command)
    else:
        # Will be registered when tree is set up
        async def register_search():
            if bot._slash_registry and bot._slash_registry._tree:
                bot._slash_registry._tree.add_command(search_command)
        if not hasattr(bot, "_pending_slash_commands"):
            bot._pending_slash_commands = []
        bot._pending_slash_commands.append(register_search)

    # Add guild command sync slash command (for easy testing)
    @bot.slash_command("sync-commands", "Sync slash commands to this guild (admin only)", guild_id=None)
    @app_commands.describe(force="Force sync even if commands haven't changed")
    async def sync_commands_handler(interaction: discord.Interaction, force: bool = False) -> None:
        """Sync commands to the current guild for instant updates."""
        # Check if user has admin permissions
        if not interaction.guild or not interaction.user:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not member.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to sync commands.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            await bot.sync_slash_commands(guild=interaction.guild)
            await interaction.followup.send(
                f"✅ Commands synced to **{interaction.guild.name}**!\n"
                "Commands should appear immediately. Try typing `/` to see them.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to sync commands: {str(e)}", ephemeral=True)

    # Add attachment info slash command
    @app_commands.command(name="attachment-info", description="Get information about message attachments")
    @app_commands.describe(message_id="Message ID with attachments (leave empty for recent message)")
    async def attachment_info_handler(interaction: discord.Interaction, message_id: str | None = None) -> None:
        """Get detailed information about attachments."""
        await interaction.response.defer()
        
        try:
            target_message = None
            if message_id:
                try:
                    msg_id_int = int(message_id)
                    target_message = await interaction.channel.fetch_message(msg_id_int)
                except (ValueError, discord.NotFound):
                    await interaction.followup.send(f"❌ Message {message_id} not found.", ephemeral=True)
                    return
            else:
                # Get recent messages to find one with attachments
                async for msg in interaction.channel.history(limit=10):
                    if msg.attachments:
                        target_message = msg
                        break
            
            if not target_message or not target_message.attachments:
                await interaction.followup.send("❌ No attachments found in recent messages.", ephemeral=True)
                return
            
            attachments = await process_all_attachments(target_message)
            summary = format_attachments_summary(attachments)
            
            embed = discord.Embed(
                title=f"Attachment Info ({len(attachments)} file(s))",
                description=summary[:4096],
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"From message by {target_message.author.display_name}")
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    # Register attachment info command
    if bot._slash_registry and bot._slash_registry._tree:
        bot._slash_registry._tree.add_command(attachment_info_handler)
    else:
        async def register_attachment_info():
            if bot._slash_registry and bot._slash_registry._tree:
                bot._slash_registry._tree.add_command(attachment_info_handler)
        if not hasattr(bot, "_pending_slash_commands"):
            bot._pending_slash_commands = []
        bot._pending_slash_commands.append(register_attachment_info)

    # Add message handler for attachment processing
    @bot.on_message_preprocess
    async def process_attachments_hook(message, context):
        """Process attachments in messages."""
        if message.attachments and config.enable_multimodal:
            try:
                attachments = await process_all_attachments(message)
                if attachments:
                    summary = format_attachments_summary(attachments)
                    # Add attachment info to message content for AI context
                    return message.content + summary
            except Exception as e:
                LOGGER.warning(f"Failed to process attachments: {e}")
        return message.content

    # Run bot
    LOGGER.info("Bot is starting...")
    LOGGER.info("Test bot features:")
    LOGGER.info("  - Mention-only responses (bot must be mentioned)")
    LOGGER.info("  - Codebase search (RAG) for AccuralAI documentation")
    LOGGER.info("  - Web search for current information")
    LOGGER.info("  - Combined search (codebase + web)")
    LOGGER.info("  - Attachment processing (images, videos, code, text files)")
    LOGGER.info("  - Web search (/search slash command)")
    LOGGER.info("  - Guild command syncing (/sync-commands slash command)")
    LOGGER.info("  - Attachment info (/attachment-info slash command)")
    
    try:
        # Start analytics task after bot starts (in on_ready)
        if config.enable_analytics:
            # Monkey-patch the _setup_client to add analytics task
            original_setup = bot._setup_client
            
            def setup_with_analytics():
                client = original_setup()
                
                # Add another on_ready handler (discord.py supports multiple handlers)
                # This will be called in addition to the original one
                @client.event
                async def on_ready():
                    # Start analytics task now that event loop is running
                    asyncio.create_task(print_analytics_periodically(bot))
                    
                    # Initialize codebase index (runs in background)
                    # TODO: Re-enable after fixing blocking issue
                    # async def init_codebase():
                    #     try:
                    #         await codebase_searcher.initialize()
                    #         LOGGER.info("Codebase index initialized successfully")
                    #     except Exception as e:
                    #         LOGGER.error(f"Failed to initialize codebase index: {e}", exc_info=True)
                    
                    # Start codebase index initialization as background task
                    # asyncio.create_task(init_codebase())
                
                return client
            
            bot._setup_client = setup_with_analytics
        
        bot.run()
    except KeyboardInterrupt:
        LOGGER.info("Bot stopped by user")
    except Exception as e:
        LOGGER.error(f"Bot error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

