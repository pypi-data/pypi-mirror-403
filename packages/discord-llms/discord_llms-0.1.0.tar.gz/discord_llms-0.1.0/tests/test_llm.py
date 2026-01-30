"""Tests for LLMClient."""

import httpx
import openai
import openai_responses
import pytest
from openai_responses import OpenAIMock

from discord_llms.config import Config
from discord_llms.llm import LLMClient
from tests.conftest import (
    build_chat_response,
    build_select_docs_response,
    build_tool_call_response,
)

# Default OpenRouter base URL used by the bot
BASE_URL = "https://api.openai.com/v1"

# =============================================================================
# select_docs() Tests
# =============================================================================


@openai_responses.mock(base_url=BASE_URL)
async def test_select_docs_returns_matching_slugs(
    openai_mock: OpenAIMock,
    test_config: Config,
) -> None:
    """Test that select_docs returns doc names from the tool call."""
    openai_mock.chat.completions.create.response = build_select_docs_response(
        ["mux-docs", "api-reference"]
    )

    client = LLMClient(test_config)
    try:
        result = await client.select_docs("How do I use the video API?")

        assert result.selected_docs == ["mux-docs", "api-reference"]
        assert result.token_usage is not None
        assert result.token_usage["total_tokens"] == 120
        assert openai_mock.chat.completions.create.route.call_count == 1
    finally:
        await client.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_select_docs_empty_selection(
    openai_mock: OpenAIMock,
    test_config: Config,
) -> None:
    """Test that select_docs returns empty list when no docs selected."""
    openai_mock.chat.completions.create.response = build_select_docs_response([])

    client = LLMClient(test_config)
    try:
        result = await client.select_docs("Something completely unrelated")

        assert result.selected_docs == []
    finally:
        await client.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_select_docs_single_doc(
    openai_mock: OpenAIMock,
    test_config: Config,
) -> None:
    """Test selecting a single doc."""
    openai_mock.chat.completions.create.response = build_select_docs_response(
        ["getting-started"]
    )

    client = LLMClient(test_config)
    try:
        result = await client.select_docs("How do I get started?")

        assert result.selected_docs == ["getting-started"]
    finally:
        await client.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_select_docs_fallback_when_no_tool_call(
    openai_mock: OpenAIMock,
    test_config: Config,
) -> None:
    """Test fallback to all docs when LLM doesn't use the tool."""
    # Return a regular text response instead of a tool call
    openai_mock.chat.completions.create.response = build_chat_response(
        "I think you should check all the documentation."
    )

    client = LLMClient(test_config)
    try:
        result = await client.select_docs("Tell me everything")

        # Should return all doc names as fallback
        expected = [doc.name for doc in test_config.docs]
        assert result.selected_docs == expected
    finally:
        await client.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_select_docs_handles_wrong_tool_name(
    openai_mock: OpenAIMock,
    test_config: Config,
) -> None:
    """Test fallback when LLM calls a different tool name."""
    openai_mock.chat.completions.create.response = build_tool_call_response(
        tool_name="wrong_tool",
        arguments={"docs": ["mux-docs"]},
    )

    client = LLMClient(test_config)
    try:
        result = await client.select_docs("How do I use the API?")

        # Should return all docs as fallback
        expected = [doc.name for doc in test_config.docs]
        assert result.selected_docs == expected
    finally:
        await client.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_select_docs_api_error(
    openai_mock: OpenAIMock,
    test_config: Config,
) -> None:
    """Test that API errors propagate correctly."""
    openai_mock.chat.completions.create.response = httpx.Response(
        status_code=500,
        json={"error": {"message": "Internal server error"}},
    )

    client = LLMClient(test_config)
    try:
        with pytest.raises(openai.InternalServerError):
            await client.select_docs("How do I use the API?")
    finally:
        await client.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_select_docs_rate_limit_error(
    openai_mock: OpenAIMock,
    test_config: Config,
) -> None:
    """Test handling of rate limit errors."""
    openai_mock.chat.completions.create.response = httpx.Response(
        status_code=429,
        json={"error": {"message": "Rate limit exceeded"}},
    )

    client = LLMClient(test_config)
    try:
        with pytest.raises(openai.RateLimitError):
            await client.select_docs("How do I use the API?")
    finally:
        await client.close()


# =============================================================================
# answer_question() Tests
# =============================================================================


