import unittest
import asyncio
from agent_sdk.core.agent import UniversalAgent
from agent_sdk.drivers.mock_driver import MockDriver

class TestHandleToolCallRequest(unittest.IsolatedAsyncioTestCase):
    
    async def test_returns_failure_when_tool_not_registered(self):
        """Verify that executing a non-existent tool returns a proper error structure."""
        driver = MockDriver()
        agent = UniversalAgent(driver)
        
        # Manually trigger _execute_tool which is the internal dispatcher
        response = await agent._execute_tool({
            "name": "missing_tool",
            "arguments": {},
            "id": "123"
        })
        
        self.assertEqual(response["status"], "error")
        self.assertIn("Tool 'missing_tool' not found", response["error"])

if __name__ == "__main__":
    unittest.main()