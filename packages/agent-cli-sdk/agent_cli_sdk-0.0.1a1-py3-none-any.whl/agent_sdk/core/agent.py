import inspect
import json
from typing import Any, AsyncGenerator, Callable, Dict, List

from ..utils.schema import generate_tool_schema
from .driver import AgentDriver
from .types import AgentEvent, Message, Role, StreamEvent, ToolDefinition


class UniversalAgent:
    """
    The main entry point for the SDK. Developers interact with this class.
    It delegates the actual execution to a specific 'driver'.
    """

    def __init__(self, driver: AgentDriver, system_instruction: str = ""):
        self._driver = driver
        self._system_instruction = system_instruction
        self._tools: List[ToolDefinition] = []
        self._history: List[Message] = []

        # Initialize driver configuration
        self._driver.set_system_prompt(system_instruction)

    def tool(self, func: Callable):
        """
        Decorator to register a function as a tool.
        """
        schema = generate_tool_schema(func)

        tool_def = ToolDefinition(
            name=func.__name__,
            description=func.__doc__ or "",
            parameters=schema,
            function=func,
        )
        self._tools.append(tool_def)
        self._driver.set_tools(self._tools)
        return func

    async def chat(self, user_input: str) -> str:
        """
        Simple non-streaming chat interface.
        Returns the final assistant response text.
        """
        response_text = ""
        async for event in self.stream(user_input):
            if event.type == AgentEvent.CONTENT:
                response_text += event.payload
        return response_text

    async def stream(self, user_input: str) -> AsyncGenerator[StreamEvent, None]:
        """
        Streaming interface that yields events (thoughts, tool calls, content).
        Handles the ReAct loop (Agent -> Tool Call -> Execute -> Tool Result -> Agent).
        """
        # 1. Add user message to history
        self._history.append(Message(role=Role.USER, content=user_input))

        # ReAct loop: continues as long as there are tool calls to process
        max_turns = 10
        for _ in range(max_turns):
            has_tool_calls = False

            async for event in self._driver.chat(self._history):
                yield event

                if event.type == AgentEvent.TOOL_CALL:
                    has_tool_calls = True
                    result = await self._execute_tool(event.payload)

                    try:
                        await self._driver.send_tool_result(event.payload, result)
                    except NotImplementedError:
                        pass

                    self._history.append(
                        Message(
                            role=Role.TOOL,
                            content=str(result),
                            name=event.payload.get("name"),
                        )
                    )

                    yield StreamEvent(
                        type=AgentEvent.TOOL_RESULT,
                        payload={"call_id": event.payload.get("id"), "result": result},
                    )

                if event.type == AgentEvent.DONE or event.type == AgentEvent.ERROR:
                    break

            # If the last stream didn't result in more tool calls,
            # the conversation turn is complete
            if not has_tool_calls:
                break

    async def _execute_tool(self, call_info: Dict[str, Any]) -> Any:
        """Executes a tool based on the call info."""
        name = call_info.get("name")
        args = call_info.get("arguments", {})

        # Find the tool
        tool = next((t for t in self._tools if t.name == name), None)
        if not tool:
            return {"error": f"Tool '{name}' not found", "status": "error"}

        try:
            # Handle if args is a JSON string or dict
            if isinstance(args, str):
                args = json.loads(args)

            # Call the function
            # Check if it's a coroutine
            if inspect.iscoroutinefunction(tool.function):
                result = await tool.function(**args)
            else:
                result = tool.function(**args)
            return result
        except Exception as e:
            return {
                "error": f"Error executing tool '{name}': {str(e)}",
                "status": "error",
            }
