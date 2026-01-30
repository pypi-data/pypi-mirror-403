# AccuralAI Discord Bot Package

High-level abstraction for building AI-powered Discord bots with minimal boilerplate, integrating seamlessly with AccuralAI orchestration.

## Quick Start

### Minimal Example

```python
from accuralai_discord import DiscordBot

# Minimal example (10 lines)
bot = DiscordBot(
    token="DISCORD_BOT_TOKEN",
    personality="friendly assistant",
    accuralai_config_path="config.toml"
)
bot.run()
```

### Test Bot (Recommended for Testing)

Use the included test bot for quick testing:

**Linux/Mac:**
```bash
export DISCORD_BOT_TOKEN="your_bot_token_here"
python -m accuralai_discord.test_bot
```

**Windows CMD:**
```cmd
set DISCORD_BOT_TOKEN=your_bot_token_here
set ACCURALAI_CONFIG_PATH=C:\path\to\config.toml
python -m accuralai_discord.test_bot
```

**Windows PowerShell:**
```powershell
$env:DISCORD_BOT_TOKEN="your_bot_token_here"
$env:ACCURALAI_CONFIG_PATH="C:\path\to\config.toml"
python -m accuralai_discord.test_bot
```

**Relative path (relative to current directory):**
```bash
export DISCORD_BOT_TOKEN="your_token"
export ACCURALAI_CONFIG_PATH="config.toml"  # or "./config.toml"
python -m accuralai_discord.test_bot
```

Or use the CLI command:
```bash
accuralai-discord-test
```

The test bot includes:
- Example tools (`echo`, `calculate`)
- Custom commands (`/test`, `/analytics`)
- Built-in analytics tracking
- Full feature configurability via environment variables

See `TEST_BOT.md` for complete documentation and environment variable reference.

## Installation

```bash
pip install accuralai-discord
```

## Features

- **Minimal Boilerplate**: Get a working bot in ~10 lines
- **AccuralAI Integration**: Automatic integration with AccuralAI orchestration pipeline
- **Conversation Memory**: Persistent conversation history with configurable scopes
- **Built-in Commands**: `/help`, `/reset`, `/personality`, `/status`
- **Custom Commands**: Easy registration of custom commands
- **Tool/Function Calling**: Register tools for AI to call during conversations
- **Multi-Modal Support**: Handle images and file attachments
- **Rich Embeds**: Formatted Discord embeds for responses
- **Context Awareness**: Automatic Discord context (roles, permissions) in prompts
- **Smart History**: Intelligent conversation history management with summarization
- **Analytics**: Built-in usage tracking and telemetry
- **Streaming Responses**: Support for streaming with typing indicators
- **Rate Limiting**: Built-in rate limiting per conversation context
- **Error Handling**: User-friendly error messages
- **Event Hooks**: Pre/post-processing hooks for customization

## Configuration

### Basic Configuration

```python
bot = DiscordBot(
    token="DISCORD_BOT_TOKEN",
    personality="technical expert",
    conversation_scope="per-user",  # or "per-channel", "per-thread"
    accuralai_config_path="accuralai-config.toml"
)
```

### Advanced Configuration

```python
from accuralai_discord import DiscordBot, DiscordBotConfig

config = DiscordBotConfig(
    token="DISCORD_BOT_TOKEN",
    personality="helpful assistant",
    conversation_scope="per-channel",
    max_history_entries=50,
    max_history_tokens=2000,
    rate_limit_per_minute=20,
    accuralai_config_path="config.toml",
    accuralai_config_overrides={
        "backends.ollama.options.model": "llama3"
    }
)

bot = DiscordBot(config=config)
bot.run()
```

## Conversation Scopes

- **per-channel**: All users in a channel share conversation history
- **per-user**: Each user has isolated context across all channels
- **per-thread**: Each Discord thread = separate conversation
- **per-channel-user**: Per user within each channel

## Custom Commands

### Prefix Commands (Text-based)

```python
@bot.command("/weather", description="Get weather info")
async def weather_command(ctx):
    return "It's sunny today!"

# Or register manually
async def custom_handler(ctx):
    return f"Hello {ctx.user.name}!"

bot.add_command("/greet", custom_handler, "Greet a user")
```

### Slash Commands (Application Commands)

Slash commands provide a modern Discord UI with autocomplete and better UX.

#### Global Slash Commands

```python
import discord

# Register a global slash command
async def ping_handler(interaction: discord.Interaction) -> str:
    return "Pong! 🏓"

bot.add_slash_command("ping", "Ping the bot", ping_handler)

# Or use decorator-style
@bot.slash_command("ping", "Ping the bot")
async def ping_slash(interaction: discord.Interaction) -> str:
    return "Pong! 🏓"
```

#### Per-Guild Slash Commands

```python
import discord

# Register a command for a specific guild (server)
async def admin_handler(interaction: discord.Interaction) -> str:
    return "Admin command executed!"

GUILD_ID = 123456789012345678  # Your guild ID
bot.add_slash_command(
    "admin", 
    "Admin-only command", 
    admin_handler,
    guild_id=GUILD_ID
)
```

#### Slash Commands with Parameters

```python
import discord

@app_commands.describe(user="The user to greet")
async def greet_handler(interaction: discord.Interaction, user: discord.Member) -> str:
    return f"Hello {user.mention}!"

bot.add_slash_command("greet", "Greet a user", greet_handler)
```

#### Configuration

Enable slash commands in your config:

