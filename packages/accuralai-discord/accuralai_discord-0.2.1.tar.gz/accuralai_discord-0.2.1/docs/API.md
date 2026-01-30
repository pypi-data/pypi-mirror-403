# AccuralAI Discord Bot API Reference

Complete API documentation for the AccuralAI Discord bot package.

## DiscordBot Class

Main bot class for creating Discord bots.

### Constructor

```python
DiscordBot(
    token: str | None = None,
    *,
    config: DiscordBotConfig | None = None,
    **kwargs: Any
) -> None
```

Initialize a Discord bot instance.

**Parameters:**
- `token`: Discord bot token (can be provided via config instead)
- `config`: DiscordBotConfig object with configuration
- `**kwargs`: Additional config parameters (merged into config)

**Example:**
```python
bot = DiscordBot(
    token="DISCORD_BOT_TOKEN",
    personality="helpful assistant",
    accuralai_config_path="config.toml"
)
```

### Methods

#### `add_tool(name, description, parameters, handler)`

Register a tool/function for the AI to call during conversations.

**Parameters:**
- `name` (str): Tool name (must be unique)
- `description` (str): Tool description (used by AI to decide when to call)
- `parameters` (dict): JSON schema for tool parameters
- `handler` (Callable): Async handler function

**Example:**
```python
async def get_weather(location: str, context: dict) -> str:
    return f"Weather in {location}: Sunny, 72°F"

bot.add_tool(
    name="get_weather",
    description="Get weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"]
    },
    handler=get_weather
)
```

#### `add_command(name, handler, description=None)`

Register a custom prefix command.

**Parameters:**
- `name` (str): Command name (with or without prefix)
- `handler` (Callable): Async handler function taking CommandContext
- `description` (str | None): Optional command description

**Example:**
```python
async def greet_command(ctx):
    return f"Hello {ctx.user.name}!"

bot.add_command("/greet", greet_command, "Greet a user")
```

#### `command(name=None, description=None)`

Decorator for registering prefix commands.

**Parameters:**
- `name` (str | None): Command name (uses function name if None)
- `description` (str | None): Command description

**Example:**
```python
@bot.command("/weather", description="Get weather info")
async def weather_command(ctx):
    return "It's sunny today!"
```

#### `add_slash_command(name, description, handler, *, guild_id=None, nsfw=False, **kwargs)`

Register a Discord slash command.

**Parameters:**
- `name` (str): Command name (must be lowercase, no spaces)
- `description` (str): Command description
- `handler` (Callable): Async handler function taking discord.Interaction
- `guild_id` (int | None): Guild ID for guild-specific command (None for global)
- `nsfw` (bool): Whether command is NSFW
- `**kwargs`: Additional app_commands parameters

**Example:**
```python
async def ping_handler(interaction: discord.Interaction) -> str:
    return "Pong!"

bot.add_slash_command("ping", "Ping the bot", ping_handler)
```

#### `slash_command(name, description, *, guild_id=None, nsfw=False, **kwargs)`

Decorator for registering slash commands.

**Parameters:**
- `name` (str): Command name
- `description` (str): Command description
- `guild_id` (int | None): Guild ID for guild-specific command
- `nsfw` (bool): Whether command is NSFW
- `**kwargs`: Additional app_commands parameters

**Example:**
```python
@bot.slash_command("ping", "Ping the bot")
async def ping_slash(interaction: discord.Interaction) -> str:
    return "Pong! 🏓"
```

#### `sync_slash_commands(*, guild=None)`

Manually sync slash commands with Discord.

**Parameters:**
- `guild` (discord.Guild | None): Guild to sync for (None for global)

**Example:**
```python
await bot.sync_slash_commands(guild=my_guild)
```

#### `get_analytics() -> BotAnalytics | None`

Get analytics tracker.

**Returns:** BotAnalytics instance if analytics enabled, None otherwise

#### `on_message_preprocess(func=None)`

Register a preprocess hook.

Hook receives `(message, context_dict)` and can modify message content.

**Example:**
```python
@bot.on_message_preprocess
async def preprocess(message, context):
    # Modify message before AI processing
    return message.content.upper()
```

