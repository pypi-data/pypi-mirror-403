"""CLI entry point for discord-llms."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import discord

from discord_llms.bot import run_bot
from discord_llms.config import Config, load_config


def main() -> None:
    """Main entry point for the discord-llms CLI."""
    # Set up logging
    discord.utils.setup_logging(level=logging.INFO)
    logger: logging.Logger = logging.getLogger("discord_llms")

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="discord-llms",
        description="Discord bot that uses LLMs to help users with documentation",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        required=True,
        help="Path to the YAML configuration file",
    )

    args: argparse.Namespace = parser.parse_args()

    if not args.config.exists():
        logger.error(f"Config file not found: {args.config}")
        print("\nTo get started:", file=sys.stderr)
        print("  1. Download the example config from GitHub", file=sys.stderr)
        print("  2. Edit it with your credentials", file=sys.stderr)
        print("  3. Run: discord-llms --config path/to/config.yaml", file=sys.stderr)
        sys.exit(1)

    config: Config = load_config(args.config)
    asyncio.run(run_bot(config))
