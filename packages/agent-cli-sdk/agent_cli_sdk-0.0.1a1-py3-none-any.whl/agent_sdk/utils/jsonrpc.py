import asyncio
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class JsonRpcClient:
    """
    A generic async JSON-RPC 2.0 client that communicates over stdio with a subprocess.
    """

    def __init__(
        self, command: str, cwd: Optional[str] = None, env: Optional[dict] = None
    ):
        self.command = command
        self.cwd = cwd
        self.env = env
        self.process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._read_task: Optional[asyncio.Task] = None
        self._notification_queue = asyncio.Queue()

    async def start(self):
        """Starts the subprocess."""
        self.process = await asyncio.create_subprocess_shell(
            self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.cwd,
            env=self.env,
        )
        self._read_task = asyncio.create_task(self._read_loop())
        logger.info(f"Started JSON-RPC process: {self.command}")

    async def stop(self):
        """Stops the subprocess."""
        if self.process:
            if self.process.returncode is None:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    self.process.kill()
            self.process = None

        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

    async def request(self, method: str, params: Any = None) -> Any:
        """Sends a JSON-RPC request and awaits the result."""
        if not self.process:
            raise RuntimeError("Process not running")

        req_id = self._request_id
        self._request_id += 1

        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": req_id}

        future = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = future

        await self._send(payload)
        return await future

    async def notify(self, method: str, params: Any = None):
        """Sends a JSON-RPC notification (no response expected)."""
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        await self._send(payload)

    async def get_notification(self) -> Dict[str, Any]:
        """Waits for the next notification from the server."""
        return await self._notification_queue.get()

    async def _send(self, payload: Dict[str, Any]):
        json_body = json.dumps(payload).encode("utf-8")
        # LSP-style framing: Content-Length header + \r\n\r\n + body
        header = f"Content-Length: {len(json_body)}\r\n\r\n".encode("ascii")

        print(f"[JsonRpc] Sending: {payload}")
        if self.process and self.process.stdin:
            self.process.stdin.write(header + json_body)
            await self.process.stdin.drain()

    async def _read_loop(self):
        """Reads stdout using Hybrid framing (LSP or NDJSON)."""
        if not self.process or not self.process.stdout:
            return

        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    logger.info("[JsonRpc] EOF reached")
                    break

                line_str = line.decode("utf-8", errors="ignore").strip()
                if not line_str:
                    continue

                # 1. Check for LSP Header
                if line_str.lower().startswith("content-length:"):
                    try:
                        content_length = int(line_str.split(":", 1)[1].strip())
                        # Skip the following empty line (\r\n)
                        await self.process.stdout.readline()
                        # Read exact body
                        body_bytes = await self.process.stdout.readexactly(
                            content_length
                        )
                        message = json.loads(body_bytes.decode("utf-8"))
                        self._handle_message(message)
                    except Exception as e:
                        logger.error(f"[JsonRpc] Error parsing LSP: {e}")
                    continue

                # 2. Check for NDJSON (Line starting with {)
                if line_str.startswith("{"):
                    try:
                        message = json.loads(line_str)
                        self._handle_message(message)
                    except json.JSONDecodeError:
                        logger.warning(f"[JsonRpc] Failed to decode NDJSON: {line_str}")
                    continue

                # 3. Otherwise, treat as log or noise
                logger.debug(f"[JsonRpc] Log/Noise: {line_str}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[JsonRpc] Read loop error: {e}")
        finally:
            # Cleanup pending requests to avoid permanent hangs
            for _, future in self._pending_requests.items():
                if not future.done():
                    future.set_exception(RuntimeError("Connection closed"))
            self._pending_requests.clear()
            # Also put a sentinel in notification queue if needed?
            # Better to let the consumer handle the closed process.

    def _handle_message(self, message: Dict[str, Any]):
        print(f"[JsonRpc] Internal handle: {message}")
        if "id" in message:
            req_id = message["id"]
            if req_id in self._pending_requests:
                # It's a response to OUR request
                future = self._pending_requests.pop(req_id)
                if "error" in message:
                    future.set_exception(Exception(message["error"]))
                else:
                    future.set_result(message.get("result"))
            else:
                # It's a request FROM the server (Client-side tool execution)
                # We need to handle this. For now, we put it in the notification queue
                # but mark it as a request so the consumer knows to reply.
                self._notification_queue.put_nowait(
                    {"type": "server_request", "payload": message}
                )
        else:
            # It's a notification or log
            self._notification_queue.put_nowait(message)

    async def send_response(self, req_id: Any, result: Any = None, error: Any = None):
        """Sends a JSON-RPC response back to the server."""
        payload = {"jsonrpc": "2.0", "id": req_id}
        if error:
            payload["error"] = error
        else:
            payload["result"] = result

        await self._send(payload)
