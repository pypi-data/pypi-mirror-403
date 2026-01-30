# AccuralAI Discord Bot Features

Comprehensive feature documentation for the AccuralAI Discord bot package.

## Core Features

### 1. Conversation Memory

Persistent conversation history with configurable scopes:

- **Per-Channel**: All users share context in a channel
- **Per-User**: Each user has isolated context across channels
- **Per-Thread**: Each Discord thread maintains separate context
- **Per-Channel-User**: Isolated context per user within each channel

Memory is stored using AccuralAI cache, supporting both in-memory and disk persistence.

### 2. Tool/Function Calling

Register custom tools that the AI can call during conversations:

```python
bot.add_tool(
    name="search_codebase",
    description="Search AccuralAI codebase",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"}
        },
        "required": ["query"]
    },
    handler=async lambda query, context: search_results
)
```

Tools are automatically included in the AI's available functions and called when relevant.

### 3. Multi-Modal Support

Process images and file attachments:

- Images are automatically extracted and included in AI requests
- File attachments are processed and analyzed
- Support for code files, text files, and media

### 4. Context Awareness

Automatically includes Discord context in prompts:

- User roles and permissions
- Channel information
- Guild/server context
- Message metadata

### 5. Smart History Management

Intelligent conversation history management:

- Summarization of old messages
- Relevance-based pruning
- Token-aware truncation
- Preserves important context

### 6. Analytics & Telemetry

Built-in usage tracking:

- Message counts
- Response latency
- Cache hit rates
- Token usage
- Error rates
- Top users

### 7. Streaming Responses

Support for streaming responses with typing indicators (requires backend support).

### 8. Rate Limiting

Per-context rate limiting to prevent abuse:

- Configurable requests per minute
- Separate limits per conversation context
- Graceful error messages when limits exceeded

### 9. Error Handling

User-friendly error handling:

- Automatic error formatting
- Detailed logging for debugging
- Graceful degradation
- Clear error messages

### 10. Event Hooks

Pre and post-processing hooks for customization:

```python
@bot.on_message_preprocess
async def preprocess(message, context):
    # Modify message before processing
    pass

@bot.on_message_postprocess
async def postprocess(response, message, context):
    # Modify response before sending
    pass
```

## Advanced Features

### Slash Commands

Modern Discord application commands:

```python
@bot.slash_command("ping", "Ping the bot")
async def ping_handler(interaction: discord.Interaction) -> str:
    return "Pong!"
```

### Prefix Commands

Traditional text-based commands:

```python
@bot.command("/help")
async def help_command(ctx):
    return "Available commands: ..."
```

### Rich Embeds

Formatted Discord embeds for responses:

- Automatic embed creation
- Metadata display
- Code blocks
- Rich formatting

### Custom Commands

Easy command registration:

```python
# Prefix command
bot.add_command("/greet", greet_handler, "Greet a user")

# Slash command
bot.add_slash_command("greet", "Greet a user", greet_handler)
```

## Test Bot Features

The included test bot adds additional features:

### Codebase Search (RAG)

Search through AccuralAI documentation and codebase:

- Indexes markdown files
- Searches Python code
- Finds configuration files
- Provides relevant snippets

### Web Search

Search the internet for current information:

- Google Search grounding integration (via Google GenAI SDK)
- Current news and information
- General knowledge queries
- Real-time web content with citations

### Combined Search

Search both codebase and web simultaneously for comprehensive answers.

### Attachment Processing

Advanced attachment handling:

- Image analysis
- Code file reading
- Text file processing
- Video metadata extraction

## Configuration Features

### Environment Variables

Full configuration via environment variables for easy deployment.

### Configuration Files

TOML-based configuration for complex setups.

### Runtime Configuration

Programmatic configuration via DiscordBotConfig object.

## Integration Features

### AccuralAI Orchestration

Seamless integration with AccuralAI orchestration pipeline:

- Automatic cache integration
- Backend routing
- Response validation
- Post-processing hooks

### Extensibility

Plugin-based architecture:

- Custom tools
- Custom commands
- Event hooks
- Middleware support