```python
from accuralai_discord import DiscordBot, DiscordBotConfig

config = DiscordBotConfig(
    token="YOUR_TOKEN",
    enable_slash_commands=True,  # Enable slash commands
    auto_sync_slash_commands=True,  # Auto-sync on startup
    sync_guild_commands=[123456789012345678],  # Sync to specific guilds (optional)
)
bot = DiscordBot(config=config)
```

**Note:** Global commands can take up to 1 hour to propagate. Guild commands sync instantly.

## Event Hooks

```python
@bot.on_message_preprocess
async def preprocess(message, context):
    # Modify message before AI processing
    return message.content.upper()

@bot.on_message_postprocess
async def postprocess(response, message, context):
    # Modify AI response before sending
    return f"[BOT] {response}"
```

## Accessing Orchestrator

```python
orchestrator = bot.get_orchestrator()
# Use orchestrator directly for advanced use cases
```

## Enhanced AI Features

### Tool/Function Calling
Register custom tools that the AI can call during conversations:

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
    handler=async def get_weather(location: str, context: dict):
        # Your tool logic
        return f"Weather in {location}: Sunny"
)
```

### Multi-Modal Support
Handle images and file attachments:

```python
bot = DiscordBot(
    token="YOUR_TOKEN",
    enable_multimodal=True,  # Automatically processes images
    accuralai_config_path="config.toml"
)
```

The bot automatically includes image attachments in AI requests.

### Rich Embeds
Use Discord embeds for formatted responses:

```python
bot = DiscordBot(
    token="YOUR_TOKEN",
    use_embeds=True,  # Use embeds instead of plain text
    accuralai_config_path="config.toml"
)
```

### Context Awareness
Bot automatically includes Discord context (roles, permissions, channel info):

```python
bot = DiscordBot(
    token="YOUR_TOKEN",
    context_aware=True,  # Include Discord metadata in prompts
    accuralai_config_path="config.toml"
)
```

### Analytics & Telemetry
Track bot usage and performance:

```python
analytics = bot.get_analytics()
summary = analytics.get_summary()
print(f"Total messages: {summary['total_messages']}")
print(f"Cache hit rate: {summary['cache_hit_rate']}")
```

### Smart History Management
Enable intelligent conversation history management:

```python
bot = DiscordBot(
    token="YOUR_TOKEN",
    smart_history=True,  # Enable summarization and relevance-based pruning
    accuralai_config_path="config.toml"
)
```

### Streaming Responses
Stream responses with typing indicators (requires backend support):

```python
from accuralai_discord import stream_response

# In your custom handler
async def stream_handler(response_stream):
    await stream_response(
        channel=message.channel,
        response_stream=response_stream,
        show_typing=True
    )
```

## CLI Usage

You can also run the bot from the command line:

```bash
accuralai-discord-bot --token YOUR_TOKEN --personality "friendly assistant"
```

Or with a configuration file:

```bash
accuralai-discord-bot --config bot-config.toml
```

## Error Handling

The bot includes built-in error handling for:
- AccuralAI pipeline errors
- Discord API errors
- Rate limiting
- Network issues

Errors are automatically formatted into user-friendly messages.

## Architecture

The bot integrates with AccuralAI's orchestration pipeline:

1. **Message Reception**: Discord messages are received via `discord.py`
2. **Context Extraction**: Conversation context is determined by scope
3. **Rate Limiting**: Per-context rate limits are enforced
4. **Command Parsing**: Commands are routed to handlers
5. **AI Generation**: Non-command messages are sent to AccuralAI orchestrator
6. **Memory Management**: Conversation history is stored using AccuralAI cache
7. **Response Delivery**: AI responses are sent back to Discord

## Configuration Files

### Bot Configuration (TOML)

```toml
[discord]
token = "${DISCORD_BOT_TOKEN}"
personality = "helpful assistant"
conversation_scope = "per-channel"
max_history_entries = 50
rate_limit_per_minute = 20

[discord.accuralai]
config_path = "accuralai-config.toml"
overrides = { "backends.ollama.options.model" = "llama3" }
```

## Examples

### Simple Q&A Bot

```python
from accuralai_discord import DiscordBot

bot = DiscordBot(
    token="YOUR_TOKEN",
    personality="knowledgeable assistant",
    accuralai_config_path="config.toml"
)
bot.run()
```

### Bot with Custom Commands

```python
from accuralai_discord import DiscordBot

bot = DiscordBot(
    token="YOUR_TOKEN",
    personality="helpful bot",
    accuralai_config_path="config.toml"
)

@bot.command("/ping")
async def ping(ctx):
    return "Pong!"

@bot.command("/info")
async def info(ctx):
    return f"Hello {ctx.user.name}! I'm a helpful bot."

bot.run()
```

### Bot with Custom Hooks

```python
from accuralai_discord import DiscordBot

bot = DiscordBot(
    token="YOUR_TOKEN",
    personality="friendly assistant",
    accuralai_config_path="config.toml"
)

@bot.on_message_preprocess
async def log_messages(message, context):
    print(f"User {context['user_id']} said: {message.content}")
    return None  # Don't modify message

@bot.on_message_postprocess
async def add_prefix(response, message, context):
    return f"🤖 {response}"

bot.run()
```

## Testing

Run tests with:

```bash
pytest tests/
```

## License

Apache-2.0

## Documentation

See the [AccuralAI documentation](https://accuralai.readthedocs.io/) for more details.

