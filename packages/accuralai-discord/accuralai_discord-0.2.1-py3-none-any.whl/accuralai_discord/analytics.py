"""Analytics and telemetry for Discord bot."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import discord


@dataclass
class BotMetrics:
    """Bot usage metrics."""

    total_messages: int = 0
    total_commands: int = 0
    total_ai_responses: int = 0
    total_errors: int = 0
    total_tokens_prompt: int = 0
    total_tokens_completion: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_latency_ms: float = 0.0
    user_interactions: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    channel_interactions: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    command_usage: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class BotAnalytics:
    """Analytics tracker for Discord bot."""

    def __init__(self) -> None:
        """Initialize analytics tracker."""
        self._metrics = BotMetrics()
        self._latency_history: list[float] = []
        self._start_time = time.time()

    def record_message(self, message: discord.Message) -> None:
        """Record a message interaction."""
        self._metrics.total_messages += 1
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
        self._metrics.user_interactions[user_id] += 1
        self._metrics.channel_interactions[channel_id] += 1

    def record_command(self, command_name: str) -> None:
        """Record a command execution."""
        self._metrics.total_commands += 1
        self._metrics.command_usage[command_name] += 1

    def record_ai_response(
        self,
        *,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: int = 0,
        cache_hit: bool = False,
    ) -> None:
        """Record an AI response."""
        self._metrics.total_ai_responses += 1
        self._metrics.total_tokens_prompt += prompt_tokens
        self._metrics.total_tokens_completion += completion_tokens

        if cache_hit:
            self._metrics.cache_hits += 1
        else:
            self._metrics.cache_misses += 1

        if latency_ms > 0:
            self._latency_history.append(latency_ms)
            # Keep only last 1000 latencies
            if len(self._latency_history) > 1000:
                self._latency_history.pop(0)
            self._metrics.average_latency_ms = sum(self._latency_history) / len(self._latency_history)

    def record_error(self) -> None:
        """Record an error."""
        self._metrics.total_errors += 1

    def get_metrics(self) -> BotMetrics:
        """Get current metrics."""
        return self._metrics

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        uptime_s = time.time() - self._start_time
        uptime_hours = uptime_s / 3600

        return {
            "uptime_hours": round(uptime_hours, 2),
            "total_messages": self._metrics.total_messages,
            "total_commands": self._metrics.total_commands,
            "total_ai_responses": self._metrics.total_ai_responses,
            "total_errors": self._metrics.total_errors,
            "total_tokens": self._metrics.total_tokens_prompt + self._metrics.total_tokens_completion,
            "cache_hit_rate": (
                self._metrics.cache_hits / (self._metrics.cache_hits + self._metrics.cache_misses)
                if (self._metrics.cache_hits + self._metrics.cache_misses) > 0
                else 0.0
            ),
            "average_latency_ms": round(self._metrics.average_latency_ms, 2),
            "top_users": dict(
                sorted(
                    self._metrics.user_interactions.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
            ),
            "top_commands": dict(
                sorted(
                    self._metrics.command_usage.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
            ),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics = BotMetrics()
        self._latency_history.clear()
        self._start_time = time.time()

