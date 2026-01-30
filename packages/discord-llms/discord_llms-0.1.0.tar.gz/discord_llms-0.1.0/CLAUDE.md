# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Discord bot that uses LLMs to help users with project documentation. The bot uses tool calling to intelligently select relevant documentation sources (llms.txt files) and answers questions in Discord threads.

## Development Commands

### Setup and Installation

```bash
# Install dependencies (requires uv: https://docs.astral.sh/uv/)
make install
# or: uv sync --group dev --group test
```

### Code Quality

```bash
# Run all quality checks (lint, format, typecheck)
make quality

# Run individual checks
make lint       # Ruff linting
make format     # Format Python (ruff), Markdown (mdformat), YAML (yamlfmt), TOML (pyproject-fmt)
make typecheck  # Type checking with ty
```

### Testing

```bash
# Run all tests with coverage
make test
# or: uv run pytest --cov=src/discord_llms --cov-report=term-missing --cov-report=html --cov-report=xml

# Run specific test file
uv run pytest tests/test_bot.py

# Run tests marked with @pytest.mark.dev
uv run pytest -m dev

# Coverage threshold: 90% (fails below this)
```

### Running the Bot

```bash
# Run the bot (requires config.yaml with credentials)
uvx discord-llms --config config.yaml

# Or with uv run for development
uv run python -m discord_llms --config config.yaml
```

## Architecture

### Core Components

**config.py**: Configuration loading and validation using Pydantic
- `BotConfig`: Discord bot token, name, channel filtering
- `DocConfig`: Documentation sources with name, summary, and URL
- `ModelConfig`: LLM API configuration (base_url, model name, api_key, plus any extra params)
- `load_config()`: Transforms YAML structure into Pydantic models

**llm.py**: LLM client wrapper around OpenAI SDK
- Uses OpenAI SDK with configurable base_url for any OpenAI-compatible API
- Two-phase approach:
  1. **Doc selection**: Uses tool calling with `select_docs` function to pick relevant docs
  2. **Question answering**: Loads selected docs and answers with conversation history
- Jinja2 templates in `src/discord_llms/templates/` for system prompts:
  - `doc_selection.md.jinja`: Prompt for selecting relevant documentation
  - `answer_question.md.jinja`: Prompt for answering with loaded docs

**bot.py**: Discord client implementation
- Thread-based conversations: Each mention creates a new thread
- Thread context tracking: Maintains conversation history and loaded docs per thread
- Channel filtering: Optionally restrict bot to specific channels
- Message splitting: Handles Discord's 2000 char limit, with special handling for code blocks:
  - Code blocks >1800 chars sent as file attachments
  - Language identifiers normalized (lowercase, trimmed)
  - Uses discord.py's Paginator for proper code block splitting

**types.py**: Shared type definitions
- `ChatMessage`: OpenAI-style chat message format
- `ThreadContext`: Per-thread state (docs, message history)
- `MessageSegment`: Union type for text and code segments in message parsing

**cli.py**: Command-line entry point
- Argument parsing (--config required)
- Logging setup via discord.utils.setup_logging
- Config validation and bot initialization

### Conversation Flow

1. User mentions bot in a channel: `@bot How do I use tool calling?`
2. Bot creates thread with truncated question as title
3. Bot sends "thinking" message while selecting docs
4. LLM selects relevant docs via tool calling (`select_docs` function)
5. Bot fetches selected llms.txt files via HTTP
6. Bot updates thinking message with selected docs
7. LLM answers question using loaded documentation context
8. Bot sends answer (splitting if needed), then deletes thinking message
9. Follow-up messages in thread continue conversation with same docs and history

### Configuration Structure

YAML config has three main sections:
- `bot`: Discord credentials and channel filtering
- `docs`: List of documentation sources (name/summary/url mapping)
- `model`: LLM API settings (base_url, name, api_key) + optional params passed to chat completions

The `docs` section uses a nested dict structure in YAML that gets flattened to `list[DocConfig]` during loading.

### Testing Strategy

Tests use pytest with async support (pytest-asyncio). Key fixtures in `conftest.py`:
- Mock Discord messages/channels/threads
- Mock HTTP responses (pytest-httpx, respx)
- Mock OpenAI responses (openai-responses)

Test coverage required: 90% minimum (enforced in CI and local runs)

## Configuration Details

The bot requires a YAML config file with Discord bot token, LLM API credentials, and documentation sources. See `config/config.example.yaml` for the template with comprehensive comments.

Required Discord permissions: Send Messages, Create Public Threads, Send Messages in Threads, Read Message History

Required Discord intents: Message Content Intent (Privileged Gateway Intent)

## Commit Conventions

This project uses Conventional Commits (enforced via commitizen):
- `feat:` new features
- `fix:` bug fixes
- `refactor:` code changes without feature/fix
- `test:` test additions/changes
- `docs:` documentation changes
- `ci:` CI/CD changes
- `chore:` maintenance tasks

Format: `type(scope): description` (e.g., `feat(bot): add thread archiving`)
