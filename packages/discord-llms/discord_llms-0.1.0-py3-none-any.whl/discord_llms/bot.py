"""Discord bot implementation."""

import io
import logging
import re
import time
from datetime import UTC, datetime

import discord
from discord.ext import commands

from discord_llms.config import Config
from discord_llms.llm import DocSelectionResult, LLMClient, LLMResponse
from discord_llms.logger import (
    ConversationLogger,
    JSONLConversationLogger,
    NullLogger,
)
from discord_llms.types import ChatMessage, LogEntry, MessageSegment, ThreadContext

logger = logging.getLogger("discord_llms")


class DocsBot(discord.Client):
    """Discord bot for documentation assistance."""

    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(intents=intents)

        self.config: Config = config
        self.llm: LLMClient = LLMClient(config)
        # Track active threads and their conversation history
        self.thread_contexts: dict[int, ThreadContext] = {}
        # Initialize conversation logger
        self.conversation_logger: ConversationLogger = (
            JSONLConversationLogger(config.logging.directory)
            if config.logging.enabled
            else NullLogger()
        )

    async def close(self) -> None:
        """Close the bot and cleanup resources."""
        self.conversation_logger.close()
        await self.llm.close()
        await super().close()

    def _log_doc_selection(
        self,
        message: discord.Message,
        thread: discord.Thread,
        question: str,
        result: DocSelectionResult,
        latency_ms: int,
    ) -> None:
        """Log a doc_selection event."""
        entry: LogEntry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": "doc_selection",
            "thread_id": thread.id,
            "user_id": message.author.id,
            "username": message.author.name,
            "guild_id": message.guild.id if message.guild else None,
            "channel_id": message.channel.id,
            "question": question,
            "model": self.config.model.name,
            "selected_docs": result.selected_docs,
            "latency_ms": latency_ms,
        }
        if result.token_usage:
            entry["token_usage"] = result.token_usage
        self.conversation_logger.log(entry)

    def _log_answer(
        self,
        message: discord.Message,
        thread: discord.Thread,
        question: str,
        request_messages: list[ChatMessage],
        response: LLMResponse,
        docs_loaded: list[str],
        latency_ms: int,
    ) -> None:
        """Log an answer event."""
        entry: LogEntry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": "answer",
            "thread_id": thread.id,
            "user_id": message.author.id,
            "username": message.author.name,
            "guild_id": message.guild.id if message.guild else None,
            "channel_id": message.channel.id,
            "question": question,
            "model": self.config.model.name,
            "request_messages": request_messages,
            "response": response.content,
            "docs_loaded": docs_loaded,
            "latency_ms": latency_ms,
        }
        if response.token_usage:
            entry["token_usage"] = response.token_usage
        self.conversation_logger.log(entry)

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        if self.user:
            logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Loaded {len(self.config.docs)} documentation sources")

    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming messages."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # Check if this is a thread we're tracking
        if isinstance(message.channel, discord.Thread):
            if message.channel.id in self.thread_contexts:
                await self._handle_thread_message(message)
                return

        # Channel filtering for mentions
        # If channels list is specified and non-empty, check if current channel is allowed
        if (
            self.config.bot.channels
            and message.channel.id not in self.config.bot.channels
        ):
            # Silently ignore - bot is not configured for this channel
            return

        # Check if the bot is mentioned in a non-thread channel
        if self.user in message.mentions:
            await self._handle_mention(message)

    async def _handle_mention(self, message: discord.Message) -> None:
        """Handle when the bot is mentioned in a channel."""
        # Remove the mention from the message content
        content: str = message.content
        for mention in message.mentions:
            content = content.replace(f"<@{mention.id}>", "").strip()
            content = content.replace(f"<@!{mention.id}>", "").strip()

        if not content:
            await message.reply(
                "Please include a question! Mention me with your question about the documentation.",
                suppress_embeds=True,
            )
            return

        # Create a thread for this conversation
        thread: discord.Thread = await message.create_thread(
            name=f"Q: {content[:50]}..." if len(content) > 50 else f"Q: {content}",
            auto_archive_duration=60,
        )

        # Send initial thinking message
        thinking_msg: discord.Message = await thread.send(
            "Let me find the relevant documentation...", suppress_embeds=True
        )

        # Use LLM to select relevant docs (with timing)
        start_time = time.perf_counter()
        doc_selection = await self.llm.select_docs(content)
        doc_selection_latency = int((time.perf_counter() - start_time) * 1000)

        # Log doc selection
        self._log_doc_selection(
            message=message,
            thread=thread,
            question=content,
            result=doc_selection,
            latency_ms=doc_selection_latency,
        )

        # Fetch the selected docs
        docs_content: dict[str, str] = {}
        for doc_name in doc_selection.selected_docs:
            doc = self.llm.get_doc_by_name(doc_name)
            if doc:
                doc_content = await self.llm.fetch_doc_content(doc)
                docs_content[doc_name] = doc_content

        if not docs_content:
            await thinking_msg.edit(
                content="I couldn't find any relevant documentation for your question. "
                "Please try rephrasing or ask about a different topic."
            )
            return

        # Update thinking message
        doc_list: str = ", ".join(docs_content.keys())
        await thinking_msg.edit(
            content=f"Found relevant docs: **{doc_list}**\n\nGenerating answer..."
        )

        # Initialize thread context
        self.thread_contexts[thread.id] = {
            "docs": docs_content,
            "messages": [{"role": "user", "content": content}],
        }

        # Get answer from LLM (with timing)
        request_messages: list[ChatMessage] = [{"role": "user", "content": content}]
        start_time = time.perf_counter()
        response = await self.llm.answer_question(
            messages=request_messages,
            docs_content=docs_content,
        )
        answer_latency = int((time.perf_counter() - start_time) * 1000)

        # Log answer
        self._log_answer(
            message=message,
            thread=thread,
            question=content,
            request_messages=request_messages,
            response=response,
            docs_loaded=list(docs_content.keys()),
            latency_ms=answer_latency,
        )

        # Store assistant response in history
        self.thread_contexts[thread.id]["messages"].append(
            {"role": "assistant", "content": response.content}
        )

        # Send the response (split if too long)
        await self._send_long_message(thread, response.content)

        # Delete the thinking message
        await thinking_msg.delete()

    async def _handle_thread_message(self, message: discord.Message) -> None:
        """Handle a message in an active thread."""
        thread: discord.Thread = message.channel  # type: ignore[assignment]
        context: ThreadContext | None = self.thread_contexts.get(thread.id)

        if not context:
            return

        content: str = message.content

        # Add user message to history
        context["messages"].append({"role": "user", "content": content})

        # Send typing indicator
        async with thread.typing():
            # Get answer from LLM with full conversation history (with timing)
            start_time = time.perf_counter()
            response = await self.llm.answer_question(
                messages=context["messages"],
                docs_content=context["docs"],
            )
            answer_latency = int((time.perf_counter() - start_time) * 1000)

        # Log answer
        self._log_answer(
            message=message,
            thread=thread,
            question=content,
            request_messages=list(context["messages"]),
            response=response,
            docs_loaded=list(context["docs"].keys()),
            latency_ms=answer_latency,
        )

        # Store assistant response in history
        context["messages"].append({"role": "assistant", "content": response.content})

        # Send the response
        await self._send_long_message(thread, response.content)

    async def _send_long_message(
        self, channel: discord.abc.Messageable, content: str
    ) -> None:
        """Send a message, splitting if it exceeds Discord's limit.

        Handles code blocks properly by using discord.py's Paginator.
        Large code blocks (>1800 chars) are sent as file attachments.
        """

        max_length: int = 2000
        code_size_threshold: int = 1800  # Send as file if larger

        # Map language to file extension
        extensions: dict[str, str] = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "c++": "cpp",
            "c#": "cs",
            "": "txt",
        }

        # Parse content into segments: text and code blocks
        # Pattern matches: ```language\ncode\n```
        code_pattern: str = r"```([a-zA-Z0-9+#\-_.]*)\n(.*?)\n```"

        segments: list[MessageSegment] = []
        last_end: int = 0

        for match in re.finditer(code_pattern, content, re.DOTALL):
            # Add text before this code block
            if match.start() > last_end:
                text_content: str = content[last_end : match.start()].strip()
                if text_content:
                    segments.append(("text", text_content))

            # Add code block
            language: str = match.group(1) or ""
            language = (
                language.lower().strip()
            )  # Normalize: lowercase and remove whitespace
            code_content: str = match.group(2)
            segments.append(("code", language, code_content))
            last_end = match.end()

        # Add remaining text after last code block
        if last_end < len(content):
            text_content = content[last_end:].strip()
            if text_content:
                segments.append(("text", text_content))

        # If no code blocks found, treat entire content as text
        if not segments:
            segments.append(("text", content))

        # Process each segment
        for segment in segments:
            if segment[0] == "text":
                text = segment[1]

                # Send short text directly
                if len(text) <= max_length:
                    await channel.send(text, suppress_embeds=True)
                    continue

                # Split long text by paragraphs
                chunks: list[str] = []
                current_chunk: str = ""
                paragraphs: list[str] = text.split("\n\n")

                for para in paragraphs:
                    if len(current_chunk) + len(para) + 2 <= max_length:
                        if current_chunk:
                            current_chunk += "\n\n" + para
                        else:
                            current_chunk = para
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        # Handle paragraph longer than max_length
                        if len(para) > max_length:
                            words: list[str] = para.split(" ")
                            current_chunk = ""
                            for word in words:
                                if len(current_chunk) + len(word) + 1 <= max_length:
                                    if current_chunk:
                                        current_chunk += " " + word
                                    else:
                                        current_chunk = word
                                else:
                                    if current_chunk:
                                        chunks.append(current_chunk)
                                    current_chunk = word
                        else:
                            current_chunk = para

                if current_chunk:
                    chunks.append(current_chunk)

                for chunk in chunks:
                    await channel.send(chunk, suppress_embeds=True)

            elif segment[0] == "code":
                language: str = segment[1]
                code: str = segment[2]

                # Check if code block is too large
                if len(code) > code_size_threshold:
                    # Send as file attachment
                    # Use mapped extension, or sanitize language identifier, or default to txt
                    ext: str = extensions.get(
                        language,
                        language
                        if language
                        and language.replace("-", "")
                        .replace("_", "")
                        .replace(".", "")
                        .isalnum()
                        else "txt",
                    )
                    file_content: io.BytesIO = io.BytesIO(code.encode("utf-8"))
                    await channel.send(
                        "Code block too large, sending as file:",
                        file=discord.File(file_content, f"code.{ext}"),
                        suppress_embeds=True,
                    )
                else:
                    # Use Paginator for code block
                    prefix: str = f"```{language}\n" if language else "```\n"
                    suffix: str = "\n```"

                    paginator: commands.Paginator = commands.Paginator(
                        prefix=prefix, suffix=suffix, max_size=max_length
                    )

                    for line in code.split("\n"):
                        paginator.add_line(line)

                    for page in paginator.pages:
                        await channel.send(page, suppress_embeds=True)


async def run_bot(config: Config) -> None:
    """Run the Discord bot."""
    bot = DocsBot(config)
    try:
        await bot.start(config.bot.token)
    finally:
        await bot.close()
