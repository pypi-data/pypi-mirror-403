import asyncio
from typing import Any, AsyncGenerator, List

from ..core.driver import AgentDriver
from ..core.types import AgentEvent, Message, Role, StreamEvent, ToolDefinition


class MockDriver(AgentDriver):
    """
    A simple Echo driver for testing the SDK without a real CLI.
    """

    def __init__(self):
        self.tools = []
        self.system_prompt = ""

    async def start(self) -> None:
        print("[MockDriver] Starting...")

    async def stop(self) -> None:
        print("[MockDriver] Stopping...")

    def set_tools(self, tools: List[ToolDefinition]) -> None:
        self.tools = tools
        print(f"[MockDriver] Registered {len(tools)} tools.")

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt
        print(f"[MockDriver] System prompt set: {prompt[:20]}...")

    async def chat(self, messages: List[Message]) -> AsyncGenerator[StreamEvent, None]:
        last_message = messages[-1]

        # If the last message was a tool result, acknowledge it
        if last_message.role == Role.TOOL:
            yield StreamEvent(type=AgentEvent.START, payload=None)
            yield StreamEvent(
                type=AgentEvent.THOUGHT, payload="I received the tool output."
            )
            response = f"The tool result was: {last_message.content}"
            yield StreamEvent(type=AgentEvent.CONTENT, payload=response)
            yield StreamEvent(type=AgentEvent.DONE, payload=None)
            return

        content = last_message.content.lower()

        yield StreamEvent(type=AgentEvent.START, payload=None)

        # Simulate "thinking"
        yield StreamEvent(type=AgentEvent.THOUGHT, payload="Processing request...")
        await asyncio.sleep(0.2)

        # Basic logic to simulate tool calling behavior
        if "weather" in content:
            # Simulate a tool call request from the agent
            tool_call_id = "call_123"
            yield StreamEvent(
                type=AgentEvent.THOUGHT, payload="I need to check the weather."
            )

            # Yield a tool call event
            # In a real driver, this comes from the model
            yield StreamEvent(
                type=AgentEvent.TOOL_CALL,
                payload={
                    "id": tool_call_id,
                    "name": "get_weather",
                    "arguments": {"location": "New York"},
                },
            )
            return

        # Default Echo behavior
        response = f"Echo: {last_message.content}"
        yield StreamEvent(type=AgentEvent.CONTENT, payload=response)

        yield StreamEvent(type=AgentEvent.DONE, payload=None)

    async def send_tool_result(self, call_id: str, result: Any) -> None:
        print(f"[MockDriver] Received tool result for {call_id}: {result}")
