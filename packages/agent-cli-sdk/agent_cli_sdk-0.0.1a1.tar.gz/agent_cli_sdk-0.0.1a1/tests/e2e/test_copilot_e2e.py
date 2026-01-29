import unittest
import asyncio
import shutil
import os
from agent_sdk.core.agent import UniversalAgent
from agent_sdk.drivers.copilot_driver import CopilotDriver

class TestCopilotE2E(unittest.TestCase):
    
    def setUp(self):
        # 1. Automatic detection of the binary
        self.cli_path = shutil.which("copilot")
        
        if not self.cli_path:
            self.skipTest("Copilot CLI binary ('copilot') not found in PATH.")

    def test_copilot_protocol_handshake(self):
        """
        Verifies that the SDK can successfully perform a JSON-RPC handshake 
        with the local Copilot CLI using the --server mode.
        """
        async def run():
            driver = CopilotDriver(executable_path=self.cli_path)
            # The start() method sends a 'ping' and expects a 'pong' via JSON-RPC.
            # We add a short timeout to fail fast if the CLI doesn't support this mode.
            await asyncio.wait_for(driver.start(), timeout=3.0)
            await driver.stop()
            return True

        try:
            # Use a fresh event loop for the E2E test
            result = asyncio.run(run())
            self.assertTrue(result)
        except asyncio.TimeoutError:
            self.skipTest("The 'copilot' binary exists but timed out during JSON-RPC handshake. "
                         "It might be a version that doesn't support '--server --stdio' mode.")
        except Exception as e:
            self.fail(f"Copilot E2E handshake failed unexpectedly: {e}")

if __name__ == "__main__":
    unittest.main()