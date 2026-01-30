"""Tests for CLI entry point."""

import sys

import pytest

from discord_llms.cli import main


def test_cli_config_not_found_exits(tmp_path, monkeypatch, capsys):
    """Test that CLI exits with error when config file not found."""
    missing_config = tmp_path / "missing.yaml"
    monkeypatch.setattr(sys, "argv", ["discord-llms", "-c", str(missing_config)])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Config file not found" in captured.err or "missing.yaml" in captured.err


def test_cli_requires_config_flag(monkeypatch, capsys):
    """Test that CLI exits with error when --config flag is not provided."""
    monkeypatch.setattr(sys, "argv", ["discord-llms"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert (
        exc_info.value.code == 2
    )  # argparse exits with code 2 for missing required args
    captured = capsys.readouterr()
    assert "required" in captured.err.lower() or "--config" in captured.err


def test_cli_shows_help_message_on_missing_config(tmp_path, monkeypatch, capsys):
    """Test that CLI shows helpful instructions when config is missing."""
    missing_config = tmp_path / "nonexistent.yaml"
    monkeypatch.setattr(sys, "argv", ["discord-llms", "-c", str(missing_config)])

    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    assert "config.example.yaml" in captured.err or "To get started" in captured.err
