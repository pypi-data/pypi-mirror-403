"""Conversation logging for LLM interactions."""

import json
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from discord_llms.types import LogEntry

logger = logging.getLogger("discord_llms")


class ConversationLogger(ABC):
    """Abstract base class for conversation logging."""

    @abstractmethod
    def log(self, entry: LogEntry) -> None:
        """Log a conversation entry."""

    @abstractmethod
    def close(self) -> None:
        """Close the logger and release resources."""


class NullLogger(ConversationLogger):
    """No-op logger implementation when logging is disabled."""

    def log(self, entry: LogEntry) -> None:
        """Do nothing."""

    def close(self) -> None:
        """Do nothing."""


class JSONLConversationLogger(ConversationLogger):
    """JSONL logger with daily file rotation.

    Writes log entries to daily files in the format: logs/YYYY-MM-DD.jsonl
    """

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self._current_date: str | None = None
        self._file: TextIO | None = None

    def _get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format."""
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _ensure_file(self) -> None:
        """Ensure the log file is open and rotated if needed."""
        current_date = self._get_current_date()

        if self._current_date != current_date:
            # Date changed, close old file and open new one
            if self._file is not None:
                self._file.close()

            # Create directory if it doesn't exist
            self.directory.mkdir(parents=True, exist_ok=True)

            # Open new file for appending
            log_path = self.directory / f"{current_date}.jsonl"
            self._file = log_path.open("a", encoding="utf-8")
            self._current_date = current_date

    def log(self, entry: LogEntry) -> None:
        """Write a log entry to the current day's JSONL file."""
        try:
            self._ensure_file()
            if self._file is not None:
                line = json.dumps(entry, ensure_ascii=False)
                self._file.write(line + "\n")
                self._file.flush()
        except Exception as e:
            logger.warning(f"Failed to write log entry: {e}")

    def close(self) -> None:
        """Close the current log file."""
        if self._file is not None:
            self._file.close()
            self._file = None
            self._current_date = None