@openai_responses.mock(base_url=BASE_URL)
async def test_answer_question_with_context(
    openai_mock: OpenAIMock,
    test_config: Config,
    sample_doc_content: dict[str, str],
) -> None:
    """Test answering a question with documentation context."""
    expected_answer = "To use the API, first create an API key in your dashboard."
    openai_mock.chat.completions.create.response = build_chat_response(expected_answer)

    client = LLMClient(test_config)
    try:
        result = await client.answer_question(
            messages=[{"role": "user", "content": "How do I use the API?"}],
            docs_content={"mux-docs": sample_doc_content["mux-docs"]},
        )

        assert result.content == expected_answer
        assert result.token_usage is not None
        assert result.token_usage["total_tokens"] == 150
        assert openai_mock.chat.completions.create.route.call_count == 1
    finally:
        await client.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_answer_question_empty_context(
    openai_mock: OpenAIMock,
    test_config: Config,
) -> None:
    """Test answering when no documentation context provided."""
    expected_answer = "I don't have any documentation to reference for this question."
    openai_mock.chat.completions.create.response = build_chat_response(expected_answer)

    client = LLMClient(test_config)
    try:
        result = await client.answer_question(
            messages=[{"role": "user", "content": "What is the meaning of life?"}],
            docs_content={},
        )

        assert result.content == expected_answer
    finally:
        await client.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_answer_question_with_conversation_history(
    openai_mock: OpenAIMock,
    test_config: Config,
    sample_doc_content: dict[str, str],
) -> None:
    """Test answering with multi-turn conversation history."""
    expected_answer = "The create method accepts an input URL parameter."
    openai_mock.chat.completions.create.response = build_chat_response(expected_answer)

    client = LLMClient(test_config)
    try:
        result = await client.answer_question(
            messages=[
                {"role": "user", "content": "How do I create an asset?"},
                {"role": "assistant", "content": "Use client.assets.create()"},
                {"role": "user", "content": "What parameters does it accept?"},
            ],
            docs_content={"mux-docs": sample_doc_content["mux-docs"]},
        )

        assert result.content == expected_answer
    finally:
        await client.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_answer_question_handles_empty_content(
    openai_mock: OpenAIMock,
    test_config: Config,
) -> None:
    """Test handling when LLM returns empty content."""
    # Response with null/None content
    openai_mock.chat.completions.create.response = build_chat_response(None)

    client = LLMClient(test_config)
    try:
        result = await client.answer_question(
            messages=[{"role": "user", "content": "Hello"}],
            docs_content={},
        )

        # Should return empty string, not None
        assert result.content == ""
    finally:
        await client.close()


@openai_responses.mock(base_url=BASE_URL)
async def test_answer_question_api_error(
    openai_mock: OpenAIMock,
    test_config: Config,
) -> None:
    """Test that API errors propagate correctly in answer_question."""
    openai_mock.chat.completions.create.response = httpx.Response(
        status_code=500,
        json={"error": {"message": "Internal server error"}},
    )

    client = LLMClient(test_config)
    try:
        with pytest.raises(openai.InternalServerError):
            await client.answer_question(
                messages=[{"role": "user", "content": "Hello"}],
                docs_content={},
            )
    finally:
        await client.close()


# =============================================================================
# get_doc_by_name() Tests
# =============================================================================


def test_get_doc_by_name_exact_match(test_config: Config) -> None:
    """Test finding a doc by exact name."""
    client = LLMClient(test_config)

    doc = client.get_doc_by_name("mux-docs")

    assert doc is not None
    assert doc.name == "mux-docs"


def test_get_doc_by_name_case_insensitive(test_config: Config) -> None:
    """Test that doc lookup is case-insensitive."""
    client = LLMClient(test_config)

    doc = client.get_doc_by_name("MUX-DOCS")

    assert doc is not None
    assert doc.name == "mux-docs"


def test_get_doc_by_name_not_found(test_config: Config) -> None:
    """Test that non-existent doc returns None."""
    client = LLMClient(test_config)

    doc = client.get_doc_by_name("nonexistent-doc")

    assert doc is None


# =============================================================================
# fetch_doc_content() Tests
# =============================================================================


async def test_fetch_doc_content_success(
    test_config: Config,
    httpx_mock,
) -> None:
    """Test successful document fetching."""
    expected_content = "# Documentation\nThis is the doc content."
    httpx_mock.add_response(
        url="https://example.com/mux-docs.txt",
        text=expected_content,
    )

    client = LLMClient(test_config)
    try:
        doc = client.get_doc_by_name("mux-docs")
        assert doc is not None

        content = await client.fetch_doc_content(doc)

        assert content == expected_content
    finally:
        await client.close()


async def test_fetch_doc_content_404(
    test_config: Config,
    httpx_mock,
) -> None:
    """Test handling of 404 errors when fetching docs."""
    httpx_mock.add_response(
        url="https://example.com/mux-docs.txt",
        status_code=404,
    )

    client = LLMClient(test_config)
    try:
        doc = client.get_doc_by_name("mux-docs")
        assert doc is not None

        content = await client.fetch_doc_content(doc)

        # Should return an error message, not raise
        assert "Error fetching documentation" in content
    finally:
        await client.close()


async def test_fetch_doc_content_timeout(
    test_config: Config,
    httpx_mock,
) -> None:
    """Test handling of timeout errors."""

    def raise_timeout(request):
        raise httpx.TimeoutException("Connection timed out")

    httpx_mock.add_callback(raise_timeout, url="https://example.com/mux-docs.txt")

    client = LLMClient(test_config)
    try:
        doc = client.get_doc_by_name("mux-docs")
        assert doc is not None

        content = await client.fetch_doc_content(doc)

        assert "Error fetching documentation" in content
    finally:
        await client.close()


async def test_fetch_doc_content_server_error(
    test_config: Config,
    httpx_mock,
) -> None:
    """Test handling of server errors (5xx)."""
    httpx_mock.add_response(
        url="https://example.com/mux-docs.txt",
        status_code=500,
    )

    client = LLMClient(test_config)
    try:
        doc = client.get_doc_by_name("mux-docs")
        assert doc is not None

        content = await client.fetch_doc_content(doc)

        assert "Error fetching documentation" in content
    finally:
        await client.close()
