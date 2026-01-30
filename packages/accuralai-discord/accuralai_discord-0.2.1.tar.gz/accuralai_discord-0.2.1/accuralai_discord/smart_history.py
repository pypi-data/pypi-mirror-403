"""Smart history management with summarization and relevance-based pruning."""

from __future__ import annotations

from typing import Any, Dict, List

from accuralai_core.contracts.models import GenerateRequest


class SmartHistoryManager:
    """Manages conversation history with intelligent pruning and summarization."""

    def __init__(
        self,
        *,
        max_entries: int = 50,
        max_tokens: int | None = None,
        summarization_threshold: int = 100,
        relevance_window: int = 20,
    ) -> None:
        """
        Initialize smart history manager.

        Args:
            max_entries: Maximum history entries
            max_tokens: Maximum tokens in history
            summarization_threshold: Number of entries before summarizing
            relevance_window: Keep last N entries regardless of summarization
        """
        self._max_entries = max_entries
        self._max_tokens = max_tokens
        self._summarization_threshold = summarization_threshold
        self._relevance_window = relevance_window

    def should_summarize(self, history: List[Dict[str, Any]]) -> bool:
        """
        Check if history should be summarized.

        Args:
            history: Current history

        Returns:
            True if should summarize
        """
        return len(history) >= self._summarization_threshold

    def summarize_history(
        self,
        history: List[Dict[str, Any]],
        orchestrator: Any,
    ) -> str:
        """
        Summarize old history entries.

        Args:
            history: History to summarize
            orchestrator: AccuralAI orchestrator for summarization

        Returns:
            Summary text
        """
        # Keep recent entries
        recent = history[-self._relevance_window:]
        old = history[:-self._relevance_window]

        if not old:
            return ""

        # Build summarization prompt
        old_text = "\n".join(
            f"{msg['role']}: {msg['content']}" for msg in old
        )

        summary_prompt = f"""Summarize the following conversation history. Focus on key points, decisions, and important context:

{old_text}

Summary:"""

        # Use orchestrator to generate summary
        # Note: This is a placeholder - actual implementation would use orchestrator
        return f"[Previous conversation context: {len(old)} messages]"

    def prune_history(
        self,
        history: List[Dict[str, Any]],
        *,
        estimate_tokens: Any,
    ) -> List[Dict[str, Any]]:
        """
        Prune history based on relevance and token limits.

        Args:
            history: Current history
            estimate_tokens: Function to estimate tokens

        Returns:
            Pruned history
        """
        if len(history) <= self._max_entries:
            return history

        # Always keep recent messages
        recent_count = min(self._relevance_window, self._max_entries)
        recent = history[-recent_count:]
        old = history[:-recent_count]

        # Prune old messages if needed
        if len(history) > self._max_entries:
            # Keep first message (context) and recent messages
            if old:
                first_message = old[0] if old else None
                # Keep middle messages if within limit
                keep_count = self._max_entries - recent_count - (1 if first_message else 0)
                if keep_count > 0 and len(old) > 1:
                    middle = old[1:keep_count + 1]
                    if first_message:
                        return [first_message] + middle + recent
                    return middle + recent
                elif first_message:
                    return [first_message] + recent
            return recent

        # Apply token limit if configured
        if self._max_tokens:
            total_tokens = sum(estimate_tokens(msg.get("content", "")) for msg in history)
            while total_tokens > self._max_tokens and len(history) > 1:
                # Remove oldest non-essential message
                if len(history) > self._relevance_window + 1:
                    history.pop(0)
                else:
                    break

        return history

    def build_contextual_history(
        self,
        history: List[Dict[str, Any]],
        current_message: str,
        *,
        max_context_length: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Build contextual history focusing on relevant messages.

        Args:
            history: Full history
            current_message: Current user message
            max_context_length: Maximum context messages to include

        Returns:
            Contextual history subset
        """
        if len(history) <= max_context_length:
            return history

        # Always include last few messages
        recent = history[-max_context_length:]
        return recent

