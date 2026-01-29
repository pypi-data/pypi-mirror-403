from typing import Any, Dict, List, Optional

from ..core.types import AgentEvent, StreamEvent
from .cli_json_driver import CliJsonDriver


class GeminiDriver(CliJsonDriver):
    """
    Driver for Gemini CLI (The "Agentic" CLI).
    Fully leverages the local 'gemini' binary as the runtime engine.
    """

    def __init__(
        self, executable_path: str = "gemini", session_id: Optional[str] = None
    ):
        # We use -o stream-json to get machine-readable output from the CLI
        super().__init__(
            executable_path, base_args=["-o", "stream-json"], session_id=session_id
        )

    def _map_event(self, data: Dict[str, Any]) -> List[StreamEvent]:
        """
        Maps Gemini CLI's specific JSONL events to universal SDK events.
        """
        res = []
        t = data.get("type")

        if t == "init":
            self.session_id = data.get("session_id")

        elif t == "message":
            if data.get("role") == "assistant" and data.get("content"):
                res.append(
                    StreamEvent(type=AgentEvent.CONTENT, payload=data.get("content"))
                )

        elif t == "tool_use":
            # Surfacing Gemini's internal tool usage as a THOUGHT or TOOL_CALL
            # In Gemini CLI, the CLI executes the tool itself.
            # We report it so the SDK user knows what's happening.
            res.append(
                StreamEvent(
                    type=AgentEvent.THOUGHT,
                    payload=f"Executing built-in tool: {data.get('tool_name')}",
                )
            )
            res.append(
                StreamEvent(
                    type=AgentEvent.TOOL_CALL,
                    payload={
                        "name": data.get("tool_name"),
                        "arguments": data.get("parameters"),
                        "id": data.get("tool_id"),
                    },
                )
            )

        elif t == "tool_result":
            # Report the result of the built-in tool
            res.append(
                StreamEvent(
                    type=AgentEvent.TOOL_RESULT,
                    payload={"id": data.get("tool_id"), "result": data.get("output")},
                )
            )

        elif t == "result":
            res.append(StreamEvent(type=AgentEvent.DONE, payload=None))

        return res

    async def send_tool_result(self, call_id: str, result: Any) -> None:
        """
        Gemini CLI handles its own tools. This is a no-op for the CLI driver.
        (If we want custom Python tools, we'd use GeminiRestDriver).
        """
        pass
