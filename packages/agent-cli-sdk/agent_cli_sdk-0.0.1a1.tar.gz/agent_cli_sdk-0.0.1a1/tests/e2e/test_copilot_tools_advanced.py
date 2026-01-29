import unittest
import asyncio
import os
from agent_sdk.drivers.copilot_driver import CopilotDriver
from agent_sdk.core.agent import UniversalAgent
from tests.e2e.testharness import E2ETestContext, get_final_content, CLI_PATH

class TestCopilotToolsAdvanced(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        self.ctx = E2ETestContext()
        await self.ctx.setup()

    async def asyncTearDown(self):
        await self.ctx.teardown()

    async def test_custom_tool_execution(self):
        """Verify that custom Python tools can be called by Copilot."""
        agent = self.ctx.agent
        
        @agent.tool
        def reverse_string(text: str):
            """Reverses the provided text."""
            return text[::-1]
            
        # We need to make sure the agent knows about the tool
        # In our SDK, UniversalAgent handles the ReAct loop
        
        prompt = "Use the 'reverse_string' tool to reverse the word 'Rocket'."
        response = await agent.chat(prompt)
        
        # The result should contain 'tekcoR'
        self.assertIn("tekcoR", response)

    async def test_built_in_tool_reading_file(self):
        """Verify Copilot can use its built-in file reading tools."""
        agent = self.ctx.agent
        
        # Create a dummy file in the work dir
        file_path = os.path.join(self.ctx.work_dir, "test_file.txt")
        with open(file_path, "w") as f:
            f.write("SECRET_KEY=123456789")
            
        # Copilot usually has access to the current directory
        # We might need to ensure the driver is running in the correct CWD
        # Currently CopilotDriver doesn't explicitly set CWD, let's see if it works.
        
        prompt = f"Read the content of '{file_path}' and tell me the SECRET_KEY."
        response = await agent.chat(prompt)
        
        self.assertIn("123456789", response)

if __name__ == "__main__":
    unittest.main()
