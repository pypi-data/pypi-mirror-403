import os
import shutil
import tempfile
import asyncio
from pathlib import Path
from agent_sdk.drivers.copilot_driver import CopilotDriver
from agent_sdk.core.agent import UniversalAgent

def get_cli_path() -> str:
    """Find the copilot CLI path."""
    cli_path = os.environ.get("COPILOT_CLI_PATH")
    if cli_path and os.path.exists(cli_path):
        return cli_path
    
    # Try common locations
    common_paths = [
        shutil.which("copilot"),
        shutil.which("github-copilot-cli"),
        "/opt/homebrew/bin/copilot",
        "/usr/local/bin/copilot"
    ]
    for p in common_paths:
        if p and os.path.exists(p):
            return p
            
    return None

CLI_PATH = get_cli_path()

def get_copilot_path():
    """Returns the path to the copilot-agent binary."""
    return "/opt/homebrew/bin/copilot"

class MockServer:
    pass

class E2ETestContext:
    def __init__(self):
        self.work_dir = tempfile.mkdtemp(prefix="agent-sdk-test-")
        self.driver = None
        self.agent = None

    async def setup(self):
        if not CLI_PATH:
            raise RuntimeError("Copilot CLI not found. Set COPILOT_CLI_PATH or ensure it is in PATH.")
        
        self.driver = CopilotDriver(executable_path=CLI_PATH, cwd=self.work_dir, env=os.environ.copy())
        self.agent = UniversalAgent(self.driver)
        await self.driver.start()

    async def teardown(self):
        if self.driver:
            await self.driver.stop()
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir, ignore_errors=True)

async def get_final_content(agent, prompt):
    """Helper to get full text from stream."""
    full_content = ""
    async for event in agent.stream(prompt):
        if event.type.name == "CONTENT":
            full_content += event.payload
    return full_content
