import unittest
import asyncio
from agent_sdk.drivers.copilot_driver import CopilotDriver
from agent_sdk.core.agent import UniversalAgent
from tests.e2e.testharness import E2ETestContext, get_final_content, CLI_PATH

class TestCopilotSessionAdvanced(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        self.ctx = E2ETestContext()
        await self.ctx.setup()

    async def asyncTearDown(self):
        await self.ctx.teardown()

    async def test_stateful_conversation(self):
        """Verify the session maintains history across multiple turns."""
        agent = self.ctx.agent
        
        # Turn 1
        await agent.chat("Remember this code: AGENT-123")
        
        # Turn 2
        response = await agent.chat("What was the code I asked you to remember?")
        self.assertIn("AGENT-123", response)

    async def test_session_persistence_and_resume(self):
        """Verify we can manually resume a session using its ID."""
        agent1 = self.ctx.agent
        driver1 = self.ctx.driver
        
        # Turn 1
        await agent1.chat("My favorite color is Blue.")
        session_id = driver1.session_id
        self.assertIsNotNone(session_id)
        
        # Stop first driver
        await driver1.stop()
        
        # Create new driver and resume
        driver2 = CopilotDriver(executable_path=CLI_PATH, session_id=session_id)
        agent2 = UniversalAgent(driver2)
        await driver2.start()
        
        # Turn 2
        response = await agent2.chat("What is my favorite color?")
        self.assertIn("Blue", response)
        await driver2.stop()

if __name__ == "__main__":
    unittest.main()
