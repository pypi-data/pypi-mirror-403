"""Shared test fixtures for discord-llms tests."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from discord_llms.config import BotConfig, Config, DocConfig, LoggingConfig, ModelConfig
from discord_llms.logger import NullLogger

# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def sample_docs() -> list[DocConfig]:
    """Sample documentation configs for testing."""
    return [
        DocConfig(
            name="mux-docs",
            summary="Documentation for the Mux video streaming API",
            url="https://example.com/mux-docs.txt",
        ),
        DocConfig(
            name="api-reference",
            summary="API reference for REST endpoints",
            url="https://example.com/api-ref.txt",
        ),
        DocConfig(
            name="getting-started",
            summary="Quick start guide for new users",
            url="https://example.com/getting-started.txt",
        ),
    ]


@pytest.fixture
def test_config(sample_docs: list[DocConfig]) -> Config:
    """Minimal Config object for testing."""
    return Config(
        bot=BotConfig(
            name="test-bot",
            token="test-token-12345",
            channels=[123456789, 987654321],
        ),
        docs=sample_docs,
        model=ModelConfig(
            name="gpt-4o-mini",
            api_key="sk-test-key-12345",
            base_url="https://api.openai.com/v1",
        ),
    )


@pytest.fixture
def test_config_all_channels(sample_docs: list[DocConfig]) -> Config:
    """Config with empty channels list (allows all channels)."""
    return Config(
        bot=BotConfig(
            name="test-bot",
            token="test-token-12345",
            channels=[],
        ),
        docs=sample_docs,
        model=ModelConfig(
            name="gpt-4o-mini",
            api_key="sk-test-key-12345",
            base_url="https://api.openai.com/v1",
        ),
    )


@pytest.fixture
def test_config_with_logging(sample_docs: list[DocConfig], tmp_path: Path) -> Config:
    """Config with logging enabled."""
    return Config(
        bot=BotConfig(
            name="test-bot",
            token="test-token-12345",
            channels=[123456789, 987654321],
        ),
        docs=sample_docs,
        model=ModelConfig(
            name="gpt-4o-mini",
            api_key="sk-test-key-12345",
            base_url="https://api.openai.com/v1",
        ),
        logging=LoggingConfig(enabled=True, directory=tmp_path / "logs"),
    )


@pytest.fixture
def null_logger() -> NullLogger:
    """A NullLogger instance for testing."""
    return NullLogger()


# =============================================================================
# Mock Response Builders
# =============================================================================


def build_chat_response(
    content: str | None,
    finish_reason: str = "stop",
) -> Any:
    """Build a mock chat completion response with text content."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "finish_reason": finish_reason,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
    }


def build_tool_call_response(
    tool_name: str,
    arguments: dict[str, Any],
    tool_call_id: str = "call_test123",
) -> Any:
    """Build a mock chat completion response with a tool call."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(arguments),
                            },
                        }
                    ],
                },
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
        },
    }


def build_select_docs_response(doc_names: list[str]) -> Any:
    """Build a mock response for the select_docs tool call."""
    return build_tool_call_response(
        tool_name="select_docs",
        arguments={"docs": doc_names},
    )


def create_sequential_responses(
    responses: list[dict[str, Any]],
) -> Any:
    """Create a callback that returns sequential responses based on call count.

    This is used when a test needs multiple different responses from the same
    endpoint (e.g., first select_docs, then answer_question).

    Usage:
        openai_mock.chat.completions.create.response = create_sequential_responses([
            build_select_docs_response(["doc1"]),
            build_chat_response("Answer here"),
        ])
    """
    from openai_responses.ext.httpx import Request, Response
    from openai_responses.ext.respx import Route

    def callback(request: Request, route: Route) -> Response:
        # Get the response for the current call count (0-indexed)
        idx = min(route.call_count, len(responses) - 1)
        return Response(200, json=responses[idx])

    return callback


# =============================================================================
# Sample Content
# =============================================================================


SAMPLE_DOC_CONTENT = {
    "mux-docs": """# Mux Video API Documentation

## Overview
Mux provides a simple API for video streaming.

## Getting Started
To use Mux, first create an API key in your dashboard.

## Code Example
```python
import mux
client = mux.Client(api_key="your-key")
asset = client.assets.create(input="https://example.com/video.mp4")
```
""",
    "api-reference": """# API Reference

## Endpoints

### POST /assets
Create a new video asset.

### GET /assets/{id}
Retrieve asset details.

### DELETE /assets/{id}
Delete an asset.
""",
    "getting-started": """# Getting Started Guide

## Step 1: Sign Up
Create an account at mux.com

## Step 2: Get API Keys
Navigate to Settings > API Keys

## Step 3: Make Your First Request
Use curl or any HTTP client to test the API.
""",
}


@pytest.fixture
def sample_doc_content() -> dict[str, str]:
    """Sample documentation content for testing."""
    return SAMPLE_DOC_CONTENT.copy()


# =============================================================================
# Discord Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_bot_user() -> MagicMock:
    """Mock Discord bot user."""
    user = MagicMock(spec=discord.User)
    user.id = 111111111111111111
    user.name = "test-bot"
    user.bot = True
    return user


@pytest.fixture
def mock_author() -> MagicMock:
    """Mock Discord message author (regular user)."""
    user = MagicMock(spec=discord.User)
    user.id = 222222222222222222
    user.name = "test-user"
    user.bot = False
    return user


@pytest.fixture
def mock_channel() -> MagicMock:
    """Mock Discord text channel."""
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = 123456789
    channel.name = "test-channel"
    channel.send = AsyncMock()
    return channel


@pytest.fixture
def mock_thread() -> MagicMock:
    """Mock Discord thread."""
    thread = MagicMock(spec=discord.Thread)
    thread.id = 333333333333333333
    thread.name = "Q: Test question"
    thread.send = AsyncMock()
    thread.typing = MagicMock(return_value=AsyncMock())
    return thread


@pytest.fixture
def mock_message(
    mock_author: MagicMock,
    mock_channel: MagicMock,
    mock_bot_user: MagicMock,
) -> MagicMock:
    """Mock Discord message mentioning the bot."""
    message = MagicMock(spec=discord.Message)
    message.id = 444444444444444444
    message.author = mock_author
    message.channel = mock_channel
    message.content = f"<@{mock_bot_user.id}> How do I use the API?"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock()
    return message


@pytest.fixture
def mock_thinking_message() -> MagicMock:
    """Mock message used for 'thinking' status."""
    msg = MagicMock(spec=discord.Message)
    msg.edit = AsyncMock()
    msg.delete = AsyncMock()
    return msg