#### `on_message_postprocess(func=None)`

Register a postprocess hook.

Hook receives `(response_text, message, context_dict)` and can modify response.

**Example:**
```python
@bot.on_message_postprocess
async def postprocess(response, message, context):
    # Modify AI response before sending
    return f"[BOT] {response}"
```

#### `run(*, token=None)`

Run the Discord bot synchronously.

**Parameters:**
- `token` (str | None): Discord bot token (uses config token if not provided)

**Example:**
```python
bot.run()
```

#### `async start(*, token=None)`

Start the Discord bot asynchronously.

**Parameters:**
- `token` (str | None): Discord bot token (uses config token if not provided)

**Example:**
```python
await bot.start()
```

#### `async close()`

Close the bot and cleanup resources.

**Example:**
```python
await bot.close()
```

## DiscordBotConfig Class

Configuration model for Discord bot.

### Fields

- `token` (str): Discord bot token (required)
- `personality` (str | None): Short personality description
- `system_prompt` (str | None): Full system prompt (overrides personality)
- `conversation_scope` (str): How to scope conversation context
  - Options: "per-channel", "per-user", "per-thread", "per-channel-user"
- `max_history_entries` (int): Maximum conversation history entries (default: 50)
- `max_history_tokens` (int | None): Maximum tokens in conversation history
- `command_prefix` (str): Prefix for commands (default: "/")
- `rate_limit_per_minute` (int): Rate limit per context per minute (default: 20)
- `accuralai_config_path` (str | None): Path to AccuralAI configuration TOML
- `accuralai_config_overrides` (dict): AccuralAI configuration overrides
- `enable_builtin_commands` (bool): Enable built-in commands (default: True)
- `conversation_ttl_hours` (int | None): TTL in hours for conversation history
- `enable_streaming` (bool): Enable streaming responses (default: False)
- `enable_tool_calling` (bool): Enable tool/function calling (default: True)
- `enable_multimodal` (bool): Enable multi-modal support (default: True)
- `use_embeds` (bool): Use Discord embeds for responses (default: False)
- `enable_analytics` (bool): Enable analytics and telemetry (default: True)
- `smart_history` (bool): Enable smart history management (default: False)
- `context_aware` (bool): Include Discord context in prompts (default: True)
- `enable_slash_commands` (bool): Enable Discord slash commands (default: True)
- `auto_sync_slash_commands` (bool): Auto-sync slash commands on startup (default: True)
- `sync_guild_commands` (list[int]): List of guild IDs to sync commands for
- `debug` (bool): Enable debug logging (default: False)

### Example

```python
from accuralai_discord import DiscordBotConfig

config = DiscordBotConfig(
    token="DISCORD_BOT_TOKEN",
    personality="technical expert",
    conversation_scope="per-channel",
    max_history_entries=50,
    rate_limit_per_minute=20,
    accuralai_config_path="config.toml",
    enable_tool_calling=True,
    enable_multimodal=True,
    context_aware=True,
)
```

## CommandContext

Context object passed to command handlers.

### Attributes

- `message` (discord.Message | None): Discord message
- `args` (list): Parsed command arguments
- `user` (discord.User | discord.Member): Message author
- `channel` (discord.abc.Messageable): Message channel
- `guild` (discord.Guild | None): Guild/server (None in DMs)

## BotAnalytics

Analytics tracker for bot usage.

### Methods

#### `get_summary() -> dict`

Get analytics summary.

**Returns:** Dictionary with:
- `uptime_hours`: Bot uptime in hours
- `total_messages`: Total messages received
- `total_commands`: Total commands executed
- `total_ai_responses`: Total AI responses generated
- `total_tokens`: Total tokens used
- `cache_hit_rate`: Cache hit rate percentage
- `average_latency_ms`: Average response latency in milliseconds
- `total_errors`: Total errors encountered
- `top_users`: Dictionary of top users by interaction count

## Exceptions

### DiscordBotError

Base exception for Discord bot errors.

### ConfigurationError

Raised when bot configuration is invalid.

### ToolExecutionError

Raised when tool execution fails.

