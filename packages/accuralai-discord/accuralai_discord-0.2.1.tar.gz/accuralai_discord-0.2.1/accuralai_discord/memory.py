"""Conversation memory management using AccuralAI cache."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from accuralai_core.contracts.models import GenerateRequest
from accuralai_core.contracts.protocols import Cache

from .utils import estimate_tokens


class ConversationMemory:
    """Manages conversation history using AccuralAI cache backend."""

    def __init__(
        self,
        cache: Cache,
        *,
        max_history_entries: int = 50,
        max_history_tokens: int | None = None,
        ttl_s: int | None = None,
    ) -> None:
        """
        Initialize conversation memory manager.

        Args:
            cache: AccuralAI cache instance for storage
            max_history_entries: Maximum number of history entries
            max_history_tokens: Maximum tokens in history (truncates oldest)
            ttl_s: TTL in seconds for conversation entries (None = no expiry)
        """
        self._cache = cache
        self._max_history_entries = max_history_entries
        self._max_history_tokens = max_history_tokens
        self._ttl_s = ttl_s

    async def get_history(self, context_key: str) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a context.

        Args:
            context_key: Context key for the conversation

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        cache_key = self._history_cache_key(context_key)
        # Create a dummy request for cache.get signature
        # GenerateRequest requires a non-empty prompt, so we use a placeholder
        from uuid import uuid4

        dummy_request = GenerateRequest(prompt="__history_lookup__", id=uuid4())
        cached_response = await self._cache.get(cache_key, request=dummy_request)

        if cached_response is None:
            return []

        # Extract history from metadata
        history_json = cached_response.metadata.get("conversation_history")
        if history_json is None:
            return []

        if isinstance(history_json, str):
            return json.loads(history_json)
        elif isinstance(history_json, list):
            return history_json
        else:
            return []

    async def append_message(
        self,
        context_key: str,
        role: str,
        content: str,
    ) -> None:
        """
        Append a message to conversation history.

        Args:
            context_key: Context key for the conversation
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        history = await self.get_history(context_key)
        history.append({"role": role, "content": content})

        # Trim history if needed
        history = await self._trim_history(history)

        # Store back to cache
        await self._store_history(context_key, history)

    async def clear_history(self, context_key: str) -> None:
        """
        Clear conversation history for a context.

        Args:
            context_key: Context key for the conversation
        """
        cache_key = self._history_cache_key(context_key)
        await self._cache.invalidate(cache_key)

    async def trim_history(
        self,
        context_key: str,
        max_entries: int | None = None,
    ) -> None:
        """
        Trim conversation history to specified maximum entries.

        Args:
            context_key: Context key for the conversation
            max_entries: Maximum entries to keep (uses config default if None)
        """
        history = await self.get_history(context_key)
        max_entries = max_entries or self._max_history_entries
        if len(history) > max_entries:
            history = history[-max_entries:]
            await self._store_history(context_key, history)

    async def _trim_history(
        self,
        history: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Trim history based on entry count and token limits."""
        # Trim by entry count
        if len(history) > self._max_history_entries:
            history = history[-self._max_history_entries :]

        # Trim by token count if configured
        if self._max_history_tokens is not None:
            total_tokens = sum(
                estimate_tokens(msg.get("content", "")) for msg in history
            )
            while total_tokens > self._max_history_tokens and len(history) > 1:
                # Remove oldest message
                removed = history.pop(0)
                total_tokens -= estimate_tokens(removed.get("content", ""))

        return history

    def _history_cache_key(self, context_key: str) -> str:
        """Generate cache key for conversation history."""
        return f"discord:history:{context_key}"

    async def _store_history(
        self,
        context_key: str,
        history: List[Dict[str, Any]],
    ) -> None:
        """Store conversation history in cache."""
        from accuralai_core.contracts.models import GenerateResponse, Usage
        from uuid import uuid4

        cache_key = self._history_cache_key(context_key)
        history_json = json.dumps(history)

        # Create a minimal response object for storage
        # GenerateResponse requires non-empty output_text unless finish_reason is 'error'
        # We use a placeholder text since this is just for history storage
        response = GenerateResponse(
            id=uuid4(),
            request_id=uuid4(),
            output_text="__history_storage__",  # Placeholder for history storage
            finish_reason="stop",
            usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            latency_ms=0,
            metadata={"conversation_history": history_json},
            validator_events=[],
        )

        await self._cache.set(cache_key, response, ttl_s=self._ttl_s)

