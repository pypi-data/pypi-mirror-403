import asyncio
from typing import Any, AsyncGenerator, Callable, List, Optional

from ..core.driver import AgentDriver
from ..core.types import AgentEvent, Message, StreamEvent, ToolDefinition
from ..utils.jsonrpc import JsonRpcClient


class CopilotDriver(AgentDriver):
    """
    Driver for GitHub Copilot CLI, strictly aligned with Official SDK logic.
    """

    def __init__(
        self,
        executable_path: str = "copilot",
        cli_path: Optional[str] = None,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        mcp_servers: Optional[dict] = None,
        custom_agents: Optional[List[dict]] = None,
        on_permission_request: Optional[Callable] = None,
        skill_directories: Optional[List[str]] = None,
        excluded_tools: Optional[List[str]] = None,
        system_message: Optional[dict] = None,
    ):
        # Allow either executable_path or cli_path for flexibility
        path = cli_path or executable_path
        # Official SDK uses: --server --log-level info --stdio
        full_command = f"{path} --server --log-level info --stdio"
        self.client = JsonRpcClient(full_command, cwd=cwd, env=env)
        self.tools: List[ToolDefinition] = []
        self.session_id = session_id
        self.model = model
        self.system_prompt: str = ""
        self._is_resumed = False if session_id is None else True

        # Extended configuration
        self.mcp_servers = mcp_servers
        self.custom_agents = custom_agents
        self.on_permission_request = on_permission_request
        self.skill_directories = skill_directories
        self.excluded_tools = excluded_tools
        self.system_message = system_message

    async def start(self) -> None:
        # 1. Start Subprocess
        await self.client.start()

        # 2. Ping (Official Handshake)
        try:
            await self.client.request("ping", {"message": "hello"})
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Copilot CLI: {e}") from e

    async def create_session(self) -> str:
        """Explicitly create a new session."""
        payload = {}
        if self.system_message:
            payload["system_message"] = self.system_message
        elif self.system_prompt:
            payload["config"] = {"system_prompt": self.system_prompt}
        else:
            payload["config"] = {"system_prompt": ""}

        if self.model:
            payload["model"] = self.model
        if self.tools:
            payload["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
                for t in self.tools
            ]
        if self.mcp_servers:
            payload["mcp_servers"] = self.mcp_servers
        if self.custom_agents:
            payload["custom_agents"] = self.custom_agents
        if self.skill_directories:
            payload["skill_directories"] = self.skill_directories
        if self.excluded_tools:
            payload["excluded_tools"] = self.excluded_tools

        res = await self.client.request("session.create", payload)
        self.session_id = res.get("sessionId")
        self._is_resumed = False
        return self.session_id

    async def destroy_session(self, session_id: str) -> None:
        """Explicitly destroy a session."""
        await self.client.request("session.destroy", {"sessionId": session_id})
        if self.session_id == session_id:
            self.session_id = None

    async def get_messages(self, session_id: str) -> List[dict]:
        """Get messages for a session."""
        res = await self.client.request(
            "session.getMessages", {"sessionId": session_id}
        )
        return res.get("messages", [])

    async def _ensure_session(self):
        """Internal helper to ensure session is active."""
        if self.session_id and self._is_resumed:
            # We already have a session ID and it was intended to be resumed.
            # Official SDK calls 'session.resume'
            payload = {"sessionId": self.session_id}
            if self.tools:
                payload["tools"] = [
                    {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    }
                    for t in self.tools
                ]
            if self.mcp_servers:
                payload["mcp_servers"] = self.mcp_servers
            if self.custom_agents:
                payload["custom_agents"] = self.custom_agents
            if self.skill_directories:
                payload["skill_directories"] = self.skill_directories
            if self.excluded_tools:
                payload["excluded_tools"] = self.excluded_tools
            if self.system_message:
                payload["system_message"] = self.system_message

            try:
                res = await self.client.request("session.resume", payload)
                self.session_id = res.get("sessionId")
                self._is_resumed = False  # Mark as active
            except Exception as e:
                print(
                    f"[CopilotDriver] Warning: Failed to resume session "
                    f"{self.session_id}: {e}"
                )
                # Fallback to create
                self.session_id = None

        if not self.session_id:
            await self.create_session()

    async def stop(self) -> None:
        if self.session_id:
            try:
                await self.client.request(
                    "session.destroy", {"sessionId": self.session_id}
                )
            except Exception:
                pass
        await self.client.stop()

    def set_tools(self, tools: List[ToolDefinition]) -> None:
        self.tools = tools

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt

    async def chat(self, messages: List[Message]) -> AsyncGenerator[StreamEvent, None]:
        # Ensure we have an active session
        await self._ensure_session()

        last_message = messages[-1]

        # 3. session.send (Official Request)
        # Official SDK returns messageId
        await self.client.request(
            "session.send",
            {"sessionId": self.session_id, "prompt": last_message.content},
        )

        # 4. Event Loop (Official Events)
        # Events come as notifications with method 'session.event'
        while True:
            notification = await self.client.get_notification()
            print(f"[CopilotDriver] Received notification: {notification}")

            # Handle Server Requests (Tools)
            if notification.get("type") == "server_request":
                payload = notification.get("payload")
                method = payload.get("method")
                req_id = payload.get("id")
                params = payload.get("params", {})

                if method == "tool.call":
                    # Official method name is 'tool.call'
                    # The 'id' must be the RPC request ID so we can respond correctly.

                    # Handle permission if callback is provided
                    if self.on_permission_request:
                        req = {
                            "kind": params.get("toolName"),  # Simplified for now
                            "toolCallId": params.get("toolCallId"),
                        }
                        # Add more details if it's a known tool type
                        if params.get("toolName") in ["edit", "create", "delete"]:
                            req["kind"] = "write"
                        elif params.get("toolName") == "shell":
                            req["kind"] = "shell"

                        # Call the handler (could be sync or async)
                        if asyncio.iscoroutinefunction(self.on_permission_request):
                            perm_res = await self.on_permission_request(
                                req, {"session_id": self.session_id}
                            )
                        else:
                            perm_res = self.on_permission_request(
                                req, {"session_id": self.session_id}
                            )

                        if perm_res.get("kind") != "approved":
                            # If not approved, we send a failure response immediately
                            await self.client.send_response(
                                req_id,
                                result={
                                    "toolCallId": params.get("toolCallId"),
                                    "result": {
                                        "resultType": "failure",
                                        "error": "Permission denied by user",
                                    },
                                },
                            )
                            continue

                    yield StreamEvent(
                        type=AgentEvent.TOOL_CALL,
                        payload={
                            "name": params.get("toolName"),
                            "arguments": params.get("arguments"),
                            "id": req_id,
                            "toolCallId": params.get("toolCallId"),
                        },
                    )
                continue

            # Handle Notifications
            method = notification.get("method")
            params = notification.get("params", {})

            if method == "session.event":
                event = params.get("event", {})
                event_type = event.get("type")
                data = event.get("data", {})

                if event_type == "assistant.message":
                    content = data.get("content", "")
                    if content:
                        yield StreamEvent(type=AgentEvent.CONTENT, payload=content)

                elif event_type == "session.idle":
                    yield StreamEvent(type=AgentEvent.DONE, payload={})
                    break

                elif event_type == "session.error":
                    yield StreamEvent(
                        type=AgentEvent.ERROR, payload=data.get("message")
                    )
                    break

            elif method == "log":
                yield StreamEvent(
                    type=AgentEvent.THOUGHT, payload=params.get("message")
                )

    async def send_tool_result(self, call_info: Any, result: Any) -> None:
        """Official SDK requirement: send tool execution result back via RPC."""
        # call_info is the payload from AgentEvent.TOOL_CALL
        req_id = call_info.get("id")
        tool_call_id = call_info.get("toolCallId")

        # Official protocol nesting:
        # { result: { toolCallId: ..., result: { resultType: success, ... } } }
        wrapped_result = {
            "toolCallId": tool_call_id,
            "result": {"resultType": "success", "textResultForLlm": str(result)},
        }
        await self.client.send_response(req_id, result=wrapped_result)
