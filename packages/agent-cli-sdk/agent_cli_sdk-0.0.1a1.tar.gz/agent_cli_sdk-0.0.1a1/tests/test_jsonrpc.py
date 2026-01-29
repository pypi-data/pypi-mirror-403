import unittest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from agent_sdk.utils.jsonrpc import JsonRpcClient

class MockStream:
    """Mock stream that simulates chunks and short reads."""
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.index = 0

    async def readline(self):
        if self.index >= len(self.chunks):
            return b""
        chunk = self.chunks[self.index]
        if b"\n" in chunk:
            line, rest = chunk.split(b"\n", 1)
            line += b"\n"
            if rest:
                self.chunks[self.index] = rest
            else:
                self.index += 1
            return line
        else:
            self.index += 1
            return chunk

    async def readexactly(self, n):
        buffer = b""
        while len(buffer) < n and self.index < len(self.chunks):
            chunk = self.chunks[self.index]
            needed = n - len(buffer)
            if len(chunk) <= needed:
                buffer += chunk
                self.index += 1
            else:
                buffer += chunk[:needed]
                self.chunks[self.index] = chunk[needed:]
        if len(buffer) < n:
            raise asyncio.IncompleteReadError(buffer, n)
        return buffer

class TestJsonRpcCommunication(unittest.IsolatedAsyncioTestCase):
    
    @patch("asyncio.create_subprocess_shell")
    async def test_read_large_payload_multiple_chunks(self, mock_shell):
        """Tests reading data that requires multiple chunks (simulating pipe behavior)."""
        large_content = "x" * 100000
        message = {"jsonrpc": "2.0", "id": 1, "result": {"data": large_content}}
        body = json.dumps(message).encode('utf-8')
        header = f"Content-Length: {len(body)}\r\n\r\n".encode('ascii')
        full_data = header + body
        
        # Split into small 16KB chunks to force multiple reads
        chunk_size = 16384
        chunks = [full_data[i:i+chunk_size] for i in range(0, len(full_data), chunk_size)]
        
        mock_stdout = MockStream(chunks)
        process = MagicMock()
        process.stdout = mock_stdout
        process.stdin = MagicMock()
        process.stdin.drain = AsyncMock()
        mock_shell.return_value = process
        
        client = JsonRpcClient("dummy")
        await client.start()
        
        # We need a way to wait for the message to be processed
        # In our implementation, it goes to _pending_requests if it has an ID
        future = asyncio.get_running_loop().create_future()
        client._pending_requests[1] = future
        
        result = await asyncio.wait_for(future, timeout=2.0)
        self.assertEqual(result["data"], large_content)
        await client.stop()

    @patch("asyncio.create_subprocess_shell")
    async def test_ndjson_parsing(self, mock_shell):
        """Verifies that the client can handle raw JSON lines (NDJSON)."""
        process = MagicMock()
        process.stdout = MockStream([
            b'{"jsonrpc": "2.0", "method": "notify", "params": "test"}\n',
            b'' # EOF
        ])
        process.stdin = MagicMock()
        process.stdin.drain = AsyncMock()
        mock_shell.return_value = process
        
        client = JsonRpcClient("dummy")
        await client.start()
        
        notification = await client.get_notification()
        self.assertEqual(notification["method"], "notify")
        await client.stop()

    @patch("asyncio.create_subprocess_shell")
    async def test_read_loop_error_cleanup(self, mock_shell):
        """Verifies that pending requests are failed when the connection closes."""
        process = MagicMock()
        process.stdout = MockStream([b''])
        process.stdin = MagicMock()
        process.stdin.drain = AsyncMock()
        mock_shell.return_value = process
        
        client = JsonRpcClient("dummy")
        await client.start()
        
        req_task = asyncio.create_task(client.request("ping"))
        await client.stop()
        
        with self.assertRaises(Exception):
            await req_task

if __name__ == "__main__":
    unittest.main()