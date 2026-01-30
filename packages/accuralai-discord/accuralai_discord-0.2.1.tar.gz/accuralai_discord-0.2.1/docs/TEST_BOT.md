# Test Bot Documentation

Complete guide to using the AccuralAI Discord test bot.

## Overview

The test bot (`accuralai_discord.test_bot`) is a fully-featured example Discord bot that demonstrates all features of the AccuralAI Discord package. It includes:

- Codebase search (RAG) for AccuralAI documentation
- Web search integration
- Attachment processing
- Example tools
- Analytics tracking
- Custom commands

## Quick Start

### Prerequisites

1. Python 3.10 or higher
2. Discord bot token
3. AccuralAI config file (optional)

### Installation

If installed from source:

```bash
cd packages/accuralai-discord
pip install -e .
```

If installed from PyPI:

```bash
pip install accuralai-discord
```

### Running the Bot

**Linux/Mac:**
```bash
export DISCORD_BOT_TOKEN="your_bot_token_here"
export ACCURALAI_CONFIG_PATH="path/to/config.toml"  # Optional
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

Or use the CLI command:
```bash
accuralai-discord-test
```

## Configuration

### Environment Variables

All configuration is done via environment variables:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DISCORD_BOT_TOKEN` | Discord bot token | Yes | - |
| `ACCURALAI_CONFIG_PATH` | Path to AccuralAI config TOML | No | - |
| `DISCORD_BOT_PERSONALITY` | Bot personality description | No | See below |
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

### Default Personality

If `DISCORD_BOT_PERSONALITY` is not set, the bot uses:

```
helpful AI assistant specialized in AccuralAI. 
You have access to search tools including web search and codebase search for AccuralAI documentation. 
Use search_codebase to find information in the AccuralAI codebase, documentation, README files, and code. 
Use search_web for current information, news, or general knowledge not in the codebase. 
Use search_all to search both simultaneously. 
Always search for relevant information before answering questions about AccuralAI or technical topics.
```

### Conversation Scopes

- `per-channel`: All users in a channel share conversation history
- `per-user`: Each user has isolated context across all channels
- `per-thread`: Each Discord thread = separate conversation
- `per-channel-user`: Per user within each channel

## Features

### 1. Codebase Search (RAG)

The test bot automatically indexes the AccuralAI codebase and documentation when it starts. This allows the bot to search through:

- Markdown files (`.md`, `.rst`)
- Python code (`.py`)
- Configuration files (`.toml`, `.txt`)
- README files
- Documentation

The bot can use the `search_codebase` tool to find information about AccuralAI architecture, packages, configuration, and implementation details.

### 2. Web Search

The bot includes a `search_web` tool that uses Google's grounding with Google Search to search the internet for:

- Current information
- News
- General knowledge
- Anything not in the codebase

Note: This requires the `GOOGLE_GENAI_API_KEY` environment variable to be set.

### 3. Combined Search

The `search_all` tool searches both the codebase and web simultaneously, providing comprehensive answers from multiple sources.

### 4. Example Tools

The test bot includes several example tools:

- `echo`: Echo back a message
- `calculate`: Perform simple calculations
- `sync_commands`: Sync Discord slash commands to a guild

### 5. Custom Commands

The test bot includes custom commands:

- `/test`: Test command
- `/analytics`: Show bot analytics
- `/process-attachments`: Process message attachments
- `/search`: Web search slash command
- `/sync-commands`: Sync guild commands
- `/attachment-info`: Get attachment information

### 6. Attachment Processing

The bot automatically processes attachments when multimodal support is enabled:

- Images: Analyzed and included in AI requests
- Code files: Read and analyzed
- Text files: Processed for content
- Videos: Metadata extracted

## Usage

### Mention-Only Mode

The test bot can be configured to only respond when specific users are mentioned. By default, it responds to user ID `1433628178018205768` when mentioned or when that user is the message author.

### Interacting with the Bot

1. **Direct messages**: Send messages directly to the bot
2. **Mentions**: Mention the bot in a channel (if mention-only mode is enabled)
3. **Commands**: Use `/` commands or prefix commands
4. **Attachments**: Attach files for the bot to process

### Example Interactions

**Question about AccuralAI:**
```
User: What is AccuralAI?
Bot: [Searches codebase] AccuralAI is an open-source organization...
```

**Technical question:**
```
User: How does the AccuralAI pipeline work?
Bot: [Searches codebase] The AccuralAI pipeline consists of...
```

**Web search:**
```
User: What's the latest Python version?
Bot: [Searches web] Python 3.12 was released in October 2023...
```

## Troubleshooting

### Bot Not Responding

1. Check that `DISCORD_BOT_TOKEN` is set correctly
2. Verify bot has proper permissions in the server
3. Check if mention-only filtering is enabled
4. Enable debug logging: `DISCORD_DEBUG=true`

### Codebase Search Not Working

1. Verify the bot can access the repository root
2. Check that markdown files exist in the codebase
3. Review logs for indexing errors
4. Wait for codebase index to initialize (check logs)

### Tool Calling Not Working

1. Ensure `DISCORD_ENABLE_TOOLS=true`
2. Verify backend supports function calling
3. Check tool descriptions are clear
4. Review tool execution logs

### Memory Issues

1. Reduce `DISCORD_MAX_HISTORY`
2. Enable `DISCORD_SMART_HISTORY=true`
3. Use disk cache for persistence
4. Set conversation TTL

For more help, see the main [README.md](../README.md) or [GitHub Issues](https://github.com/AccuralAI/accuralai-discord/issues).

