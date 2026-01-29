import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from agent_sdk.drivers.copilot_driver import CopilotDriver

class AsyncIterator:
    def __init__(self, items):
        self.items = iter(items)
    def __aiter__(self): return self
    async def __anext__(self):
        try: return next(self.items)
        except StopIteration: raise StopAsyncIteration
    async def readexactly(self, n): return b""
    async def readline(self): return b"" # EOF

class MockProcess:
    def __init__(self):
        self.stdin = MagicMock()
        self.stdin.drain = AsyncMock()
        self.stdout = AsyncIterator([])
        self.stderr = AsyncMock()
        self.returncode = None
    
    def kill(self): pass
    def terminate(self): pass
    async def wait(self): return 0

class TestCleanup(unittest.TestCase):
    
    def _feed_init(self, process):
        # We need a proper mock stdout that returns the init response
        # But constructing AsyncIterator is tedious.
        # Let's just mock client.request to skip handshake wait.
        pass

    @patch("asyncio.create_subprocess_shell")
    def test_stop_should_terminate_process(self, mock_create):
        mock_process = MockProcess()
        # Mock stdout as simple async iterator to avoid attribute errors
        mock_process.stdout = AsyncIterator([]) 
        mock_create.return_value = mock_process
        
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        
        async def run():
            driver = CopilotDriver(executable_path="dummy")
            # Hack: Patch request to avoid waiting for network
            driver.client.request = AsyncMock(return_value={})
            
            await driver.start()
            await driver.stop()
            
            mock_process.terminate.assert_called()
            
        asyncio.run(run())

    @patch("asyncio.create_subprocess_shell")
    def test_force_kill_on_timeout(self, mock_create):
        mock_process = MockProcess()
        mock_process.stdout = AsyncIterator([]) 
        mock_create.return_value = mock_process
        
        async def slow_wait():
            await asyncio.sleep(0.1) 
            return 0
        mock_process.wait = slow_wait
        
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        
        async def run():
            driver = CopilotDriver(executable_path="dummy")
            driver.client.request = AsyncMock(return_value={})
            
            await driver.start()
            await driver.stop()
            
            mock_process.terminate.assert_called()
            
        asyncio.run(run())

if __name__ == "__main__":
    unittest.main()
