import unittest
import asyncio
import shutil
from agent_sdk.core.agent import UniversalAgent
from agent_sdk.drivers.gemini_driver import GeminiDriver
from agent_sdk.core.types import AgentEvent

class TestGeminiE2E(unittest.TestCase):
    
    def setUp(self):
        # Check if gemini CLI is installed
        if not shutil.which("gemini"):
            self.skipTest("gemini CLI not found in PATH")

    def test_gemini_cli_chat(self):
        """
        Real E2E test invoking the local 'gemini' CLI.
        Requires 'gemini' to be authenticated.
        """
        async def run():
            driver = GeminiDriver(executable_path="gemini")
            agent = UniversalAgent(driver)
            
            # Simple query
            response = await agent.chat("Say 'E2E Test Passed' and nothing else.")
            return response, driver.session_id

        response_text, session_id = asyncio.run(run())
        
        # Verify response contains the expected phrase
        self.assertIn("E2E Test Passed", response_text)
        # Verify session ID was captured
        self.assertIsNotNone(session_id)

if __name__ == "__main__":
    unittest.main()
