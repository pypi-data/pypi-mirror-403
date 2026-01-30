"""LLM client for OpenRouter API with tool calling support."""

import json
from dataclasses import dataclass
from typing import Any

import httpx
from jinja2 import Environment, PackageLoader
from openai import AsyncOpenAI
from openai._types import NOT_GIVEN
from openai.types.chat import ChatCompletion

from discord_llms.config import Config, DocConfig
from discord_llms.types import ChatMessage, TokenUsage

# Jinja2 environment for loading prompt templates
_jinja_env = Environment(
    loader=PackageLoader("discord_llms", "templates"),
    autoescape=False,  # Plain text prompts, not HTML
    trim_blocks=True,
    lstrip_blocks=True,
)

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "select_docs",
            "description": "Select which documentation sources are relevant to answer the user's question",
            "parameters": {
                "type": "object",
                "properties": {
                    "docs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of documentation names to include in the context",
                    }
                },
                "required": ["docs"],
            },
        },
    }
]


@dataclass
class DocSelectionResult:
    """Result from document selection."""

    selected_docs: list[str]
    token_usage: TokenUsage | None = None


@dataclass
class LLMResponse:
    """Response from the LLM."""

    content: str
    tool_call: dict[str, Any] | None = None
    token_usage: TokenUsage | None = None


class LLMClient:
    """Client for interacting with the LLM via OpenRouter API."""

    def __init__(self, config: Config) -> None:
        self.config: Config = config
        self.openai_client: AsyncOpenAI = AsyncOpenAI(
            api_key=config.model.api_key,
            base_url=config.model.base_url,
            timeout=120.0,
        )
        # Keep httpx client for doc fetching only
        self.http_client: httpx.AsyncClient = httpx.AsyncClient(timeout=120.0)

    async def close(self) -> None:
        """Close the HTTP clients."""
        await self.openai_client.close()
        await self.http_client.aclose()

    def _get_doc_selection_prompts(self) -> tuple[str, str]:
        """Get the system prompt and assistant prefill for document selection."""
        system_template = _jinja_env.get_template("system_doc_selection.md.jinja")
        assistant_template = _jinja_env.get_template("assistant_doc_selection.md.jinja")
        return (
            system_template.render(),
            assistant_template.render(docs=self.config.docs),
        )

    def _get_answering_prompts(self, docs_content: dict[str, str]) -> tuple[str, str]:
        """Get the system prompt and assistant prefill for answering."""
        system_template = _jinja_env.get_template("system_answer_question.md.jinja")
        assistant_template = _jinja_env.get_template(
            "assistant_answer_question.md.jinja"
        )
        return (
            system_template.render(),
            assistant_template.render(docs_content=docs_content),
        )

    async def _call_api(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> ChatCompletion:
        """Make a call to the OpenAI-compatible API."""
        # Get extra params from config (everything except base_url, name, api_key)
        extra_params = (
            dict(self.config.model.model_extra) if self.config.model.model_extra else {}
        )

        response = await self.openai_client.chat.completions.create(
            model=self.config.model.name,
            messages=messages,
            tools=tools if tools else NOT_GIVEN,
            tool_choice="auto" if tools else NOT_GIVEN,
            **extra_params,
        )
        return response

    def _extract_token_usage(self, result: ChatCompletion) -> TokenUsage | None:
        """Extract token usage from a ChatCompletion response."""
        if result.usage is None:
            return None
        return TokenUsage(
            prompt_tokens=result.usage.prompt_tokens,
            completion_tokens=result.usage.completion_tokens,
            total_tokens=result.usage.total_tokens,
        )

    async def select_docs(self, user_question: str) -> DocSelectionResult:
        """Use the LLM to select relevant docs for the user's question."""
        system_prompt, assistant_prefill = self._get_doc_selection_prompts()

        messages: list[ChatMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": assistant_prefill},
            {"role": "user", "content": user_question},
        ]

        result = await self._call_api(messages, tools=TOOLS)
        token_usage = self._extract_token_usage(result)

        choice = result.choices[0]
        tool_calls = choice.message.tool_calls or []

        for tool_call in tool_calls:
            function = getattr(tool_call, "function", None)
            if function and getattr(function, "name", None) == "select_docs":
                args: dict[str, Any] = json.loads(function.arguments)
                return DocSelectionResult(
                    selected_docs=args.get("docs", []),
                    token_usage=token_usage,
                )

        # Fallback: return all docs if no tool call
        return DocSelectionResult(
            selected_docs=[doc.name for doc in self.config.docs],
            token_usage=token_usage,
        )

    async def answer_question(
        self,
        messages: list[ChatMessage],
        docs_content: dict[str, str],
    ) -> LLMResponse:
        """Answer a question with the loaded documentation context."""
        system_prompt, assistant_prefill = self._get_answering_prompts(docs_content)

        api_messages: list[ChatMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": assistant_prefill},
            *messages,
        ]

        result = await self._call_api(api_messages)
        token_usage = self._extract_token_usage(result)

        content = result.choices[0].message.content or ""

        return LLMResponse(content=content, token_usage=token_usage)

    def get_doc_by_name(self, name: str) -> DocConfig | None:
        """Get a document config by name."""
        for doc in self.config.docs:
            if doc.name.lower() == name.lower():
                return doc
        return None

    async def fetch_doc_content(self, doc: DocConfig) -> str:
        """Fetch the content of a document from its URL."""
        try:
            response = await self.http_client.get(doc.url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            return f"Error fetching documentation: {e}"
