# AccuralAI Discord Bot Documentation

Complete guide to using and configuring the AccuralAI Discord bot package.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Features](#features)
5. [API Reference](#api-reference)
6. [Advanced Usage](#advanced-usage)
7. [Test Bot](#test-bot)
8. [Troubleshooting](#troubleshooting)

## Quick Start

The fastest way to get started is using the test bot:

```bash
export DISCORD_BOT_TOKEN="your_bot_token_here"
python -m accuralai_discord.test_bot
```

For a custom bot:

```python
from accuralai_discord import DiscordBot

bot = DiscordBot(
    token="DISCORD_BOT_TOKEN",
    personality="helpful assistant",
    accuralai_config_path="config.toml"
)
bot.run()
```

## Installation

### From PyPI

```bash
pip install accuralai-discord
```

### From Source

```bash
git clone https://github.com/AccuralAI/accuralai-discord.git
cd accuralai-discord
pip install -e .
```

### Dependencies

- Python 3.10+
- discord.py >= 2.3
- accuralai-core
- pydantic >= 2.5
- aiohttp >= 3.9

## Configuration

### Environment Variables

The test bot can be configured via environment variables:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DISCORD_BOT_TOKEN` | Discord bot token | Yes | - |
| `ACCURALAI_CONFIG_PATH` | Path to AccuralAI config TOML | No | - |
| `DISCORD_BOT_PERSONALITY` | Bot personality description | No | "helpful assistant" |
| `DISCORD_BOT_SCOPE` | Conversation scope | No | "per-channel" |
| `DISCORD_ENABLE_STREAMING` | Enable streaming responses | No | "false" |
| `DISCORD_ENABLE_TOOLS` | Enable tool calling | No | "true" |
| `DISCORD_ENABLE_MULTIMODAL` | Enable multi-modal support | No | "true" |
| `DISCORD_USE_EMBEDS` | Use Discord embeds | No | "false" |
| `DISCORD_ENABLE_ANALYTICS` | Enable analytics | No | "true" |
| `DISCORD_SMART_HISTORY` | Enable smart history | No | "false" |
| `DISCORD_CONTEXT_AWARE` | Enable context awareness | No | "true" |
| `DISCORD_DEBUG` | Enable debug logging | No | "false" |
| `DISCORD_RATE_LIMIT` | Rate limit per minute | No | 20 |
| `DISCORD_MAX_HISTORY` | Max history entries | No | 50 |

### Configuration Object

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
)
```

## Features

### Conversation Scopes

- **per-channel**: All users in a channel share conversation history
- **per-user**: Each user has isolated context across all channels
- **per-thread**: Each Discord thread = separate conversation
- **per-channel-user**: Per user within each channel

### Built-in Commands

- `/help` - Show available commands
- `/reset` - Clear conversation history
- `/personality` - View or update bot personality
- `/status` - Show bot status

### Custom Commands

Register prefix commands:

```python
@bot.command("/weather", description="Get weather info")
async def weather_command(ctx):
    return "It's sunny today!"
```

Or slash commands:

```python
@bot.slash_command("ping", "Ping the bot")
async def ping_slash(interaction: discord.Interaction) -> str:
    return "Pong! 🏓"
```

### Tool/Function Calling

Register tools for the AI to call:

```python
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
    handler=lambda location, context: f"Weather in {location}: Sunny"
)
```

### Multi-Modal Support

The bot automatically processes image attachments when `enable_multimodal=True`:

```python
bot = DiscordBot(
    token="YOUR_TOKEN",
    enable_multimodal=True,
    accuralai_config_path="config.toml"
)
```

### Rich Embeds

Use Discord embeds for formatted responses:

```python
bot = DiscordBot(
    token="YOUR_TOKEN",
    use_embeds=True,
    accuralai_config_path="config.toml"
)
```

### Context Awareness

Automatically includes Discord context (roles, permissions, channel info):

```python
bot = DiscordBot(
    token="YOUR_TOKEN",
    context_aware=True,
    accuralai_config_path="config.toml"
)
```

### Analytics

Track bot usage and performance:

```python
analytics = bot.get_analytics()
summary = analytics.get_summary()
print(f"Total messages: {summary['total_messages']}")
print(f"Cache hit rate: {summary['cache_hit_rate']}")
```

## API Reference

### DiscordBot

Main bot class.

#### `__init__(token=None, *, config=None, **kwargs)`

Initialize Discord bot.

**Parameters:**
- `token`: Discord bot token (can be provided via config)
- `config`: DiscordBotConfig object
- `**kwargs`: Additional config parameters

#### `add_tool(name, description, parameters, handler)`

Register a tool for AI to call.

**Parameters:**
- `name`: Tool name
- `description`: Tool description
- `parameters`: JSON schema for parameters
- `handler`: Async handler function

#### `add_command(name, handler, description=None)`

Register a custom command.

#### `run(token=None)`

Run the Discord bot synchronously.

#### `async start(token=None)`

Start the Discord bot asynchronously.

### DiscordBotConfig

Configuration model for Discord bot.

**Fields:**
- `token`: Discord bot token
- `personality`: Short personality description
- `system_prompt`: Full system prompt (overrides personality)
- `conversation_scope`: How to scope conversation context
- `max_history_entries`: Maximum conversation history entries
- `rate_limit_per_minute`: Rate limit per context per minute
- `accuralai_config_path`: Path to AccuralAI configuration TOML
- `enable_tool_calling`: Enable tool/function calling
- `enable_multimodal`: Enable multi-modal support
- `use_embeds`: Use Discord embeds for responses
- `enable_analytics`: Enable analytics and telemetry
- And more...

## Advanced Usage

### Event Hooks

Preprocess messages:

```python
@bot.on_message_preprocess
async def preprocess(message, context):
    # Modify message before AI processing
    return message.content.upper()
```

Postprocess responses:

```python
@bot.on_message_postprocess
async def postprocess(response, message, context):
    # Modify AI response before sending
    return f"[BOT] {response}"
```

### Memory Management

Conversation memory is automatically managed using AccuralAI cache. History persists across bot restarts when using disk cache.

### Rate Limiting

Rate limits are enforced per conversation context (channel, user, or thread depending on scope).

### Error Handling

Built-in error handling provides user-friendly error messages and logs detailed errors for debugging.

## Test Bot

The test bot (`accuralai_discord.test_bot`) is a fully-featured example bot that includes:

- Example tools (echo, calculate)
- Web search integration
- Codebase search (RAG) for AccuralAI documentation
- Attachment processing
- Analytics tracking
- Custom commands

### Running the Test Bot

```bash
# Set environment variables
export DISCORD_BOT_TOKEN="your_token_here"
export ACCURALAI_CONFIG_PATH="path/to/config.toml"  # Optional

# Run the bot
python -m accuralai_discord.test_bot
```

### Test Bot Features

- **Mention-only mode**: Configure to only respond when specific users are mentioned
- **Codebase search**: RAG search through AccuralAI documentation
- **Web search**: Search the internet for current information
- **Combined search**: Search both codebase and web simultaneously
- **Attachment processing**: Automatically process images, videos, code files
- **Analytics**: Built-in usage tracking

## Troubleshooting

### Bot Not Responding

1. Check that `DISCORD_BOT_TOKEN` is set correctly
2. Verify bot has proper permissions in the server
3. Check if mention-only filtering is enabled
4. Review debug logs with `DISCORD_DEBUG=true`

### Tool Calling Not Working

1. Ensure `enable_tool_calling=True` in config
2. Verify tools are registered before bot runs
3. Check backend supports function calling
4. Review tool descriptions are clear and specific

### Memory Issues

1. Reduce `max_history_entries` if using too much memory
2. Enable `smart_history` for intelligent pruning
3. Use disk cache for persistent memory
4. Set `conversation_ttl_hours` to expire old conversations

### Rate Limiting

1. Increase `rate_limit_per_minute` if needed
2. Check if multiple contexts are hitting limits
3. Review rate limit logs

For more help, see the [GitHub Issues](https://github.com/AccuralAI/accuralai-discord/issues).

