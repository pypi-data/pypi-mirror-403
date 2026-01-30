"""End-to-end integration tests for the Discord bot flow."""

from unittest.mock import AsyncMock, MagicMock

import discord
import openai_responses
from openai_responses import OpenAIMock

from discord_llms.bot import DocsBot
from discord_llms.config import Config
from tests.conftest import (
    SAMPLE_DOC_CONTENT,
    build_chat_response,
    build_select_docs_response,
    create_sequential_responses,
)

# OpenAI base URL for mocking
BASE_URL = "https://api.openai.com/v1"

# =============================================================================
# Full Question-Answer Flow Tests
# =============================================================================


@openai_responses.mock(base_url=BASE_URL)
async def test_full_question_answer_flow(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test complete flow: message → select_docs → fetch → answer → response.

    This tests the entire happy path from a user mentioning the bot
    through to receiving an answer.
    """
    # Phase 1: LLM selects relevant docs
    # Phase 2: LLM generates answer with doc context
    openai_mock.chat.completions.create.response = create_sequential_responses(
        [
            build_select_docs_response(["mux-docs", "api-reference"]),
            build_chat_response(
                "To create a video asset, use the POST /assets endpoint. "
                "Here's an example:\n\n"
                "```python\n"
                "import mux\n"
                "client = mux.Client(api_key='your-key')\n"
                "asset = client.assets.create(input='https://example.com/video.mp4')\n"
                "```"
            ),
        ]
    )

    # Mock doc content fetching via respx router
    openai_mock.router.get("https://example.com/mux-docs.txt").respond(
        text=SAMPLE_DOC_CONTENT["mux-docs"]
    )
    openai_mock.router.get("https://example.com/api-ref.txt").respond(
        text=SAMPLE_DOC_CONTENT["api-reference"]
    )

    # Set up bot
    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    # Create the initial message
    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789  # Allowed channel
    message.content = f"<@{mock_bot_user.id}> How do I create a video asset?"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock(return_value=mock_thread)
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    # Execute the flow
    await bot.on_message(message)

    # Verify the flow executed correctly
    # 1. Thread was created
    message.create_thread.assert_called_once()
    assert "video asset" in message.create_thread.call_args[1]["name"].lower()

    # 2. Thinking message was sent and later deleted
    assert mock_thread.send.call_count >= 1  # Thinking + response
    mock_thinking_message.delete.assert_called_once()

    # 3. Both LLM calls were made (select_docs + answer_question)
    assert openai_mock.chat.completions.create.route.call_count == 2

    # 4. Thread context was stored with correct data
    assert mock_thread.id in bot.thread_contexts
    context = bot.thread_contexts[mock_thread.id]
    assert "mux-docs" in context["docs"]
    assert "api-reference" in context["docs"]
    assert len(context["messages"]) == 2

    await bot.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_flow_with_no_relevant_docs(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test flow when LLM determines no docs are relevant."""
    # LLM returns empty doc selection
    openai_mock.chat.completions.create.response = build_select_docs_response([])

    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789
    message.content = f"<@{mock_bot_user.id}> What's the weather like?"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock(return_value=mock_thread)
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    await bot.on_message(message)

    # Should show "no docs found" message
    mock_thinking_message.edit.assert_called()
    edit_content = mock_thinking_message.edit.call_args[1]["content"]
    assert "couldn't find" in edit_content.lower()

    # Only one LLM call (select_docs), no answer_question call
    assert openai_mock.chat.completions.create.route.call_count == 1

    await bot.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_flow_with_single_doc_selection(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test flow when only one doc is selected."""
    openai_mock.chat.completions.create.response = create_sequential_responses(
        [
            build_select_docs_response(["getting-started"]),
            build_chat_response(
                "To get started, sign up at mux.com and get your API keys."
            ),
        ]
    )

    openai_mock.router.get("https://example.com/getting-started.txt").respond(
        text=SAMPLE_DOC_CONTENT["getting-started"]
    )

    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789
    message.content = f"<@{mock_bot_user.id}> How do I get started?"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock(return_value=mock_thread)
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    await bot.on_message(message)

    # Verify only one doc was fetched
    context = bot.thread_contexts[mock_thread.id]
    assert len(context["docs"]) == 1
    assert "getting-started" in context["docs"]

    await bot.close()


# =============================================================================
# Thread Conversation Flow Tests
# =============================================================================


@openai_responses.mock(base_url=BASE_URL)
async def test_thread_conversation_flow(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test multi-turn conversation in a thread.

    Flow:
    1. User asks initial question → thread created
    2. User asks follow-up → bot responds with context
    3. User asks another follow-up → bot maintains full history
    """
    # Set up responses for initial + 2 follow-ups
    openai_mock.chat.completions.create.response = create_sequential_responses(
        [
            # Initial question
            build_select_docs_response(["mux-docs"]),
            build_chat_response("Use client.assets.create() to upload videos."),
            # First follow-up
            build_chat_response(
                "The input parameter accepts a URL to your video file."
            ),
            # Second follow-up
            build_chat_response(
                "Yes, you can also pass playback_policy for access control."
            ),
        ]
    )

    openai_mock.router.get("https://example.com/mux-docs.txt").respond(
        text=SAMPLE_DOC_CONTENT["mux-docs"]
    )

    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    # === Initial Question ===
    initial_message = MagicMock(spec=discord.Message)
    initial_message.author = mock_author
    initial_message.channel = MagicMock(spec=discord.TextChannel)
    initial_message.channel.id = 123456789
    initial_message.content = f"<@{mock_bot_user.id}> How do I upload a video?"
    initial_message.mentions = [mock_bot_user]
    initial_message.reply = AsyncMock()
    initial_message.create_thread = AsyncMock(return_value=mock_thread)
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    await bot.on_message(initial_message)

    # Verify initial state
    assert mock_thread.id in bot.thread_contexts
    assert len(bot.thread_contexts[mock_thread.id]["messages"]) == 2

    # === First Follow-up ===
    mock_thread.typing = MagicMock(return_value=AsyncMock())

    followup1 = MagicMock(spec=discord.Message)
    followup1.author = mock_author
    followup1.channel = mock_thread
    followup1.content = "What parameters does it accept?"

    await bot.on_message(followup1)

    # Should have 4 messages now
    assert len(bot.thread_contexts[mock_thread.id]["messages"]) == 4

    # === Second Follow-up ===
    followup2 = MagicMock(spec=discord.Message)
    followup2.author = mock_author
    followup2.channel = mock_thread
    followup2.content = "Can I set playback permissions?"

    await bot.on_message(followup2)

    # Should have 6 messages now
    context = bot.thread_contexts[mock_thread.id]
    assert len(context["messages"]) == 6

    # Verify message history is correct
    assert context["messages"][0]["role"] == "user"
    assert "upload" in context["messages"][0]["content"].lower()
    assert context["messages"][1]["role"] == "assistant"
    assert context["messages"][2]["role"] == "user"
    assert "parameters" in context["messages"][2]["content"].lower()
    assert context["messages"][3]["role"] == "assistant"
    assert context["messages"][4]["role"] == "user"
    assert "playback" in context["messages"][4]["content"].lower()
    assert context["messages"][5]["role"] == "assistant"

    # Total LLM calls: 2 (initial) + 1 (followup1) + 1 (followup2) = 4
    assert openai_mock.chat.completions.create.route.call_count == 4

    await bot.close()


# =============================================================================
# Error Handling Integration Tests
# =============================================================================


@openai_responses.mock(base_url=BASE_URL)
async def test_flow_handles_doc_fetch_failure(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test flow when doc fetching fails but bot continues."""
    openai_mock.chat.completions.create.response = create_sequential_responses(
        [
            build_select_docs_response(["mux-docs", "api-reference"]),
            build_chat_response("Based on the available documentation..."),
        ]
    )

    # First doc succeeds, second fails
    openai_mock.router.get("https://example.com/mux-docs.txt").respond(
        text=SAMPLE_DOC_CONTENT["mux-docs"]
    )
    openai_mock.router.get("https://example.com/api-ref.txt").respond(status_code=500)

    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789
    message.content = f"<@{mock_bot_user.id}> Tell me about the API"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock(return_value=mock_thread)
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    await bot.on_message(message)

    # Bot should still respond, using the one doc that succeeded
    context = bot.thread_contexts[mock_thread.id]
    assert "mux-docs" in context["docs"]
    # api-reference will have an error message as content
    assert "api-reference" in context["docs"]
    assert "Error" in context["docs"]["api-reference"]

    await bot.close()


# =============================================================================
# Edge Case Integration Tests
# =============================================================================


@openai_responses.mock(base_url=BASE_URL)
async def test_flow_with_all_docs_selected(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test flow when LLM selects all available docs."""
    all_doc_names = [doc.name for doc in test_config.docs]

    openai_mock.chat.completions.create.response = create_sequential_responses(
        [
            build_select_docs_response(all_doc_names),
            build_chat_response("Here's a comprehensive overview..."),
        ]
    )

    # Mock all doc URLs
    openai_mock.router.get("https://example.com/mux-docs.txt").respond(
        text=SAMPLE_DOC_CONTENT["mux-docs"]
    )
    openai_mock.router.get("https://example.com/api-ref.txt").respond(
        text=SAMPLE_DOC_CONTENT["api-reference"]
    )
    openai_mock.router.get("https://example.com/getting-started.txt").respond(
        text=SAMPLE_DOC_CONTENT["getting-started"]
    )

    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789
    message.content = f"<@{mock_bot_user.id}> Give me a full overview"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock(return_value=mock_thread)
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    await bot.on_message(message)

    # All docs should be in context
    context = bot.thread_contexts[mock_thread.id]
    assert len(context["docs"]) == 3
    for doc_name in all_doc_names:
        assert doc_name in context["docs"]

    await bot.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_flow_with_long_response(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test flow when LLM returns a response exceeding Discord's limit."""
    # Generate a response > 2000 chars
    long_response = "Here's a detailed explanation:\n\n" + ("This is important. " * 200)

    openai_mock.chat.completions.create.response = create_sequential_responses(
        [
            build_select_docs_response(["mux-docs"]),
            build_chat_response(long_response),
        ]
    )

    openai_mock.router.get("https://example.com/mux-docs.txt").respond(
        text=SAMPLE_DOC_CONTENT["mux-docs"]
    )

    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789
    message.content = f"<@{mock_bot_user.id}> Explain everything in detail"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock(return_value=mock_thread)
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    await bot.on_message(message)

    # Multiple messages should have been sent to the thread
    # (thinking message + response chunks)
    assert mock_thread.send.call_count > 1

    await bot.close()
