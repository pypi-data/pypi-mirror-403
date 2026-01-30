"""Tests for configuration loading."""

import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from discord_llms.config import Config, DocConfig, load_config


def test_load_config() -> None:
    """Test loading configuration from YAML."""
    config_content = """
bot:
  name: test-bot
  token: test-token
  channels: []

docs:
  - test-doc:
      summary: Test documentation summary
      url: https://example.com/docs.txt

model:
  name: test-model
  api_key: test-key
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        f.flush()

        config: Config = load_config(Path(f.name))

        assert config.bot.name == "test-bot"
        assert config.bot.token == "test-token"
        assert config.bot.channels == []
        assert len(config.docs) == 1
        assert config.docs[0].name == "test-doc"
        assert config.docs[0].summary == "Test documentation summary"
        assert config.docs[0].url == "https://example.com/docs.txt"
        assert config.model.name == "test-model"
        assert config.model.api_key == "test-key"
        assert config.model.base_url == "https://openrouter.ai/api/v1"

    os.unlink(f.name)


def test_load_config_with_extra_model_params() -> None:
    """Test loading configuration with extra model parameters."""
    config_content = """
bot:
  name: test-bot
  token: test-token
  channels: []

docs:
  - test-doc:
      summary: Test documentation summary
      url: https://example.com/docs.txt

model:
  name: test-model
  api_key: test-key
  temperature: 0.5
  max_tokens: 2048
  top_p: 0.9
  frequency_penalty: 0.3
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        f.flush()

        config: Config = load_config(Path(f.name))

        assert config.model.name == "test-model"
        assert config.model.api_key == "test-key"
        assert config.model.base_url == "https://openrouter.ai/api/v1"
        # Extra params should be in model_extra
        assert config.model.model_extra is not None
        assert config.model.model_extra["temperature"] == 0.5
        assert config.model.model_extra["max_tokens"] == 2048
        assert config.model.model_extra["top_p"] == 0.9
        assert config.model.model_extra["frequency_penalty"] == 0.3

    os.unlink(f.name)


def test_load_config_with_channels() -> None:
    """Test loading configuration with specific channel IDs."""
    config_content = """
bot:
  name: test-bot
  token: test-token
  channels:
    - 1234567890123456789
    - 9876543210987654321

docs:
  - test-doc:
      summary: Test documentation summary
      url: https://example.com/docs.txt

model:
  name: test-model
  api_key: test-key
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        f.flush()

        config: Config = load_config(Path(f.name))

        assert config.bot.name == "test-bot"
        assert config.bot.token == "test-token"
        assert config.bot.channels == [1234567890123456789, 9876543210987654321]
        assert len(config.bot.channels) == 2

    os.unlink(f.name)


def test_doc_config_requires_valid_url() -> None:
    """Test that DocConfig rejects empty or invalid URLs."""
    # Empty URL should fail
    with pytest.raises(ValidationError):
        DocConfig(name="test", summary="test", url="")

    # Non-HTTP URL should fail
    with pytest.raises(ValidationError):
        DocConfig(name="test", summary="test", url="not-a-url")

    # Valid HTTP URL should work
    doc = DocConfig(name="test", summary="test", url="https://example.com/docs.txt")
    assert doc.url == "https://example.com/docs.txt"

    # Valid HTTP (non-HTTPS) URL should also work
    doc = DocConfig(name="test", summary="test", url="http://example.com/docs.txt")
    assert doc.url == "http://example.com/docs.txt"
