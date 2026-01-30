# Setup Guide

Complete setup guide for the AccuralAI Discord bot.

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.10 or higher** installed
2. **Discord Bot Token** - Create a bot at https://discord.com/developers/applications
3. **AccuralAI Config** (optional) - Configuration file for AccuralAI orchestration

## Installation

### Option 1: Install from PyPI

```bash
pip install accuralai-discord
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/AccuralAI/AccuralAI.git
cd AccuralAI/packages/accuralai-discord

# Install in development mode
pip install -e .
```

## Creating a Discord Bot

1. Go to https://discord.com/developers/applications
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot" and confirm
5. Under "Token", click "Reset Token" to get your bot token
6. Copy the token (you'll need it for `DISCORD_BOT_TOKEN`)

### Bot Permissions

Enable the following permissions in the "Bot Permissions" section:

- **Send Messages**
- **Read Message History**
- **Use Slash Commands**
- **Attach Files** (if using multimodal features)
- **Embed Links** (if using embeds)
- **Read Messages/View Channels**

The minimum permissions integer is: `534723950656`

## Configuration

### Environment Variables

Set the following environment variables:

**Linux/Mac:**
```bash
export DISCORD_BOT_TOKEN="your_bot_token_here"
export ACCURALAI_CONFIG_PATH="path/to/config.toml"  # Optional
```

**Windows CMD:**
```cmd
set DISCORD_BOT_TOKEN=your_bot_token_here
set ACCURALAI_CONFIG_PATH=C:\path\to\config.toml
```

**Windows PowerShell:**
```powershell
$env:DISCORD_BOT_TOKEN="your_bot_token_here"
$env:ACCURALAI_CONFIG_PATH="C:\path\to\config.toml"
```

### AccuralAI Configuration

The bot needs an AccuralAI config file to connect to LLM backends. Create a `config.toml` file:

```toml
[backends.ollama]
plugin_id = "accuralai-ollama"
options = { model = "llama3" }

[backends.google]
plugin_id = "accuralai-google"
options = { model = "gemini-pro" }
```

For more details, see the [AccuralAI Core Configuration Example](../../../plan/accuralai-core-config-example.toml).

## Running the Bot

### Test Bot (Recommended for First Time)

The easiest way to get started is using the test bot:

```bash
python -m accuralai_discord.test_bot
```

Or use the CLI command:

```bash
accuralai-discord-test
```

### Custom Bot

Create a Python script:

```python
from accuralai_discord import DiscordBot

bot = DiscordBot(
    token="DISCORD_BOT_TOKEN",
    personality="helpful assistant",
    accuralai_config_path="config.toml"
)
bot.run()
```

## Inviting the Bot to Your Server

1. Go to the OAuth2 > URL Generator section in your Discord application
2. Select scopes:
   - `bot`
   - `applications.commands` (for slash commands)
3. Select bot permissions (see above)
4. Copy the generated URL
5. Open the URL in your browser and select your server

## Verifying Installation

Once the bot is running:

1. Check the console for startup messages
2. Try mentioning the bot in Discord
3. Use `/help` command to see available commands
4. Check `/status` for bot status

## Troubleshooting

### Bot Doesn't Respond

1. **Check token**: Verify `DISCORD_BOT_TOKEN` is set correctly
2. **Check permissions**: Ensure bot has necessary permissions
3. **Check mention filtering**: If mention-only mode is enabled, ensure you're mentioning the bot correctly
4. **Check logs**: Enable debug mode with `DISCORD_DEBUG=true`

### Import Errors

If you get import errors:

```bash
# Reinstall the package
pip install -e .

# Or upgrade dependencies
pip install --upgrade accuralai-discord discord.py
```

### Config Errors

If the bot can't load the AccuralAI config:

1. Check the path is correct
2. Verify the config file is valid TOML
3. Ensure backend plugins are installed:
   ```bash
   pip install accuralai-ollama  # or accuralai-google
   ```

### Codebase Search Not Working

The bot automatically indexes the codebase when it starts. If search isn't working:

1. Check logs for indexing errors
2. Verify the repository root is accessible
3. Wait for indexing to complete (check logs)
4. Enable debug mode: `DISCORD_DEBUG=true`

## Next Steps

- Read the [README.md](../README.md) for features
- Check [FEATURES.md](FEATURES.md) for detailed feature documentation
- See [API.md](API.md) for API reference
- Review [TEST_BOT.md](TEST_BOT.md) for test bot documentation

## Getting Help

- **GitHub Issues**: https://github.com/AccuralAI/accuralai-discord/issues
- **Documentation**: https://accuralai.readthedocs.io/
- **Discord**: [Join our Discord server](https://discord.gg/accuralai) (if available)

