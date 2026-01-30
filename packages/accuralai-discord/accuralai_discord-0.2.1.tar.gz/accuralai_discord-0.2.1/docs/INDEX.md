# AccuralAI Discord Bot Documentation Index

Welcome to the AccuralAI Discord Bot documentation!

## Documentation Structure

This documentation is automatically indexed by the bot's codebase search when you run the test bot. The bot can search through all markdown files in this directory to answer questions about AccuralAI Discord bot features, setup, API, and usage.

### Main Documentation Files

1. **[README.md](README.md)** - Complete overview and quick start guide
   - Installation
   - Basic configuration
   - Features overview
   - Examples

2. **[SETUP.md](SETUP.md)** - Step-by-step setup guide
   - Prerequisites
   - Installation instructions
   - Bot creation
   - Configuration
   - Troubleshooting

3. **[FEATURES.md](FEATURES.md)** - Detailed feature documentation
   - Core features
   - Advanced features
   - Test bot features
   - Configuration features

4. **[API.md](API.md)** - Complete API reference
   - DiscordBot class
   - DiscordBotConfig class
   - CommandContext
   - BotAnalytics
   - Methods and properties

5. **[TEST_BOT.md](TEST_BOT.md)** - Test bot documentation
   - Overview
   - Configuration
   - Features
   - Usage examples
   - Troubleshooting

## Quick Links

- **Getting Started**: Start with [SETUP.md](SETUP.md) for installation
- **First Bot**: Use [README.md](README.md) for a minimal example
- **Advanced Features**: See [FEATURES.md](FEATURES.md) for detailed features
- **API Reference**: Check [API.md](API.md) for method signatures
- **Test Bot**: Read [TEST_BOT.md](TEST_BOT.md) for the full-featured example

## Using with Codebase Search

When you run the test bot, it automatically indexes all markdown files in this directory. You can ask the bot questions like:

- "How do I set up the bot?"
- "What features does the bot support?"
- "How do I add a custom tool?"
- "What configuration options are available?"
- "How does the codebase search work?"

The bot will search through these documentation files to provide accurate answers.

## Contributing

If you want to improve the documentation:

1. Edit the relevant markdown file
2. The bot will automatically re-index on restart
3. Test by asking the bot about the topic

## Installation Note

When users install the package (via `pip install accuralai-discord` or cloning the repo), these documentation files are included in the package. The bot's codebase search automatically finds and indexes all markdown files in `packages/*/docs/` directories when running.

For source installations, the bot indexes from the repository root, so all docs are automatically available.

