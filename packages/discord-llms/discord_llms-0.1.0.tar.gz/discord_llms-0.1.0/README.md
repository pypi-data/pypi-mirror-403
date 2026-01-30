# discord-llms

A Discord bot that uses LLMs to help users with project documentation. Point it at `llms.txt` files and let users ask questions in Discord threads.

## Features

- **Thread-based conversations**: Each question starts a new thread for focused discussion
- **Smart document selection**: LLM automatically selects relevant documentation for each question
- **Multi-doc support**: Configure multiple documentation sources with summaries
- **OpenAI-compatible API support**: Use any OpenAI-compatible provider (OpenRouter, OpenAI, Anthropic, local LLMs, etc.)
- **Tool calling**: Uses LLM tool calling to intelligently select documentation

## How it works

1. User mentions the bot with a question: `@docs-bot How do I use tool calling?`
1. Bot creates a new thread for the conversation
1. LLM analyzes the question and selects relevant documentation using tool calling
1. Bot fetches the selected `llms.txt` files
1. LLM answers the question using the documentation context
1. Follow-up questions in the thread continue the conversation

## Installation

Install [uv](https://docs.astral.sh/uv/):

**Linux/Mac:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Configuration

### Configuration File

Download the example configuration file:

**Linux/Mac:**

```bash
curl -o config.yaml https://raw.githubusercontent.com/S1M0N38/discord-llms.txt/main/config/config.example.yaml
```

**Windows (PowerShell):**

```powershell
Invoke-WebRequest -Uri https://raw.githubusercontent.com/S1M0N38/discord-llms.txt/main/config/config.example.yaml -OutFile config.yaml
```

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
1. Create a new application
1. Go to "Bot" section and create a bot
1. Enable "Message Content Intent" under Privileged Gateway Intents
1. Copy the bot token (you'll add it to the config file in the next step)
1. Go to "OAuth2" > "URL Generator"
1. Select scopes: `bot`
1. Select permissions: `Send Messages`, `Create Public Threads`, `Send Messages in Threads`, `Read Message History`
1. Use the generated URL to invite the bot to your server

### LLM Provider Setup

The bot needs an LLM API to function. Get an API key from one of these providers:

- **OpenRouter**: [https://openrouter.ai/settings/keys](https://openrouter.ai/settings/keys) (recommended - supports multiple models including Claude)
- **OpenAI**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

Any OpenAI-compatible API works. You can also use local LLMs with tools like Ollama or LM Studio.

### Edit Configuration

Now edit `config.yaml` with your credentials:

1. Set `bot.token` to your Discord bot token (from Discord Bot Setup)
1. Set `model.api_key` to your LLM provider API key (from LLM Provider Setup)
1. Optionally customize `model.base_url` and `model.name` for your provider

See the comprehensive comments in `config.yaml` for all available options and examples.

## Usage

```bash
uvx discord-llms --config config.yaml
```

## Deploy (Docker)

Build and export an image with your config baked in:

```bash
make export CONFIG=path/to/config.yaml TAG=latest
```

You can also pass the config path positionally:

```bash
make export path/to/config.yaml TAG=latest
```

This creates `discord-llms-<tag>.tar`. Treat it as sensitive because it contains your secrets.

Load the image:

```bash
docker load -i discord-llms-latest.tar
```

Run it (logs persisted host):

```bash
docker run -d --name discord-llms \
  --restart unless-stopped \
  -v /volume1/docker/discord-llms/logs:/app/logs \
  discord-llms:latest
```
