"""Shared type definitions for discord-llms."""

from typing import Literal, TypedDict


class ChatMessage(TypedDict):
    """A chat message in the conversation."""

    role: Literal["system", "user", "assistant"]
    content: str


class ThreadContext(TypedDict):
    """Context for an active conversation thread."""

    docs: dict[str, str]
    messages: list[ChatMessage]


type TextSegment = tuple[Literal["text"], str]
type CodeSegment = tuple[Literal["code"], str, str]
type MessageSegment = TextSegment | CodeSegment


class TokenUsage(TypedDict):
    """Token usage statistics from an LLM API call."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LogEntry(TypedDict, total=False):
    """A conversation log entry for JSONL logging."""

    timestamp: str
    event_type: Literal["doc_selection", "answer"]
    thread_id: int
    user_id: int
    username: str
    guild_id: int | None
    channel_id: int
    question: str
    model: str
    request_messages: list[ChatMessage]
    response: str
    selected_docs: list[str]
    docs_loaded: list[str]
    token_usage: TokenUsage
    latency_ms: int
    error: str | None
