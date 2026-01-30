"""Error handling middleware."""

from __future__ import annotations

import logging
from typing import Any

from accuralai_core.contracts.errors import AccuralAIError
from discord import HTTPException
from discord.errors import RateLimited

LOGGER = logging.getLogger("accuralai.discord")


class ErrorHandler:
    """Handles errors and formats user-friendly messages."""

    @staticmethod
    def format_error(error: Exception, context: dict[str, Any] | None = None) -> str:
        """
        Format error as user-friendly message.

        Args:
            error: Exception that occurred
            context: Additional context (user, channel, etc.)

        Returns:
            User-friendly error message
        """
        if isinstance(error, AccuralAIError):
            error_msg = getattr(error, "message", None) or str(error)
            return f"❌ AI service error: {error_msg}"
        elif isinstance(error, RateLimited):
            retry_after = getattr(error, "retry_after", None)
            if retry_after:
                return (
                    f"⏳ Rate limited. Please try again in {retry_after:.1f} seconds."
                )
            return "⏳ Rate limited. Please try again later."
        elif isinstance(error, HTTPException):
            return f"❌ Discord API error: {error.text or str(error)}"
        else:
            LOGGER.exception("Unexpected error", extra=context)
            return "❌ An unexpected error occurred. Please try again later."

    @staticmethod
    def log_error(
        error: Exception,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Log error with context.

        Args:
            error: Exception that occurred
            context: Additional context
        """
        context = context or {}
        LOGGER.error(
            "Error in Discord bot",
            exc_info=error,
            extra=context,
        )
