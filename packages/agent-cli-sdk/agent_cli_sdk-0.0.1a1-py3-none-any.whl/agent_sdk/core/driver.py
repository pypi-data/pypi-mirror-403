from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, List

from .types import Message, StreamEvent, ToolDefinition


class AgentDriver(ABC):
    """
    The abstract base class that all specific CLI drivers must implement.
    This acts as the 'Adapter' in our architecture.
    """

    @abstractmethod
    async def start(self) -> None:
        """Initialize the underlying CLI process or connection."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Terminate the underlying CLI process or connection."""
        pass

    @abstractmethod
    def set_tools(self, tools: List[ToolDefinition]) -> None:
        """Register tools with the underlying agent."""
        pass

    @abstractmethod
    def set_system_prompt(self, prompt: str) -> None:
        """Set the system instruction."""
        pass

    @abstractmethod
    async def chat(self, messages: List[Message]) -> AsyncGenerator[StreamEvent, None]:
        """
        Send a conversation history to the agent and yield events back.
        """
        pass

    @abstractmethod
    async def send_tool_result(self, call_id: str, result: Any) -> None:
        """
        Send the result of a tool execution back to the agent
        (required by some protocols like JSON-RPC).
        """
        pass
