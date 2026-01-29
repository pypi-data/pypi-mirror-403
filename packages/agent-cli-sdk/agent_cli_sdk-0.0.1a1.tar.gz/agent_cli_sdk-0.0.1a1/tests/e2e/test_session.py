import unittest
import shutil
from agent_sdk.core.agent import UniversalAgent
from agent_sdk.drivers.copilot_driver import CopilotDriver
from .testharness import get_copilot_path

class TestSessionsE2E(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        pass

    async def test_should_have_stateful_conversation(self):
        driver = CopilotDriver(cli_path=get_copilot_path())
        agent = UniversalAgent(driver)
        await driver.start()
        try:
            await agent.chat("My name is Alice.")
            response = await agent.chat("What is my name?")
            self.assertIn("Alice", response)
        finally:
            await driver.stop()

if __name__ == "__main__":
    unittest.main()