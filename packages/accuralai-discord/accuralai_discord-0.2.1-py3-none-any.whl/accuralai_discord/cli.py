"""CLI runner for Discord bot."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .bot import DiscordBot
from .config import DiscordBotConfig


def main() -> None:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run AccuralAI Discord bot")
    parser.add_argument(
        "--token",
        help="Discord bot token (or set DISCORD_BOT_TOKEN env var)",
        default=os.getenv("DISCORD_BOT_TOKEN"),
    )
    parser.add_argument(
        "--config",
        help="Path to bot configuration TOML file",
        type=Path,
    )
    parser.add_argument(
        "--personality",
        help="Bot personality description",
    )
    parser.add_argument(
        "--scope",
        choices=["per-channel", "per-user", "per-thread", "per-channel-user"],
        help="Conversation scope",
    )
    parser.add_argument(
        "--accuralai-config",
        help="Path to AccuralAI configuration TOML file",
        type=Path,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if not args.token:
        print("Error: Discord bot token is required (--token or DISCORD_BOT_TOKEN)")
        sys.exit(1)

    # Build config
    config_kwargs: dict = {"token": args.token}
    if args.personality:
        config_kwargs["personality"] = args.personality
    if args.scope:
        config_kwargs["conversation_scope"] = args.scope
    if args.accuralai_config:
        config_kwargs["accuralai_config_path"] = str(args.accuralai_config)
    if args.debug:
        config_kwargs["debug"] = True

    # Load from TOML if provided
    if args.config:
        try:
            import tomli
        except ImportError:
            try:
                import tomllib as tomli  # Python 3.11+
            except ImportError:
                print("Error: tomli package required for TOML config files")
                print("Install with: pip install tomli")
                sys.exit(1)

        with open(args.config, "rb") as f:
            toml_data = tomli.load(f)
        discord_config = toml_data.get("discord", {})
        config_kwargs.update(discord_config)

    bot = DiscordBot(config=DiscordBotConfig(**config_kwargs))
    bot.run()


if __name__ == "__main__":
    main()

