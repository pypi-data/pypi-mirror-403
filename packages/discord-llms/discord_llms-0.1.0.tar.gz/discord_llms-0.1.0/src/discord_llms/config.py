"""Configuration loading and validation."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, field_validator


class BotConfig(BaseModel):
    """Discord bot configuration."""

    name: str
    token: str
    channels: list[int]  # Empty list = all channels allowed


class DocConfig(BaseModel):
    """Documentation configuration."""

    name: str
    summary: str
    url: str

    @field_validator("url")
    @classmethod
    def url_must_be_valid(cls, v: str) -> str:
        """Validate that url is a valid HTTP/HTTPS URL."""
        if not v or not v.startswith(("http://", "https://")):
            raise ValueError("url must be a valid HTTP/HTTPS URL")
        return v


class ModelConfig(BaseModel):
    """LLM model configuration.

    Required fields: base_url, name, api_key
    Any additional fields (temperature, max_tokens, etc.) are passed through
    to the chat completions API call.
    """

    model_config = ConfigDict(extra="allow")

    base_url: str = "https://openrouter.ai/api/v1"
    name: str
    api_key: str


class LoggingConfig(BaseModel):
    """Conversation logging configuration."""

    enabled: bool = False
    directory: Path = Path("logs")


class Config(BaseModel):
    """Main configuration."""

    bot: BotConfig
    docs: list[DocConfig]
    model: ModelConfig
    logging: LoggingConfig = LoggingConfig()


def load_config(path: Path) -> Config:
    """Load configuration from a YAML file."""
    with path.open() as f:
        data: dict[str, Any] = yaml.safe_load(f)

    # Transform docs list format from YAML
    docs: list[DocConfig] = []
    for doc in data.get("docs", []):
        if isinstance(doc, dict):
            for name, details in doc.items():
                if isinstance(details, dict):
                    docs.append(
                        DocConfig(
                            name=name,
                            summary=details.get("summary", ""),
                            url=details.get("url", ""),
                        )
                    )

    # Parse logging config (optional section)
    logging_data = data.get("logging", {})
    logging_config = LoggingConfig(**logging_data) if logging_data else LoggingConfig()

    return Config(
        bot=BotConfig(**data.get("bot", {})),
        docs=docs,
        model=ModelConfig(**data.get("model", {})),
        logging=logging_config,
    )
