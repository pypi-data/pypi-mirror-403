import unittest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from agent_sdk.drivers.copilot_driver import CopilotDriver
from agent_sdk.core.types import Message, Role, AgentEvent

class MockProcess:
    def __init__(self):
        self.stdin = MagicMock()
        self.stdin.drain = AsyncMock()
        self.stdout = MagicMock()
        self.stderr = AsyncMock()
        self.returncode = None
        self._stdout_queue = asyncio.Queue()
        self.stdout.readline = self._mock_readline
        self.stdout.readexactly = self._mock_readexactly

    async def _mock_readline(self):
        return await self._stdout_queue.get()

    async def _mock_readexactly(self, n):
        return await self._stdout_queue.get()
    
    def feed_stdout(self, data: bytes):
        self._stdout_queue.put_nowait(data)

    def kill(self):
        pass
    def terminate(self):
        pass
    async def wait(self):
        return 0

class TestCopilotDriver(unittest.IsolatedAsyncioTestCase):
    
    def _feed_lsp(self, process, json_obj):
        body = json.dumps(json_obj).encode('utf-8')
        # Feed header line
        process.feed_stdout(f"Content-Length: {len(body)}\r\n".encode('ascii'))
        # Feed empty line
        process.feed_stdout(b"\r\n")
        # Feed body
        process.feed_stdout(body)

    @patch("asyncio.create_subprocess_shell")
    async def test_official_protocol_flow(self, mock_create):
        """
        Verifies the official Copilot SDK flow:
        Initialize -> Session.Create -> Session.Send -> Events
        """
        process = MockProcess()
        mock_create.return_value = process
        
        driver = CopilotDriver(executable_path="dummy-cli")
        
        # 1. Start Driver (Spawns process)
        start_task = asyncio.create_task(driver.start())
        await asyncio.sleep(0.01)
        
        # Mock Response to 'ping'
        self._feed_lsp(process, {"jsonrpc": "2.0", "id": 0, "result": {"message": "pong"}})
        await asyncio.wait_for(start_task, timeout=1.0)
        
        # 2. Chat (Trigger Session Create + Send)
        messages = [Message(role=Role.USER, content="Hello")]
        events = []
        
        # Run chat loop in background
        async def consume_chat():
            async for e in driver.chat(messages):
                events.append(e)
        
        consumer_task = asyncio.create_task(consume_chat())
        
        # Mock Response to 'session.create' (Triggered by first chat)
        await asyncio.sleep(0.01)
        self._feed_lsp(process, {"jsonrpc": "2.0", "id": 1, "result": {"sessionId": "sess_001"}})
        
        # Mock Response to 'session.send'
        await asyncio.sleep(0.01)
        self._feed_lsp(process, {"jsonrpc": "2.0", "id": 2, "result": {"messageId": "msg_001"}})
        
        # Mock Response events
        await asyncio.sleep(0.01)
        self._feed_lsp(process, {
            "jsonrpc": "2.0", 
            "method": "session.event", 
            "params": {
                "sessionId": "sess_001",
                "event": {
                    "type": "assistant.message",
                    "data": {"content": "Hello World"}
                }
            }
        })
        
        # Server sends 'session.event' with type 'session.idle'
        self._feed_lsp(process, {
            "jsonrpc": "2.0", 
            "method": "session.event", 
            "params": {
                "sessionId": "sess_001",
                "event": {"type": "session.idle"}
            }
        })
        
        await asyncio.wait_for(consumer_task, timeout=2.0)
        
        # 3. Cleanup
        process.feed_stdout(b'') # EOF
        await driver.stop()
        
        # Assertions
        content = "".join([e.payload for e in events if e.type == AgentEvent.CONTENT])
        self.assertEqual(content, "Hello World")
        self.assertEqual(driver.session_id, "sess_001")

    @patch("asyncio.create_subprocess_shell")
    async def test_session_resume_flow(self, mock_create):
        """Verifies that the driver attempts to resume an existing session."""
        process = MockProcess()
        mock_create.return_value = process
        
        driver = CopilotDriver(executable_path="dummy", session_id="old_sess")
        
        # Start Driver in background task because it awaits a 'ping' response
        start_task = asyncio.create_task(driver.start())
        await asyncio.sleep(0.01)
        
        # Provide ping response to unblock start()
        self._feed_lsp(process, {"jsonrpc": "2.0", "id": 0, "result": {"message": "pong"}})
        await start_task

        # Trigger chat which should call session.resume
        messages = [Message(role=Role.USER, content="Hi")]
        
        # Start chat generator consumption
        chat_iter = driver.chat(messages)
        # First iteration triggers _ensure_session -> session.resume
        chat_task = asyncio.create_task(chat_iter.__anext__())
        
        await asyncio.sleep(0.01)
        # Expecting id: 1 to be session.resume
        self._feed_lsp(process, {"jsonrpc": "2.0", "id": 1, "result": {"sessionId": "old_sess"}})
        
        # Expecting id: 2 to be session.send (after resume returns)
        await asyncio.sleep(0.01)
        self._feed_lsp(process, {"jsonrpc": "2.0", "id": 2, "result": {"messageId": "msg_1"}})
        
        # Feed a log event
        self._feed_lsp(process, {
            "jsonrpc": "2.0", 
            "method": "log", 
            "params": {"message": "Thinking..."}
        })
        # Feed an idle event to finish
        self._feed_lsp(process, {
            "jsonrpc": "2.0", 
            "method": "session.event", 
            "params": {"sessionId": "old_sess", "event": {"type": "session.idle"}}
        })

        # Consume events
        events = []
        # Get the first event from our background task
        events.append(await chat_task)
        # Get remaining events
        async for e in chat_iter:
            events.append(e)

        # Verify log was captured as THOUGHT
        thoughts = [e.payload for e in events if e.type == AgentEvent.THOUGHT]
        self.assertIn("Thinking...", thoughts)
        self.assertEqual(driver.session_id, "old_sess")
        
        # Ensure stop() doesn't hang by feeding response for session.destroy
        stop_task = asyncio.create_task(driver.stop())
        await asyncio.sleep(0.01)
        self._feed_lsp(process, {"jsonrpc": "2.0", "id": 3, "result": True})
        await stop_task

if __name__ == "__main__":
    unittest.main()
