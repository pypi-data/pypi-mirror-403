import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

from ..core.driver import AgentDriver
from ..core.types import AgentEvent, Message, Role, StreamEvent, ToolDefinition


class CliJsonDriver(AgentDriver):
    """
    A generic driver for AI CLIs that output Newline-Delimited JSON (JSONL).
    Examples: gemini -o stream-json, copilot --stream-json (hypothetical)
    """

    def __init__(
        self,
        executable_path: str,
        base_args: List[str] = None,
        session_id: Optional[str] = None,
    ):
        self.executable_path = executable_path
        self.base_args = base_args or []
        self.session_id = session_id
        self.tools: List[ToolDefinition] = []
        self.system_instruction: str = ""

    async def start(self) -> None:
        try:
            process = await asyncio.create_subprocess_exec(
                self.executable_path,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.wait()
        except FileNotFoundError as e:
            raise RuntimeError(f"CLI not found at '{self.executable_path}'") from e

    async def stop(self) -> None:
        pass

    def set_tools(self, tools: List[ToolDefinition]) -> None:
        self.tools = tools

    def set_system_prompt(self, prompt: str) -> None:
        self.system_instruction = prompt

    async def chat(self, messages: List[Message]) -> AsyncGenerator[StreamEvent, None]:
        last_message = messages[-1]
        if last_message.role != Role.USER:
            return

        cmd = [self.executable_path] + self.base_args

        # This part is still a bit tool-specific (session resume)
        # But we can generalize it with a hook or specific args
        if self.session_id:
            # Standardizing on --resume if possible, or skip
            cmd.extend(["--resume", self.session_id])

        cmd.append(last_message.content)

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        if process.stdout:
            async for line in process.stdout:
                line_text = line.decode("utf-8").strip()
                if not line_text:
                    continue

                try:
                    data = json.loads(line_text)
                    # We expect the CLI to follow a standard event format:
                    # {"type": "content|tool_use|...", "content": "..."}
                    # If it follows Gemini's format, we map it:
                    for event in self._map_event(data):
                        yield event
                except json.JSONDecodeError:
                    pass
        await process.wait()
        if process.returncode != 0:
            stderr = await process.stderr.read()
            yield StreamEvent(
                type=AgentEvent.ERROR, payload=f"CLI failed: {stderr.decode()}"
            )

    def _map_event(self, data: Dict[str, Any]) -> List[StreamEvent]:
        # Mapping logic (can be overridden by subclasses)
        # For now, default to Gemini-style
        res = []
        t = data.get("type")
        if t == "init":
            self.session_id = data.get("session_id")
        elif t == "message" and data.get("role") == "assistant":
            res.append(
                StreamEvent(type=AgentEvent.CONTENT, payload=data.get("content"))
            )
        elif t == "tool_use":
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
        elif t == "result":
            res.append(StreamEvent(type=AgentEvent.DONE, payload=None))
        return res

    async def send_tool_result(self, call_id: str, result: Any) -> None:
        pass
