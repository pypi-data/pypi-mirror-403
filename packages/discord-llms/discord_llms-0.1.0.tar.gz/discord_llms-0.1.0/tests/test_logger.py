"""Tests for conversation logging."""

import json
from pathlib import Path
from unittest.mock import patch

from discord_llms.logger import (
    ConversationLogger,
    JSONLConversationLogger,
    NullLogger,
)
from discord_llms.types import LogEntry

# =============================================================================
# NullLogger Tests
# =============================================================================


def test_null_logger_is_conversation_logger() -> None:
    """Test that NullLogger implements ConversationLogger."""
    logger = NullLogger()
    assert isinstance(logger, ConversationLogger)


def test_null_logger_log_does_nothing() -> None:
    """Test that NullLogger.log() completes without error."""
    logger = NullLogger()
    entry: LogEntry = {
        "timestamp": "2026-01-24T10:30:00+00:00",
        "event_type": "doc_selection",
        "thread_id": 123,
        "user_id": 456,
        "username": "test-user",
        "question": "How do I use the API?",
        "model": "gpt-4o-mini",
    }
    # Should not raise
    logger.log(entry)


def test_null_logger_close_does_nothing() -> None:
    """Test that NullLogger.close() completes without error."""
    logger = NullLogger()
    # Should not raise
    logger.close()


# =============================================================================
# JSONLConversationLogger Tests
# =============================================================================


def test_jsonl_logger_is_conversation_logger() -> None:
    """Test that JSONLConversationLogger implements ConversationLogger."""
    logger = JSONLConversationLogger(Path("/tmp/test-logs"))
    assert isinstance(logger, ConversationLogger)
    logger.close()


def test_jsonl_logger_creates_directory(tmp_path: Path) -> None:
    """Test that logger creates the log directory if it doesn't exist."""
    log_dir = tmp_path / "nested" / "logs"
    assert not log_dir.exists()

    logger = JSONLConversationLogger(log_dir)
    entry: LogEntry = {
        "timestamp": "2026-01-24T10:30:00+00:00",
        "event_type": "doc_selection",
        "thread_id": 123,
        "user_id": 456,
        "username": "test-user",
        "question": "Test question",
        "model": "gpt-4o-mini",
    }
    logger.log(entry)
    logger.close()

    assert log_dir.exists()


def test_jsonl_logger_writes_valid_jsonl(tmp_path: Path) -> None:
    """Test that logger writes valid JSONL format."""
    logger = JSONLConversationLogger(tmp_path)
    entry: LogEntry = {
        "timestamp": "2026-01-24T10:30:00+00:00",
        "event_type": "doc_selection",
        "thread_id": 123,
        "user_id": 456,
        "username": "test-user",
        "question": "How do I use the API?",
        "model": "gpt-4o-mini",
        "selected_docs": ["openai", "langchain"],
        "token_usage": {
            "prompt_tokens": 150,
            "completion_tokens": 50,
            "total_tokens": 200,
        },
        "latency_ms": 1250,
    }
    logger.log(entry)
    logger.close()

    # Find the log file
    log_files = list(tmp_path.glob("*.jsonl"))
    assert len(log_files) == 1

    # Read and parse the JSONL
    content = log_files[0].read_text()
    lines = content.strip().split("\n")
    assert len(lines) == 1

    parsed = json.loads(lines[0])
    assert parsed["event_type"] == "doc_selection"
    assert parsed["thread_id"] == 123
    assert parsed["selected_docs"] == ["openai", "langchain"]
    assert parsed["token_usage"]["total_tokens"] == 200


def test_jsonl_logger_appends_entries(tmp_path: Path) -> None:
    """Test that multiple log entries are appended to the same file."""
    logger = JSONLConversationLogger(tmp_path)

    entry1: LogEntry = {
        "timestamp": "2026-01-24T10:30:00+00:00",
        "event_type": "doc_selection",
        "thread_id": 123,
        "user_id": 456,
        "username": "test-user",
        "question": "First question",
        "model": "gpt-4o-mini",
    }
    entry2: LogEntry = {
        "timestamp": "2026-01-24T10:30:15+00:00",
        "event_type": "answer",
        "thread_id": 123,
        "user_id": 456,
        "username": "test-user",
        "question": "First question",
        "model": "gpt-4o-mini",
        "response": "Here is the answer...",
    }

    logger.log(entry1)
    logger.log(entry2)
    logger.close()

    log_files = list(tmp_path.glob("*.jsonl"))
    assert len(log_files) == 1

    content = log_files[0].read_text()
    lines = content.strip().split("\n")
    assert len(lines) == 2

    parsed1 = json.loads(lines[0])
    parsed2 = json.loads(lines[1])
    assert parsed1["event_type"] == "doc_selection"
    assert parsed2["event_type"] == "answer"


