"""Tool/function calling support for Discord bot."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, Optional

import discord
from accuralai_core.contracts.models import GenerateResponse

LOGGER = logging.getLogger("accuralai.discord")


class ToolRegistry:
    """Registry for bot tools/functions."""

    def __init__(self) -> None:
        """Initialize tool registry."""
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
    ) -> None:
        """
        Register a tool.

        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for parameters
            handler: Async handler function
        """
        self._tools[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        self._handlers[name] = handler
        LOGGER.debug(f"Registered tool: {name} - {description}")

    def get_tools(self) -> list[Dict[str, Any]]:
        """Get all registered tools as list."""
        tools = list(self._tools.values())
        LOGGER.debug(f"Retrieved {len(tools)} registered tools")
        return tools

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:
        """
        Execute a tool.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            context: Discord context (message, user, etc.)

        Returns:
            Tool execution result
        """
        handler = self._handlers.get(tool_name)
        if not handler:
            LOGGER.debug(f"Tool not found: {tool_name}")
            raise ValueError(f"Unknown tool: {tool_name}")

        LOGGER.debug(f"Executing tool {tool_name} with arguments: {arguments}")
        result = await handler(**arguments, context=context)
        LOGGER.debug(f"Tool {tool_name} execution completed")
        return result


class ToolExecutor:
    """Executes tools from AI responses."""

    def __init__(self, registry: ToolRegistry) -> None:
        """
        Initialize tool executor.

        Args:
            registry: Tool registry
        """
        self._registry = registry

    async def process_tool_calls(
        self,
        response: GenerateResponse,
        message: discord.Message,
    ) -> Optional[str]:
        """
        Process tool calls from AI response.

        Args:
            response: AI response that may contain tool calls
            message: Original Discord message

        Returns:
            Result message to send, or None if no tool calls
        """
        tool_calls = response.metadata.get("tool_calls") or []
        if not tool_calls:
            return None

        results = []
        context = {
            "message": message,
            "user": message.author,
            "channel": message.channel,
            "guild": message.guild,
        }

        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_id = tool_call.get("id", "")
            arguments = tool_call.get("arguments", {})

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            try:
                result = await self._registry.execute(tool_name, arguments, context)
                results.append(
                    {
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "result": result,
                    }
                )
            except Exception as e:
                LOGGER.error(f"Tool execution error: {e}", exc_info=e)
                results.append(
                    {
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "error": str(e),
                    }
                )

        # Format results for user
        if len(results) == 1:
            result = results[0]
            if "error" in result:
                return f"❌ Error executing {result['name']}: {result['error']}"
            return f"✅ Executed {result['name']}: {result['result']}"
        else:
            lines = ["**Tool Execution Results:**"]
            for result in results:
                if "error" in result:
                    lines.append(f"❌ {result['name']}: {result['error']}")
                else:
                    lines.append(f"✅ {result['name']}: {result['result']}")
            return "\n".join(lines)

