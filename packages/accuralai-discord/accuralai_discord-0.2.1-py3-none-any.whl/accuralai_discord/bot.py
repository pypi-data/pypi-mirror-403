"""Main DiscordBot class."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional
from uuid import uuid4

import discord
from accuralai_core.config.loader import load_settings
from accuralai_core.core.orchestrator import CoreOrchestrator
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage
from accuralai_core.contracts.protocols import EventPublisher

from .commands.builtin import BuiltinCommands
from .commands.registry import CommandContext, CommandHandler, CommandRegistry
from .commands.slash import SlashCommandRegistry, slash_command
from .config import DiscordBotConfig
from .context import extract_context_from_message
from .memory import ConversationMemory
from .middleware.error_handler import ErrorHandler
from .middleware.rate_limit import RateLimiter
from .utils import build_system_prompt, clean_discord_message
from .tools import ToolRegistry, ToolExecutor
from .analytics import BotAnalytics
from .context_aware import build_discord_context, enhance_system_prompt_with_context, build_contextual_prompt
from .multimodal import enhance_request_with_attachments, format_attachment_info
from .embeds import create_response_embed
from .smart_history import SmartHistoryManager

LOGGER = logging.getLogger("accuralai.discord")


class DiscordBot:
    """High-level Discord bot with AccuralAI integration."""

    def __init__(
        self,
        token: str | None = None,
        *,
        config: DiscordBotConfig | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Discord bot.

        Args:
            token: Discord bot token (can be provided via config instead)
            config: Bot configuration object
            **kwargs: Additional config parameters (merged into config)
        """
        # Build config from kwargs or use provided
        if config is None:
            if token:
                kwargs["token"] = token
            config = DiscordBotConfig(**kwargs)

        self._config = config
        self._client: discord.Client | None = None
        self._orchestrator: CoreOrchestrator | None = None
        self._memory: ConversationMemory | None = None
        self._command_registry = CommandRegistry(prefix=config.command_prefix)
        self._slash_registry = SlashCommandRegistry() if config.enable_slash_commands else None
        self._rate_limiter = RateLimiter(
            requests_per_minute=config.rate_limit_per_minute
        )
        self._error_handler = ErrorHandler()

        # Configure logging based on debug flag
        self._setup_logging()

        # Enhanced features
        self._tool_registry = ToolRegistry() if config.enable_tool_calling else None
        self._tool_executor = ToolExecutor(self._tool_registry) if self._tool_registry else None
        self._analytics = BotAnalytics() if config.enable_analytics else None
        self._smart_history = SmartHistoryManager(
            max_entries=config.max_history_entries,
            max_tokens=config.max_history_tokens,
        ) if config.smart_history else None

        # Event hooks
        self._preprocess_hooks: List[Callable] = []
        self._postprocess_hooks: List[Callable] = []

        # Initialize built-in commands
        if config.enable_builtin_commands:
            self._register_builtin_commands()

    def _setup_logging(self) -> None:
        """Configure logging based on debug flag."""
        logger = logging.getLogger("accuralai.discord")
        root_logger = logging.getLogger()
        
        # Disable propagation to root logger if basicConfig was called (has handlers)
        # This prevents duplicate messages when both root and child loggers have handlers
        if root_logger.handlers:
            logger.propagate = False
        
        if self._config.debug:
            logger.setLevel(logging.DEBUG)
            # Also set discord.py logger to DEBUG if debug is enabled
            logging.getLogger("discord").setLevel(logging.DEBUG)
            # Set core and google loggers to DEBUG for comprehensive debugging
            logging.getLogger("accuralai.core").setLevel(logging.DEBUG)
            logging.getLogger("accuralai.google").setLevel(logging.DEBUG)
            # Only add handler if one doesn't exist and root logger doesn't have handlers
            # (root logger handler from basicConfig will handle messages if it exists)
            if not logger.handlers and not root_logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    )
                )
                logger.addHandler(handler)
            logger.debug("Debug logging enabled")
        else:
            logger.setLevel(logging.INFO)

    def _register_builtin_commands(self) -> None:
        """Register built-in commands."""
        builtin = BuiltinCommands(self)
        self._command_registry.register(
            "help", builtin.help_command, "Show available commands"
        )
        self._command_registry.register(
            "reset", builtin.reset_command, "Clear conversation history"
        )
        self._command_registry.register(
            "personality",
            builtin.personality_command,
            "View or update bot personality",
        )
        self._command_registry.register(
            "status", builtin.status_command, "Show bot status"
        )
        
        # Register built-in slash commands if enabled
        if self._slash_registry:
            async def help_slash(interaction: discord.Interaction) -> str:
                ctx = CommandContext(
                    message=None,
                    args=[],
                    user=interaction.user,
                    channel=interaction.channel,
                    guild=interaction.guild,
                )
                return await builtin.help_command(ctx)
            
            async def reset_slash(interaction: discord.Interaction) -> None:
                # Defer immediately to prevent interaction timeout
                await interaction.response.defer(ephemeral=False)
                
                ctx = CommandContext(
                    message=None,
                    args=[],
                    user=interaction.user,
                    channel=interaction.channel,
                    guild=interaction.guild,
                )
                response = await builtin.reset_command(ctx)
                
                # Send response as followup since we deferred
                await interaction.followup.send(response)
            
            async def status_slash(interaction: discord.Interaction) -> str:
                ctx = CommandContext(
                    message=None,
                    args=[],
                    user=interaction.user,
                    channel=interaction.channel,
                    guild=interaction.guild,
                )
                return await builtin.status_command(ctx)
            
            self.add_slash_command("help", "Show available commands", help_slash)
            self.add_slash_command("reset", "Clear conversation history", reset_slash)
            self.add_slash_command("status", "Show bot status", status_slash)

    async def _conversation_loop(
        self,
        prompt: str,
        system_prompt: str | None,
        history: list[dict[str, Any]],
        metadata: dict[str, Any],
        message: discord.Message,
    ) -> tuple[str, GenerateResponse | None]:
        """
        Run conversation loop with tool calling support.
        
        Iterates until a final response is generated, handling tool calls
        and adding results to conversation history.
        
        Returns:
            Tuple of (final_response_text, final_response_object)
        """
        conversation = list(history)
        user_added = False
        pending_prompt = prompt
        loop_count = 0
        final_response: GenerateResponse | None = None
        last_request_id = None
        max_iterations = 15  # Prevent infinite loops

        LOGGER.debug(
            f"Starting conversation loop: prompt_length={len(prompt)}, "
            f"history_entries={len(history)}, metadata_keys={list(metadata.keys())}"
        )

        while loop_count < max_iterations:
            # Prepare parameters with function calling config if tools are available
            parameters: dict[str, Any] = {}
            if self._config.enable_tool_calling and self._tool_registry:
                tools = self._tool_registry.get_tools()
                if tools and "function_calling_config" not in parameters:
                    parameters["function_calling_config"] = {"mode": "AUTO"}
                    LOGGER.debug(f"Added function calling config: {len(tools)} tools available")

            # Create GenerateRequest
            # Add unique identifiers to metadata to prevent incorrect cache hits
            # Include the original user prompt and loop iteration to ensure uniqueness
            request_metadata = {
                **metadata,
                "discord_original_prompt": prompt if loop_count == 0 else metadata.get("discord_original_prompt", ""),
                "discord_loop_iteration": loop_count,
                "discord_conversation_turn": str(uuid4()) if loop_count == 0 else metadata.get("discord_conversation_turn", ""),
            }
            
            request = GenerateRequest(
                prompt=pending_prompt,
                system_prompt=system_prompt,
                history=conversation,
                metadata=request_metadata,
                parameters=parameters,
                tags=["discord", self._config.conversation_scope],
            )
            last_request_id = request.id  # Store for potential fallback response

            # Enhance with attachments if multimodal enabled
            if self._config.enable_multimodal:
                request = enhance_request_with_attachments(request, message)

            # Add tools if enabled
            if self._config.enable_tool_calling and self._tool_registry:
                request.tools = self._tool_registry.get_tools()
                LOGGER.debug(f"Added {len(request.tools)} tools to request: {[t.get('function', {}).get('name') for t in request.tools]}")

            # Generate response
            LOGGER.debug(
                f"Generating response (iteration {loop_count + 1}/{max_iterations}): "
                f"prompt_length={len(request.prompt)}, tools={len(request.tools) if request.tools else 0}, "
                f"parameters={request.parameters}, system_prompt_length={len(request.system_prompt) if request.system_prompt else 0}"
            )
            response = await self._orchestrator.generate(request)
            final_response = response
            tool_calls = response.metadata.get("tool_calls") or []

            LOGGER.debug(
                f"Response received: tokens={response.usage.prompt_tokens + response.usage.completion_tokens}, "
                f"tool_calls={len(tool_calls)}, latency={response.latency_ms}ms"
            )
            if tool_calls:
                LOGGER.debug(f"Tool calls in response: {[tc.get('name') for tc in tool_calls]}")
            else:
                LOGGER.debug("No tool calls in response - model chose not to use tools")

            # Add user message to conversation if not already added
            if not user_added:
                conversation.append({"role": "user", "content": prompt})
                user_added = True

            # Handle tool calls
            if tool_calls:
                LOGGER.debug(f"Processing {len(tool_calls)} tool call(s): {[tc.get('name') for tc in tool_calls]}")
                # Add assistant message with tool calls to conversation
                conversation.append({
                    "role": "assistant",
                    "tool_calls": tool_calls,
                })
                
                # Execute tools and add results to conversation
                tool_error = False
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name")
                    tool_id = tool_call.get("id", "")
                    arguments = tool_call.get("arguments", {})
                    
                    if isinstance(arguments, str):
                        import json
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            arguments = {}
                    
                    # Execute tool
                    context = {
                        "message": message,
                        "user": message.author,
                        "channel": message.channel,
                        "guild": message.guild,
                        "bot": self,  # Add bot instance for tool handlers
                    }
                    
                    try:
                        if self._tool_registry:
                            LOGGER.debug(f"Executing tool: {tool_name} with args: {arguments}")
                            result = await self._tool_registry.execute(
                                tool_name, arguments, context
                            )
                            # Check if result contains an error
                            has_error = False
                            if isinstance(result, list) and result and isinstance(result[0], dict):
                                has_error = result[0].get("error") is not None
                            elif isinstance(result, dict):
                                has_error = result.get("error") is not None
                            
                            if has_error:
                                LOGGER.warning(f"Tool {tool_name} returned error: {result}")
                            else:
                                LOGGER.debug(f"Tool {tool_name} executed successfully: {result}")
                            # Add tool result to conversation
                            conversation.append({
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "name": tool_name,
                                "content": str(result),
                            })
                    except Exception as e:
                        LOGGER.error(f"Tool execution error: {e}", exc_info=e)
                        LOGGER.debug(f"Tool execution failed for {tool_name}: {e}")
                        conversation.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "name": tool_name,
                            "content": f"Error: {str(e)}",
                        })
                        tool_error = True
                
                # Continue loop with prompt asking for final response
                # After tool execution, ask model to synthesize a final response
                pending_prompt = "" if loop_count < max_iterations - 1 else "Please provide a final response based on the tool results."
                loop_count += 1
                if tool_error:
                    # Stop on error to avoid infinite loops
                    LOGGER.warning("Tool error occurred, breaking loop to avoid infinite loop")
                    break
                LOGGER.debug(f"Tool calls completed, continuing loop to get final response (iteration {loop_count + 1}/{max_iterations})")
                continue
            elif self._config.enable_tool_calling and self._tool_registry and request.tools:
                # If we have tools but model didn't call any, log a warning
                LOGGER.debug(
                    f"Model did not call any tools despite having {len(request.tools)} available. "
                    f"Request prompt: {request.prompt[:100]}..."
                )

            # No tool calls - check if we have a valid final response
            output_text = response.output_text or ""
            # Check for placeholder text that indicates we need to continue
            placeholder_texts = ["[tool-call]", "[function-call]", "tool-call", "function-call"]
            is_placeholder = any(placeholder.lower() in output_text.lower() for placeholder in placeholder_texts)
            
            # If we've done tool calls and the response is empty or placeholder,
            # try to extract response from tool results first
            if loop_count > 0 and (not output_text.strip() or is_placeholder) and conversation:
                LOGGER.debug(f"Response after tool calls is empty or placeholder, checking tool results. Text: {output_text[:50] if output_text else '(empty)'}")
                # Find last tool result in conversation
                for entry in reversed(conversation):
                    if entry.get("role") == "tool":
                        tool_content = entry.get("content", "")
                        if tool_content and len(tool_content.strip()) > 10:
                            # Use tool result as response if it's substantial
                            output_text = tool_content[:2000]
                            LOGGER.debug(f"Extracted tool result as response after empty/placeholder detection")
                            break
                
                # If we still don't have a valid response after extracting from tools, continue loop
                if not output_text.strip() or is_placeholder:
                    LOGGER.debug(f"Still no valid response after tool extraction, continuing loop (iteration {loop_count + 1}/{max_iterations})")
                    loop_count += 1
                    # Continue with explicit prompt asking for final response
                    # The conversation history already includes tool results, so AI can synthesize
                    pending_prompt = "" if loop_count < max_iterations - 1 else "Please provide a final response based on the tool results above."
                    continue
            
            # We have a valid final response (either from model or extracted from tool results)
            LOGGER.debug(f"No tool calls detected, final response ready. Length: {len(output_text)}")
            if output_text.strip():
                conversation.append({
                    "role": "assistant",
                    "content": output_text,
                })
            else:
                # Even if empty, we should break to avoid infinite loops
                LOGGER.warning("Final response is empty, breaking loop to avoid infinite loop")
            break

        if loop_count >= max_iterations:
            LOGGER.warning("Conversation loop reached max iterations")
            LOGGER.debug(f"Loop terminated after {max_iterations} iterations")
        
        # If final response is placeholder or empty after tool calls, extract from tool results
        output_text = final_response.output_text if final_response else ""
        placeholder_texts = ["[tool-call]", "[function-call]", "tool-call", "function-call"]
        is_placeholder = any(placeholder.lower() in output_text.lower() for placeholder in placeholder_texts) if output_text else False
        
        # If we have tool results but response is placeholder/empty, use tool result
        if (is_placeholder or not output_text.strip()) and loop_count > 0 and conversation:
            # Find last tool result in conversation
            for entry in reversed(conversation):
                if entry.get("role") == "tool":
                    tool_name = entry.get("name", "tool")
                    tool_content = entry.get("content", "")
                    if tool_content and len(tool_content.strip()) > 10:
                        # Use tool result as response
                        output_text = tool_content[:2000]
                        LOGGER.debug(f"Using tool result '{tool_name}' as response (placeholder detected or empty)")
                        # Update final_response with tool result
                        if final_response:
                            final_response = final_response.model_copy(update={"output_text": output_text})
                        else:
                            response_id = uuid4()
                            final_response = GenerateResponse(
                                id=response_id,
                                request_id=last_request_id or response_id,
                                output_text=output_text,
                                finish_reason="stop",
                                usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                                latency_ms=0,
                            )
                        break

        # Update conversation history
        context_key = extract_context_from_message(message, self._config.conversation_scope)[0]
        await self._memory._store_history(context_key, conversation)

        # Return the output text (either from response or extracted from tool results)
        final_output = output_text if output_text.strip() else (final_response.output_text if final_response and final_response.output_text else "")
        return (final_output, final_response)

    async def _ensure_orchestrator(self) -> CoreOrchestrator:
        """Ensure orchestrator is initialized."""
        if self._orchestrator is None:
            LOGGER.debug("Initializing orchestrator")
            config_overrides = self._config.accuralai_config_overrides or {}
            config_paths = []
            if self._config.accuralai_config_path:
                config_paths.append(self._config.accuralai_config_path)
                LOGGER.debug(f"Using AccuralAI config: {self._config.accuralai_config_path}")
            
            # Log backend configuration
            if "backends" in config_overrides:
                LOGGER.debug(f"Backend overrides: {list(config_overrides.get('backends', {}).keys())}")

            # Ensure Discord-specific metadata fields are included in cache keys
            # This prevents incorrect cache hits between different user questions
            if "canonicalizer" not in config_overrides:
                config_overrides["canonicalizer"] = {}
            if "options" not in config_overrides["canonicalizer"]:
                config_overrides["canonicalizer"]["options"] = {}
            
            # Get existing cache_key_metadata_fields or use empty list
            existing_fields = config_overrides["canonicalizer"]["options"].get(
                "cache_key_metadata_fields", []
            )
            # Add Discord-specific fields if not already present
            discord_fields = [
                "discord_original_prompt",
                "discord_message_id",
                "discord_conversation_turn",
            ]
            for field in discord_fields:
                if field not in existing_fields:
                    existing_fields.append(field)
            config_overrides["canonicalizer"]["options"]["cache_key_metadata_fields"] = existing_fields

            self._orchestrator = CoreOrchestrator(
                config_overrides=config_overrides,
                config_paths=config_paths if config_paths else None,
            )
            await self._orchestrator.__aenter__()

            # Initialize memory with orchestrator's cache
            from accuralai_core.connectors.cache import load_cache

            # Use the orchestrator's registry instead of creating a new one
            registry = self._orchestrator._registry
            cache_binding = await load_cache(
                self._orchestrator._config.cache, registry
            )
            cache = cache_binding.cache if cache_binding else None

            if cache is None:
                # Fallback to memory cache
                try:
                    from accuralai_cache.memory import build_memory_cache

                    cache = await build_memory_cache()
                except ImportError:
                    # If accuralai-cache not available, create a minimal in-memory cache
                    from accuralai_core.connectors.cache import build_inmemory_cache

                    cache = await build_inmemory_cache()

            ttl_s = None
            if self._config.conversation_ttl_hours:
                ttl_s = self._config.conversation_ttl_hours * 3600

            self._memory = ConversationMemory(
                cache=cache,
                max_history_entries=self._config.max_history_entries,
                max_history_tokens=self._config.max_history_tokens,
                ttl_s=ttl_s,
            )
            LOGGER.debug(
                f"Orchestrator initialized: cache_type={type(cache).__name__}, "
                f"max_history={self._config.max_history_entries}, ttl={ttl_s}s"
            )
        else:
            LOGGER.debug("Orchestrator already initialized")

        return self._orchestrator

    def add_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
    ) -> None:
        """
        Register a tool/function for AI to call.

        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for parameters
            handler: Async handler function
        """
        if self._tool_registry:
            self._tool_registry.register(name, description, parameters, handler)

    def get_analytics(self) -> BotAnalytics | None:
        """Get analytics tracker."""
        return self._analytics

    def get_orchestrator(self) -> CoreOrchestrator | None:
        """Get the orchestrator instance (may be None if not initialized yet)."""
        return self._orchestrator

    def add_command(
        self,
        name: str,
        handler: CommandHandler | Callable[[CommandContext], Awaitable[str | None]],
        description: str | None = None,
    ) -> None:
        """
        Register a custom command.

        Args:
            name: Command name (with or without prefix)
            handler: Async handler function
            description: Optional command description
        """
        self._command_registry.register(name, handler, description)

    def command(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable:
        """
        Decorator for registering prefix-based commands.

        Args:
            name: Command name (uses function name if None)
            description: Command description
        """

        def decorator(func: CommandHandler) -> CommandHandler:
            cmd_name = name or func.__name__
            self.add_command(cmd_name, func, description)
            return func

        return decorator

    def add_slash_command(
        self,
        name: str,
        description: str,
        handler: Callable,
        *,
        guild_id: int | None = None,
        nsfw: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Register a slash command.

        Args:
            name: Command name (must be lowercase, no spaces)
            description: Command description
            handler: Async handler function taking discord.Interaction
            guild_id: Guild ID for guild-specific command (None for global)
            nsfw: Whether command is NSFW
            **kwargs: Additional app_commands parameters
        """
        if not self._slash_registry:
            LOGGER.warning("Slash commands not enabled. Enable with enable_slash_commands=True")
            return

        if guild_id:
            # Will be registered when tree is set up
            async def register_when_ready():
                await self._slash_registry.register_guild_command(
                    guild_id, name, description, handler, nsfw=nsfw, **kwargs
                )
            # Store for later registration
            if not hasattr(self, "_pending_slash_commands"):
                self._pending_slash_commands = []
            self._pending_slash_commands.append(register_when_ready)
        else:
            async def register_when_ready():
                await self._slash_registry.register_global_command(
                    name, description, handler, nsfw=nsfw, **kwargs
                )
            if not hasattr(self, "_pending_slash_commands"):
                self._pending_slash_commands = []
            self._pending_slash_commands.append(register_when_ready)

    async def sync_slash_commands(self, *, guild: discord.Guild | None = None) -> None:
        """
        Manually sync slash commands with Discord.

        Args:
            guild: Guild to sync for (None for global)
        """
        if not self._slash_registry:
            LOGGER.warning("Slash commands not enabled")
            return
        await self._slash_registry.sync_commands(guild=guild)

    def slash_command(
        self,
        name: str,
        description: str,
        *,
        guild_id: int | None = None,
        nsfw: bool = False,
        **kwargs: Any,
    ) -> Callable:
        """
        Decorator for registering slash commands.

        Args:
            name: Command name (must be lowercase, no spaces)
            description: Command description
            guild_id: Guild ID for guild-specific command (None for global)
            nsfw: Whether command is NSFW
            **kwargs: Additional app_commands parameters

        Example:
            @bot.slash_command("ping", "Ping the bot")
            async def ping_handler(interaction: discord.Interaction) -> str:
                return "Pong!"
        """
        def decorator(func: Callable) -> Callable:
            self.add_slash_command(
                name, description, func, guild_id=guild_id, nsfw=nsfw, **kwargs
            )
            return func
        return decorator

    def on_message_preprocess(
        self,
        func: Callable | None = None,
    ) -> Callable:
        """
        Register a preprocess hook.

        Hook receives (message, context_dict) and can modify message content.

        Args:
            func: Hook function
        """

        def decorator(f: Callable) -> Callable:
            self._preprocess_hooks.append(f)
            return f

        if func is None:
            return decorator
        return decorator(func)

    def on_message_postprocess(
        self,
        func: Callable | None = None,
    ) -> Callable:
        """
        Register a postprocess hook.

        Hook receives (response_text, message, context_dict) and can modify response.

        Args:
            func: Hook function
        """

        def decorator(f: Callable) -> Callable:
            self._postprocess_hooks.append(f)
            return f

        if func is None:
            return decorator
        return decorator(func)

    async def _handle_message(self, message: discord.Message) -> None:
        """Handle incoming Discord message."""
        LOGGER.debug(
            f"Received message: author={message.author}, channel={message.channel}, "
            f"content_length={len(message.content or '')}, attachments={len(message.attachments)}"
        )

        # Ignore bot messages
        if message.author.bot:
            LOGGER.debug("Ignoring bot message")
            return

        # Track analytics
        if self._analytics:
            self._analytics.record_message(message)

        # Extract context
        context_key, metadata = extract_context_from_message(
            message, self._config.conversation_scope
        )
        LOGGER.debug(f"Extracted context: key={context_key}, scope={self._config.conversation_scope}")

        # Check rate limits
        allowed, retry_after = await self._rate_limiter.check_rate_limit(context_key)
        if not allowed:
            LOGGER.debug(f"Rate limit exceeded for context {context_key}, retry after {retry_after}s")
            await message.channel.send(
                f"⏳ Rate limited. Please try again in {retry_after:.1f} seconds."
            )
            return

        # Clean message content
        content = clean_discord_message(message.content)

        # Build Discord context if enabled
        discord_context = {}
        if self._config.context_aware:
            discord_context = build_discord_context(message)

        # Enhance content with attachments if multimodal enabled
        attachment_info = ""
        if self._config.enable_multimodal and message.attachments:
            attachment_info = "\n".join(
                format_attachment_info(att) for att in message.attachments
            )
            if attachment_info:
                content += f"\n\n{attachment_info}"

        # Run preprocess hooks
        for hook in self._preprocess_hooks:
            try:
                result = await hook(message, {**metadata, **discord_context})
                # If hook returns None, skip this message (hook filtered it out)
                if result is None:
                    LOGGER.debug(f"Preprocess hook filtered out message: {hook.__name__ if hasattr(hook, '__name__') else 'unknown'}")
                    return
                # If hook returns a string (even empty), use it (allows hooks to modify content)
                # Note: Empty string is valid and means hook processed but content is empty
                if isinstance(result, str):
                    content = result
            except Exception as e:
                LOGGER.warning("Preprocess hook error", exc_info=e)

        # Check for commands
        command_name, args = self._command_registry.parse_command(content)
        if command_name:
            LOGGER.debug(f"Command detected: {command_name} with args: {args}")
            handler = self._command_registry.get_handler(command_name)
            if handler:
                try:
                    if self._analytics:
                        self._analytics.record_command(command_name)
                    ctx = CommandContext(
                        message=message,
                        args=args,
                        user=message.author,
                        channel=message.channel,
                        guild=message.guild,
                    )
                    response = await handler(ctx)
                    if response:
                        LOGGER.debug(f"Command {command_name} executed, sending response")
                        # Split command responses to respect Discord limits (max 3 messages)
                        from .utils import split_discord_message
                        response_chunks = split_discord_message(str(response), max_size=2000, max_messages=3)
                        for chunk in response_chunks:
                            await message.channel.send(chunk)
                except Exception as e:
                    LOGGER.debug(f"Command {command_name} failed: {e}")
                    if self._analytics:
                        self._analytics.record_error()
                    error_msg = self._error_handler.format_error(e, metadata)
                    # Split error messages to respect Discord limits (max 3 messages)
                    from .utils import split_discord_message
                    error_chunks = split_discord_message(error_msg, max_size=2000, max_messages=3)
                    for chunk in error_chunks:
                        await message.channel.send(chunk)
                    self._error_handler.log_error(e, metadata)
            return

        # AI conversation path
        try:
            await self._ensure_orchestrator()

            # Load conversation history
            history = await self._memory.get_history(context_key)
            LOGGER.debug(f"Loaded conversation history: {len(history)} entries for context {context_key}")

            # Apply smart history if enabled
            if self._smart_history:
                from .utils import estimate_tokens
                history = self._smart_history.prune_history(history, estimate_tokens=estimate_tokens)

            # Get available tools for system prompt
            available_tools = None
            if self._config.enable_tool_calling and self._tool_registry:
                available_tools = self._tool_registry.get_tools()
            
            # Build system prompt with tool information
            base_prompt = build_system_prompt(
                self._config.personality, 
                self._config.system_prompt,
                available_tools=available_tools
            )

            # Enhance with Discord context if enabled
            if self._config.context_aware and base_prompt and discord_context:
                system_prompt = enhance_system_prompt_with_context(base_prompt, discord_context)
            else:
                system_prompt = base_prompt

            # Debug: Log system prompt content (truncated if too long)
            if system_prompt:
                prompt_preview = system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt
                LOGGER.debug(f"System prompt preview: {prompt_preview}")
                if "sync_commands" in system_prompt.lower() or "tools" in system_prompt.lower():
                    LOGGER.debug("System prompt contains tool/sync_commands references")

            # Build contextual prompt
            if self._config.context_aware:
                prompt = build_contextual_prompt(content, message)
            else:
                prompt = content

            # Run conversation loop with tool calling support
            LOGGER.debug(f"Starting AI conversation: prompt_length={len(prompt)}, system_prompt_set={bool(system_prompt)}, system_prompt_length={len(system_prompt) if system_prompt else 0}")
            response_text, final_response = await self._conversation_loop(
                prompt=prompt,
                system_prompt=system_prompt,
                history=history,
                metadata={
                    **metadata,
                    **discord_context,
                    "discord_message_id": str(message.id),
                    "discord_channel_id": str(message.channel.id),
                },
                message=message,
            )
            LOGGER.debug(f"Conversation completed: response_length={len(response_text)}")

            # Track analytics on final response
            if self._analytics and final_response:
                cache_hit = final_response.metadata.get("cache_status") == "hit"
                self._analytics.record_ai_response(
                    prompt_tokens=final_response.usage.prompt_tokens,
                    completion_tokens=final_response.usage.completion_tokens,
                    latency_ms=final_response.latency_ms,
                    cache_hit=cache_hit,
                )

            # Run postprocess hooks
            for hook in self._postprocess_hooks:
                try:
                    result = await hook(response_text, message, {**metadata, **discord_context})
                    if result:
                        response_text = result  # Allow hooks to modify response
                except Exception as e:
                    LOGGER.warning("Postprocess hook error", exc_info=e)

            # Send response - ensure we always send something
            if not response_text or not response_text.strip():
                # If response is empty, try to extract from tool results or send fallback
                LOGGER.warning("Response text is empty, attempting to extract from tool results or send fallback")
                if final_response and final_response.metadata.get("tool_calls") and self._memory:
                    # We had tool calls, extract from last tool result
                    context_key = extract_context_from_message(message, self._config.conversation_scope)[0]
                    history = await self._memory.get_history(context_key)
                    if history:
                        for entry in reversed(history):
                            if entry.get("role") == "tool":
                                tool_content = entry.get("content", "")
                                if tool_content and len(tool_content.strip()) > 10:
                                    response_text = tool_content[:2000]
                                    LOGGER.debug(f"Extracted tool result as fallback response")
                                    break
                
                # If still empty, send a fallback message
                if not response_text or not response_text.strip():
                    response_text = "I processed your request, but didn't generate a response. Please try rephrasing your question."
                    LOGGER.warning("Sending fallback message due to empty response")
            
            if self._config.use_embeds and final_response:
                LOGGER.debug("Sending response as embed")
                # If response is too long for embed, use text messages instead (max 3 messages)
                if len(response_text) > 4096:
                    LOGGER.debug(f"Response too long for embed ({len(response_text)} chars), using text messages instead")
                    from .utils import split_discord_message
                    chunks = split_discord_message(response_text, max_size=2000, max_messages=3)
                    for chunk in chunks:
                        await message.channel.send(chunk)
                else:
                    embed = create_response_embed(final_response, show_metadata=False)
                    await message.channel.send(embed=embed)
            else:
                # Split long messages (max 3 messages, 2000 chars each = 6000 char total limit)
                from .utils import split_discord_message
                chunks = split_discord_message(response_text, max_size=2000, max_messages=3)
                LOGGER.debug(f"Sending response in {len(chunks)} chunk(s), response_length={len(response_text)}")
                if chunks:
                    for chunk in chunks:
                        await message.channel.send(chunk)
                else:
                    # Fallback if chunks is empty (shouldn't happen but just in case)
                    LOGGER.error("No chunks to send, sending empty fallback")
                    await message.channel.send("I processed your request, but couldn't generate a response. Please try again.")

            # Note: Conversation history is already updated in _conversation_loop

        except Exception as e:
            if self._analytics:
                self._analytics.record_error()
            error_msg = self._error_handler.format_error(e, metadata)
            # Split error messages to respect Discord limits (max 3 messages)
            from .utils import split_discord_message
            error_chunks = split_discord_message(error_msg, max_size=2000, max_messages=3)
            for chunk in error_chunks:
                await message.channel.send(chunk)
            self._error_handler.log_error(e, metadata)

    def _setup_client(self) -> discord.Client:
        """Setup Discord client with handlers."""
        from discord import app_commands
        
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message content
        
        LOGGER.info(f"Discord intents configured - message_content: {intents.message_content}, guild_messages: {intents.guild_messages}, messages: {intents.messages}")
        LOGGER.debug(f"Full Discord intents: {intents}")

        client = discord.Client(intents=intents)

        # Setup slash commands if enabled
        if self._slash_registry:
            tree = app_commands.CommandTree(client)
            self._slash_registry.set_tree(tree)

            @client.event
            async def on_ready() -> None:
                LOGGER.info(f"Bot logged in as {client.user}")
                LOGGER.debug(f"Bot user ID: {client.user.id}, Guilds: {len(client.guilds)}")
                
                # Register pending slash commands (direct Command objects)
                if hasattr(self, "_pending_slash_commands"):
                    LOGGER.debug(f"Registering {len(self._pending_slash_commands)} pending slash commands")
                    for register_func in self._pending_slash_commands:
                        await register_func()
                
                # Sync slash commands
                if self._config.auto_sync_slash_commands:
                    LOGGER.debug("Auto-syncing slash commands")
                    if self._config.sync_guild_commands:
                        # Sync for specific guilds
                        for guild_id in self._config.sync_guild_commands:
                            LOGGER.debug(f"Syncing commands for guild {guild_id}")
                            guild = client.get_guild(guild_id)
                            if guild:
                                await self._slash_registry.sync_commands(guild=guild)
                                LOGGER.debug(f"Synced commands for guild {guild_id}")
                            else:
                                LOGGER.warning(f"Guild {guild_id} not found, skipping sync")
                    else:
                        # Sync global commands
                        LOGGER.debug("Syncing global commands")
                        await self._slash_registry.sync_commands()
                        LOGGER.debug("Global commands synced")
                else:
                    LOGGER.info("Auto-sync disabled. Use /sync-commands in a guild to sync manually.")
        else:
            @client.event
            async def on_ready() -> None:
                LOGGER.info(f"Bot logged in as {client.user}")
                LOGGER.debug(f"Bot user ID: {client.user.id}, Guilds: {len(client.guilds)}")

        @client.event
        async def on_message(message: discord.Message) -> None:
            LOGGER.debug(f"on_message event fired: author={message.author}, content='{message.content[:50]}...'")
            await self._handle_message(message)

        return client

    def run(self, *, token: str | None = None) -> None:
        """
        Run the Discord bot.

        Args:
            token: Discord bot token (uses config token if not provided)
        """
        token = token or self._config.token
        if not token:
            raise ValueError("Discord bot token is required")

        self._client = self._setup_client()
        self._client.run(token)

    async def start(self, *, token: str | None = None) -> None:
        """
        Start the Discord bot asynchronously.

        Args:
            token: Discord bot token (uses config token if not provided)
        """
        token = token or self._config.token
        if not token:
            raise ValueError("Discord bot token is required")

        self._client = self._setup_client()
        await self._client.start(token)

    async def close(self) -> None:
        """Close the bot and cleanup resources."""
        if self._orchestrator:
            await self._orchestrator.aclose()
        if self._client:
            await self._client.close()

