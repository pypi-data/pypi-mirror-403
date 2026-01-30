"""Tests for DocsBot Discord handlers."""

from unittest.mock import AsyncMock, MagicMock

import discord
import openai_responses
from openai_responses import OpenAIMock

from discord_llms.bot import DocsBot
from discord_llms.config import Config
from tests.conftest import (
    build_chat_response,
    build_select_docs_response,
    create_sequential_responses,
)

# Default OpenRouter base URL used by the bot
BASE_URL = "https://api.openai.com/v1"

# =============================================================================
# Bot Initialization Tests
# =============================================================================


def test_bot_initialization(test_config: Config) -> None:
    """Test that the bot initializes correctly."""
    bot = DocsBot(test_config)

    assert bot.config == test_config
    assert bot.llm is not None
    assert bot.thread_contexts == {}


def test_bot_has_correct_intents(test_config: Config) -> None:
    """Test that the bot has required intents enabled."""
    bot = DocsBot(test_config)

    assert bot.intents.message_content is True
    assert bot.intents.guilds is True


# =============================================================================
# Message Filtering Tests
# =============================================================================


@openai_responses.mock(base_url=BASE_URL)
async def test_ignores_own_messages(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
) -> None:
    """Test that the bot ignores its own messages."""
    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user  # Set bot's user

    # Create a message from the bot itself
    message = MagicMock(spec=discord.Message)
    message.author = mock_bot_user  # Same as bot user

    await bot.on_message(message)

    # Should not make any API calls
    assert openai_mock.chat.completions.create.route.call_count == 0


@openai_responses.mock(base_url=BASE_URL)
async def test_ignores_messages_in_unallowed_channels(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
) -> None:
    """Test that the bot ignores messages in channels not in the allowed list."""
    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    # Create a message in an unallowed channel
    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 999999999  # Not in test_config.bot.channels
    message.mentions = [mock_bot_user]

    await bot.on_message(message)

    # Should not make any API calls
    assert openai_mock.chat.completions.create.route.call_count == 0