def test_jsonl_logger_daily_rotation(tmp_path: Path) -> None:
    """Test that logger rotates to a new file when date changes."""
    logger = JSONLConversationLogger(tmp_path)

    entry1: LogEntry = {
        "timestamp": "2026-01-24T10:30:00+00:00",
        "event_type": "doc_selection",
        "thread_id": 123,
        "user_id": 456,
        "username": "test-user",
        "question": "Question on day 1",
        "model": "gpt-4o-mini",
    }

    # Log entry on "day 1"
    with patch.object(logger, "_get_current_date", return_value="2026-01-24"):
        logger.log(entry1)

    entry2: LogEntry = {
        "timestamp": "2026-01-25T10:30:00+00:00",
        "event_type": "doc_selection",
        "thread_id": 456,
        "user_id": 789,
        "username": "other-user",
        "question": "Question on day 2",
        "model": "gpt-4o-mini",
    }

    # Log entry on "day 2"
    with patch.object(logger, "_get_current_date", return_value="2026-01-25"):
        logger.log(entry2)

    logger.close()

    # Should have two separate files
    log_files = sorted(tmp_path.glob("*.jsonl"))
    assert len(log_files) == 2
    assert log_files[0].name == "2026-01-24.jsonl"
    assert log_files[1].name == "2026-01-25.jsonl"

    # Each file should have one entry
    day1_content = log_files[0].read_text().strip()
    day2_content = log_files[1].read_text().strip()

    assert json.loads(day1_content)["question"] == "Question on day 1"
    assert json.loads(day2_content)["question"] == "Question on day 2"


def test_jsonl_logger_handles_unicode(tmp_path: Path) -> None:
    """Test that logger handles unicode characters correctly."""
    logger = JSONLConversationLogger(tmp_path)
    entry: LogEntry = {
        "timestamp": "2026-01-24T10:30:00+00:00",
        "event_type": "answer",
        "thread_id": 123,
        "user_id": 456,
        "username": "test-user",
        "question": "How do I use emojis? \U0001f600",
        "model": "gpt-4o-mini",
        "response": "Here's how: \u4e2d\u6587 \u65e5\u672c\u8a9e \ud55c\uad6d\uc5b4",
    }
    logger.log(entry)
    logger.close()

    log_files = list(tmp_path.glob("*.jsonl"))
    content = log_files[0].read_text(encoding="utf-8")
    parsed = json.loads(content.strip())
    assert "\U0001f600" in parsed["question"]
    assert "\u4e2d\u6587" in parsed["response"]


def test_jsonl_logger_handles_write_error(tmp_path: Path) -> None:
    """Test that logger handles write errors gracefully."""
    logger = JSONLConversationLogger(tmp_path)

    entry: LogEntry = {
        "timestamp": "2026-01-24T10:30:00+00:00",
        "event_type": "doc_selection",
        "thread_id": 123,
        "user_id": 456,
        "username": "test-user",
        "question": "Test",
        "model": "gpt-4o-mini",
    }

    # First log to open the file
    logger.log(entry)

    # Mock file.write to raise an error
    with patch.object(logger._file, "write", side_effect=IOError("Disk full")):
        # Should not raise, just log a warning
        logger.log(entry)

    logger.close()


def test_jsonl_logger_close_without_logging(tmp_path: Path) -> None:
    """Test that close() works even if no entries were logged."""
    logger = JSONLConversationLogger(tmp_path)
    # Should not raise
    logger.close()

    # No files should be created
    log_files = list(tmp_path.glob("*.jsonl"))
    assert len(log_files) == 0


def test_jsonl_logger_close_is_idempotent(tmp_path: Path) -> None:
    """Test that close() can be called multiple times."""
    logger = JSONLConversationLogger(tmp_path)
    entry: LogEntry = {
        "timestamp": "2026-01-24T10:30:00+00:00",
        "event_type": "doc_selection",
        "thread_id": 123,
        "user_id": 456,
        "username": "test-user",
        "question": "Test",
        "model": "gpt-4o-mini",
    }
    logger.log(entry)

    # Close multiple times should not raise
    logger.close()
    logger.close()
    logger.close()


def test_jsonl_logger_file_name_format(tmp_path: Path) -> None:
    """Test that log files are named with YYYY-MM-DD format."""
    logger = JSONLConversationLogger(tmp_path)

    entry: LogEntry = {
        "timestamp": "2026-01-24T10:30:00+00:00",
        "event_type": "doc_selection",
        "thread_id": 123,
        "user_id": 456,
        "username": "test-user",
        "question": "Test",
        "model": "gpt-4o-mini",
    }

    with patch.object(logger, "_get_current_date", return_value="2026-12-31"):
        logger.log(entry)

    logger.close()

    log_files = list(tmp_path.glob("*.jsonl"))
    assert len(log_files) == 1
    assert log_files[0].name == "2026-12-31.jsonl"


def test_jsonl_logger_answer_entry_with_all_fields(tmp_path: Path) -> None:
    """Test logging a complete answer entry with all fields."""
    logger = JSONLConversationLogger(tmp_path)
    entry: LogEntry = {
        "timestamp": "2026-01-24T10:30:15+00:00",
        "event_type": "answer",
        "thread_id": 123456,
        "user_id": 789,
        "username": "user",
        "guild_id": 111,
        "channel_id": 222,
        "question": "How do I use tool calling?",
        "model": "gpt-4o-mini",
        "request_messages": [
            {"role": "user", "content": "How do I use tool calling?"},
        ],
        "response": "To use tool calling...",
        "docs_loaded": ["openai", "langchain"],
        "token_usage": {
            "prompt_tokens": 2500,
            "completion_tokens": 300,
            "total_tokens": 2800,
        },
        "latency_ms": 3500,
    }
    logger.log(entry)
    logger.close()

    log_files = list(tmp_path.glob("*.jsonl"))
    content = log_files[0].read_text()
    parsed = json.loads(content.strip())

    assert parsed["event_type"] == "answer"
    assert parsed["guild_id"] == 111
    assert parsed["channel_id"] == 222
    assert len(parsed["request_messages"]) == 1
    assert parsed["docs_loaded"] == ["openai", "langchain"]
    assert parsed["latency_ms"] == 3500
