"""Tests for conversation memory."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from accuralai_core.contracts.models import GenerateResponse, Usage
from accuralai_discord.memory import ConversationMemory
from uuid import uuid4


@pytest.fixture
def mock_cache() -> MagicMock:
    """Create a mock cache."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.invalidate = AsyncMock()
    return cache


@pytest.mark.anyio
async def test_get_history_empty(mock_cache: MagicMock) -> None:
    """Test getting history when cache is empty."""
    memory = ConversationMemory(mock_cache)
    history = await memory.get_history("test:context")
    assert history == []


@pytest.mark.anyio
async def test_get_history_with_data(mock_cache: MagicMock) -> None:
    """Test getting history with cached data."""
    cached_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    import json

    response = GenerateResponse(
        id=uuid4(),
        request_id=uuid4(),
        output_text="",
        finish_reason="stop",
        usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
        latency_ms=0,
        metadata={"conversation_history": json.dumps(cached_history)},
        validator_events=[],
    )
    mock_cache.get = AsyncMock(return_value=response)

    memory = ConversationMemory(mock_cache)
    history = await memory.get_history("test:context")
    assert history == cached_history


@pytest.mark.anyio
async def test_append_message(mock_cache: MagicMock) -> None:
    """Test appending a message to history."""
    memory = ConversationMemory(mock_cache, max_history_entries=10)
    await memory.append_message("test:context", "user", "Hello")

    # Should have called set to store history
    assert mock_cache.set.called


@pytest.mark.anyio
async def test_clear_history(mock_cache: MagicMock) -> None:
    """Test clearing conversation history."""
    memory = ConversationMemory(mock_cache)
    await memory.clear_history("test:context")

    mock_cache.invalidate.assert_called_once()
    call_args = mock_cache.invalidate.call_args[0]
    assert call_args[0] == "discord:history:test:context"


@pytest.mark.anyio
async def test_trim_history_by_entries(mock_cache: MagicMock) -> None:
    """Test trimming history by entry count."""
    # Setup: create history with more entries than max
    import json

    long_history = [
        {"role": "user", "content": f"Message {i}"} for i in range(20)
    ]
    response = GenerateResponse(
        id=uuid4(),
        request_id=uuid4(),
        output_text="",
        finish_reason="stop",
        usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
        latency_ms=0,
        metadata={"conversation_history": json.dumps(long_history)},
        validator_events=[],
    )
    mock_cache.get = AsyncMock(return_value=response)

    memory = ConversationMemory(mock_cache, max_history_entries=10)
    await memory.trim_history("test:context")

    # Should have trimmed to 10 entries
    assert mock_cache.set.called
    call_kwargs = mock_cache.set.call_args[1]
    stored_response = call_kwargs["value"]
    stored_history = json.loads(stored_response.metadata["conversation_history"])
    assert len(stored_history) == 10

