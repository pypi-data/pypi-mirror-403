"""Streaming response support for Discord bot."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Optional

import discord
from accuralai_core.contracts.models import GenerateResponse

from .utils import split_discord_message


class StreamingResponse:
    """Manages streaming response to Discord."""

    def __init__(
        self,
        channel: discord.TextChannel | discord.DMChannel | discord.Thread,
        *,
        show_typing: bool = True,
        update_interval: float = 0.5,
        max_chunk_size: int = 2000,
    ) -> None:
        """
        Initialize streaming response handler.

        Args:
            channel: Discord channel to send to
            show_typing: Show typing indicator while streaming
            update_interval: Seconds between message updates
            max_chunk_size: Maximum characters per Discord message
        """
        self._channel = channel
        self._show_typing = show_typing
        self._update_interval = update_interval
        self._max_chunk_size = max_chunk_size
        self._message: Optional[discord.Message] = None
        self._buffer: str = ""
        self._last_update: float = 0.0
        self._typing_task: Optional[asyncio.Task] = None

    async def start(self, initial_text: str = "") -> None:
        """Start streaming with optional initial text."""
        if initial_text:
            self._message = await self._channel.send(initial_text)
        else:
            self._message = await self._channel.send("_Generating..._")

        if self._show_typing:
            self._typing_task = asyncio.create_task(self._typing_loop())

    async def append(self, text: str) -> None:
        """Append text to stream."""
        self._buffer += text

        # Check if we should update
        import time

        now = time.time()
        should_update = (
            now - self._last_update >= self._update_interval
            or len(self._buffer) >= self._max_chunk_size
        )

        if should_update and self._message:
            await self._update_message()

    async def finish(self, final_text: Optional[str] = None) -> discord.Message:
        """Finish streaming and return final message."""
        if self._typing_task:
            self._typing_task.cancel()
            try:
                await self._typing_task
            except asyncio.CancelledError:
                pass

        if final_text:
            self._buffer = final_text

        # Split into multiple messages if needed (respecting 3-message limit)
        chunks = split_discord_message(self._buffer, max_size=self._max_chunk_size, max_messages=3)
        
        if not chunks:
            # Empty buffer, send placeholder
            if self._message:
                return self._message
            return await self._channel.send("_No response generated._")
        
        # If we have multiple chunks, send them as separate messages
        if len(chunks) > 1:
            # Delete the streaming message if it exists
            if self._message:
                try:
                    await self._message.delete()
                except discord.HTTPException:
                    pass  # Message might already be deleted
            
            # Send all chunks
            messages = []
            for chunk in chunks:
                msg = await self._channel.send(chunk)
                messages.append(msg)
            return messages[-1]  # Return last message
        
        # Single chunk - update existing message or send new one
        if self._message:
            try:
                await self._message.edit(content=chunks[0])
                return self._message
            except discord.HTTPException:
                # Message might be too long or deleted, send new one
                return await self._channel.send(chunks[0])
        
        # No existing message, send new one
        return await self._channel.send(chunks[0])

    async def _update_message(self, final: bool = False) -> None:
        """Update the Discord message with current buffer."""
        if not self._message:
            return

        import time

        # During streaming, only show first chunk with indicator
        # Final splitting will happen in finish()
        max_display = self._max_chunk_size - 10  # Leave room for "..."
        if len(self._buffer) > max_display:
            # Truncate for display during streaming
            content = self._buffer[:max_display]
            if not final:
                content += "..."  # Indicate more coming
        else:
            content = self._buffer
            if not final:
                content += " ▌"  # Cursor indicator

        try:
            await self._message.edit(content=content)
            self._last_update = time.time()
        except discord.HTTPException:
            # Message might be too long or deleted, send new one
            if final:
                # Final update - use proper splitting
                chunks = split_discord_message(self._buffer, max_size=self._max_chunk_size, max_messages=3)
                if chunks:
                    self._message = await self._channel.send(chunks[0])
            else:
                self._message = await self._channel.send(content)

    async def _typing_loop(self) -> None:
        """Continuously show typing indicator."""
        try:
            while True:
                await self._channel.typing()
                await asyncio.sleep(3)  # Discord typing indicator lasts ~10s
        except asyncio.CancelledError:
            pass


async def stream_response(
    channel: discord.TextChannel | discord.DMChannel | discord.Thread,
    response_stream: AsyncIterator[str],
    *,
    show_typing: bool = True,
    update_interval: float = 0.5,
) -> discord.Message:
    """
    Stream a response to Discord channel.

    Args:
        channel: Discord channel to send to
        response_stream: Async iterator yielding text chunks
        show_typing: Show typing indicator
        update_interval: Seconds between updates

    Returns:
        Final Discord message
    """
    streamer = StreamingResponse(
        channel, show_typing=show_typing, update_interval=update_interval
    )
    await streamer.start()

    async for chunk in response_stream:
        await streamer.append(chunk)

    return await streamer.finish()

