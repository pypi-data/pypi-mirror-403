import unittest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from agent_sdk.drivers.gemini_driver import GeminiDriver
from agent_sdk.core.types import Message, Role, AgentEvent

class AsyncIterator:
    def __init__(self, items):
        self.items = iter(items)
    
    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.items)
        except StopIteration:
            raise StopAsyncIteration

# Mock Process for subprocess
class MockProcess:
    def __init__(self, stdout_lines):
        self.stdout = AsyncIterator(stdout_lines)
        self.stderr = AsyncMock()
        self.returncode = 0

    async def wait(self): return 0

class TestGeminiCliDriver(unittest.TestCase):
    
    @patch("asyncio.create_subprocess_exec")
    def test_start_check(self, mock_exec):
        # Mock successful version check
        mock_process = MockProcess([b'v1.0.0\n'])
        mock_exec.return_value = mock_process
        
        driver = GeminiDriver()
        asyncio.run(driver.start())
        
        self.assertTrue(mock_exec.called)
        args, _ = mock_exec.call_args
        self.assertEqual(args[1], "--version")

    @patch("asyncio.create_subprocess_exec")
    def test_chat_interaction(self, mock_exec):
        # Mock CLI output stream
        cli_output = [
            json.dumps({"type": "init", "session_id": "sess_123"}).encode(),
            json.dumps({"type": "message", "role": "assistant", "content": "Hello", "delta": True}).encode(),
            json.dumps({"type": "message", "role": "assistant", "content": " World", "delta": True}).encode(),
            json.dumps({"type": "result", "status": "success"}).encode()
        ]
        
        mock_process = MockProcess(cli_output)
        mock_exec.return_value = mock_process
        
        driver = GeminiDriver()
        # Pre-set session to skip version check logic inside chat? No, chat calls exec directly.
        # But we need to handle the fact that chat() creates a new process.
        
        messages = [Message(role=Role.USER, content="Hi")]
        
        events = []
        async def run():
            async for e in driver.chat(messages):
                events.append(e)
        
        asyncio.run(run())
        
        # Verify Session ID capture
        self.assertEqual(driver.session_id, "sess_123")
        
        # Verify Content
        content = "".join([e.payload for e in events if e.type == AgentEvent.CONTENT])
        self.assertEqual(content, "Hello World")
        
        # Verify Command arguments
        args, _ = mock_exec.call_args
        self.assertIn("gemini", args)
        self.assertIn("-o", args)
        self.assertIn("Hi", args)

    @patch("asyncio.create_subprocess_exec")
    def test_chat_resume(self, mock_exec):
        driver = GeminiDriver()
        driver.session_id = "sess_existing"
        
        mock_process = MockProcess([])
        mock_exec.return_value = mock_process
        
        messages = [Message(role=Role.USER, content="Next")]
        
        async def run():
            async for e in driver.chat(messages):
                pass
        
        asyncio.run(run())
        
        args, _ = mock_exec.call_args
        # Should include --resume sess_existing
        self.assertIn("--resume", args)
        self.assertIn("sess_existing", args)

    @patch("asyncio.create_subprocess_exec")
    def test_tool_event_mapping(self, mock_exec):
        """Verifies mapping of Gemini CLI tool events."""
        cli_output = [
            json.dumps({"type": "tool_use", "tool_name": "search", "parameters": {"q": "test"}, "tool_id": "call_1"}).encode(),
            json.dumps({"type": "tool_result", "tool_id": "call_1", "output": "results"}).encode(),
            json.dumps({"type": "result", "status": "success"}).encode()
        ]
        mock_process = MockProcess(cli_output)
        mock_exec.return_value = mock_process
        
        driver = GeminiDriver()
        events = []
        async def run():
            async for e in driver.chat([Message(role=Role.USER, content="Hi")]):
                events.append(e)
        asyncio.run(run())
        
        # Verify Tool Call
        tool_calls = [e.payload for e in events if e.type == AgentEvent.TOOL_CALL]
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["name"], "search")
        
        # Verify Tool Result
        tool_results = [e.payload for e in events if e.type == AgentEvent.TOOL_RESULT]
        self.assertEqual(len(tool_results), 1)
        self.assertEqual(tool_results[0]["result"], "results")

if __name__ == "__main__":
    unittest.main()