@openai_responses.mock(base_url=BASE_URL)
async def test_responds_in_allowed_channels(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test that the bot responds to mentions in allowed channels."""
    # Set up OpenAI mock responses
    openai_mock.chat.completions.create.response = create_sequential_responses(
        [
            build_select_docs_response(["mux-docs"]),
            build_chat_response("Here's how to use the API..."),
        ]
    )

    # Set up doc fetching mock via respx router
    openai_mock.router.get("https://example.com/mux-docs.txt").respond(
        text="# Mux Docs\nDocumentation content here."
    )

    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    # Create a message in an allowed channel
    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789  # In test_config.bot.channels
    message.content = f"<@{mock_bot_user.id}> How do I use the API?"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock(return_value=mock_thread)

    # Mock the thread's send to return a thinking message
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    await bot.on_message(message)

    # Should have made API calls
    assert openai_mock.chat.completions.create.route.call_count == 2
    # Thread should have been created
    message.create_thread.assert_called_once()

    await bot.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_allows_all_channels_when_list_empty(
    openai_mock: OpenAIMock,
    test_config_all_channels: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test that empty channels list allows all channels."""
    openai_mock.chat.completions.create.response = create_sequential_responses(
        [
            build_select_docs_response(["mux-docs"]),
            build_chat_response("Response content"),
        ]
    )

    openai_mock.router.get("https://example.com/mux-docs.txt").respond(
        text="# Docs content"
    )

    bot = DocsBot(test_config_all_channels)
    bot._connection.user = mock_bot_user

    # Any channel should work
    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 999999999999  # Random channel
    message.content = f"<@{mock_bot_user.id}> Question?"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock(return_value=mock_thread)
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    await bot.on_message(message)

    # Should have made API calls
    assert openai_mock.chat.completions.create.route.call_count == 2

    await bot.close()


# =============================================================================
# Mention Handling Tests
# =============================================================================


@openai_responses.mock(base_url=BASE_URL)
async def test_requires_message_content_with_mention(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
) -> None:
    """Test that bot asks for a question when mentioned without content."""
    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789
    message.content = f"<@{mock_bot_user.id}>"  # Just the mention, no question
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()

    await bot.on_message(message)

    # Should reply asking for a question
    message.reply.assert_called_once()
    reply_content = message.reply.call_args[0][0]
    assert "Please include a question" in reply_content

    # Should not make any LLM API calls
    assert openai_mock.chat.completions.create.route.call_count == 0


@openai_responses.mock(base_url=BASE_URL)
async def test_strips_mention_from_content(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test that bot removes mentions when processing the question."""
    openai_mock.chat.completions.create.response = create_sequential_responses(
        [
            build_select_docs_response(["mux-docs"]),
            build_chat_response("Answer"),
        ]
    )

    openai_mock.router.get("https://example.com/mux-docs.txt").respond(text="# Docs")

    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789
    # Include both mention formats
    message.content = f"<@{mock_bot_user.id}> <@!{mock_bot_user.id}> What is Mux?"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock(return_value=mock_thread)
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    await bot.on_message(message)

    # Thread should be created with clean question
    thread_name = message.create_thread.call_args[1]["name"]
    assert f"<@{mock_bot_user.id}>" not in thread_name
    assert "Mux" in thread_name

    await bot.close()


# =============================================================================
# Thread Handling Tests
# =============================================================================


@openai_responses.mock(base_url=BASE_URL)
async def test_thread_context_is_stored(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test that thread context is properly stored after initial response."""
    openai_mock.chat.completions.create.response = create_sequential_responses(
        [
            build_select_docs_response(["mux-docs"]),
            build_chat_response("Here's the answer."),
        ]
    )

    openai_mock.router.get("https://example.com/mux-docs.txt").respond(
        text="# Mux Docs\nContent"
    )

    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789
    message.content = f"<@{mock_bot_user.id}> How do I use Mux?"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock(return_value=mock_thread)
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    await bot.on_message(message)

    # Thread context should be stored
    assert mock_thread.id in bot.thread_contexts
    context = bot.thread_contexts[mock_thread.id]
    assert "mux-docs" in context["docs"]
    assert len(context["messages"]) == 2  # user + assistant
    assert context["messages"][0]["role"] == "user"
    assert context["messages"][1]["role"] == "assistant"

    await bot.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_thread_followup_includes_history(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
) -> None:
    """Test that follow-up messages in thread include conversation history."""
    openai_mock.chat.completions.create.response = build_chat_response(
        "Follow-up answer."
    )

    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    # Pre-populate thread context (as if initial question was already handled)
    bot.thread_contexts[mock_thread.id] = {
        "docs": {"mux-docs": "# Mux Documentation"},
        "messages": [
            {"role": "user", "content": "How do I use Mux?"},
            {"role": "assistant", "content": "First, create an API key."},
        ],
    }

    # Create a follow-up message in the thread
    followup_message = MagicMock(spec=discord.Message)
    followup_message.author = mock_author
    followup_message.channel = mock_thread
    followup_message.content = "What about video encoding?"

    # Mock the typing context manager
    mock_thread.typing = MagicMock(return_value=AsyncMock())

    await bot.on_message(followup_message)

    # Context should now have 4 messages (2 original + 1 followup + 1 answer)
    context = bot.thread_contexts[mock_thread.id]
    assert len(context["messages"]) == 4
    assert context["messages"][2]["content"] == "What about video encoding?"
    assert context["messages"][3]["content"] == "Follow-up answer."

    await bot.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_ignores_messages_in_untracked_threads(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
) -> None:
    """Test that messages in untracked threads are ignored."""
    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    # Create a message in a thread we're not tracking
    untracked_thread = MagicMock(spec=discord.Thread)
    untracked_thread.id = 555555555555555555  # Not in thread_contexts

    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = untracked_thread
    message.content = "Hello?"

    await bot.on_message(message)

    # Should not make any API calls
    assert openai_mock.chat.completions.create.route.call_count == 0


# =============================================================================
# No Docs Found Tests
# =============================================================================


@openai_responses.mock(base_url=BASE_URL)
async def test_handles_no_docs_found(
    openai_mock: OpenAIMock,
    test_config: Config,
    mock_bot_user: MagicMock,
    mock_author: MagicMock,
    mock_thread: MagicMock,
    mock_thinking_message: MagicMock,
) -> None:
    """Test behavior when no relevant docs are found."""
    # LLM returns docs that don't exist in config
    openai_mock.chat.completions.create.response = build_select_docs_response(
        ["nonexistent-doc"]
    )

    bot = DocsBot(test_config)
    bot._connection.user = mock_bot_user

    message = MagicMock(spec=discord.Message)
    message.author = mock_author
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.id = 123456789
    message.content = f"<@{mock_bot_user.id}> What about quantum physics?"
    message.mentions = [mock_bot_user]
    message.reply = AsyncMock()
    message.create_thread = AsyncMock(return_value=mock_thread)
    mock_thread.send = AsyncMock(return_value=mock_thinking_message)

    await bot.on_message(message)

    # Thinking message should be edited to show no docs found
    mock_thinking_message.edit.assert_called()
    edit_content = mock_thinking_message.edit.call_args[1]["content"]
    assert "couldn't find any relevant documentation" in edit_content

    await bot.close()


# =============================================================================
# Long Message Handling Tests
# =============================================================================


async def test_send_long_message_splits_correctly(
    test_config: Config,
    mock_channel: MagicMock,
) -> None:
    """Test that long messages are split correctly."""
    bot = DocsBot(test_config)

    # Create a message longer than Discord's 2000 char limit
    long_content = "This is a test paragraph.\n\n" * 100

    await bot._send_long_message(mock_channel, long_content)

    # Should have sent multiple messages
    assert mock_channel.send.call_count > 1

    # Each message should be under the limit
    for call in mock_channel.send.call_args_list:
        sent_content = call[0][0]
        assert len(sent_content) <= 2000


async def test_send_long_message_handles_code_blocks(
    test_config: Config,
    mock_channel: MagicMock,
) -> None:
    """Test that code blocks are handled properly."""
    bot = DocsBot(test_config)

    content = """Here's some text.

```python
def hello():
    print("Hello, World!")
```

More text here."""

    await bot._send_long_message(mock_channel, content)

    # Should have sent messages
    assert mock_channel.send.call_count >= 1


async def test_send_short_message_not_split(
    test_config: Config,
    mock_channel: MagicMock,
) -> None:
    """Test that short messages are not split."""
    bot = DocsBot(test_config)

    short_content = "This is a short message."

    await bot._send_long_message(mock_channel, short_content)

    # Should send exactly one message
    assert mock_channel.send.call_count == 1
    mock_channel.send.assert_called_once_with(short_content, suppress_embeds=True)


async def test_send_long_message_large_code_as_file(
    test_config: Config,
    mock_channel: MagicMock,
) -> None:
    """Test that large code blocks (>1800 chars) are sent as file attachments."""
    bot = DocsBot(test_config)

    # Generate code block > 1800 chars (threshold in bot.py)
    large_code = "x = 1\n" * 400  # ~2400 chars
    content = f"```python\n{large_code}\n```"

    await bot._send_long_message(mock_channel, content)

    # Should have sent a file attachment
    assert mock_channel.send.call_count >= 1

    # Find the call with the file attachment
    file_call = None
    for call in mock_channel.send.call_args_list:
        if call.kwargs.get("file"):
            file_call = call
            break

    assert file_call is not None, "Expected a file attachment to be sent"
    assert "Code block too large" in file_call.args[0]
    assert file_call.kwargs["file"].filename == "code.py"


async def test_send_long_message_special_char_languages(
    test_config: Config,
    mock_channel: MagicMock,
) -> None:
    """Test that languages with special characters are handled properly."""
    bot = DocsBot(test_config)

    content = """Here's some C++ code:

```c++
class MyClass {
public:
    void method() {}
};
```

And some C# code:

```c#
public class MyClass {
    public void Method() {}
}
```

And F# code:

```f#
let factorial n =
    if n <= 1 then 1
    else n * factorial (n - 1)
```

And TypeScript React:

```typescript-react
const Component: React.FC = () => {
    return <div>Hello</div>;
}
```"""

    await bot._send_long_message(mock_channel, content)

    # Should have sent at least 4 messages (one for each code block)
    # Could be more if there are text segments between blocks
    assert mock_channel.send.call_count >= 4

    # Verify code blocks were preserved with proper formatting
    calls = mock_channel.send.call_args_list
    code_blocks = [call[0][0] for call in calls if call[0][0].startswith("```")]

    # Check that language identifiers are preserved
    assert any("c++" in block for block in code_blocks)
    assert any("c#" in block for block in code_blocks)
    assert any("f#" in block for block in code_blocks)
    assert any("typescript-react" in block for block in code_blocks)
