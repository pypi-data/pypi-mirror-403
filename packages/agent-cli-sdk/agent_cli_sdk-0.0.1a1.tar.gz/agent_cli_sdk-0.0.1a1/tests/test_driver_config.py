import unittest
from agent_sdk.drivers.cli_json_driver import CliJsonDriver

class TestDriverConfig(unittest.TestCase):
    
    def test_init_validation(self):
        # Future proofing: ensure we can instantiate with valid paths
        driver = CliJsonDriver(executable_path="ls")
        self.assertEqual(driver.executable_path, "ls")

    def test_non_existent_executable(self):
        # We don't check existence at init, but at start()
        # This aligns with Copilot SDK which validates on start()
        driver = CliJsonDriver(executable_path="/non/existent/path")
        
        # Async test helper
        import asyncio
        async def run():
            with self.assertRaises(RuntimeError) as cm:
                await driver.start()
            self.assertIn("CLI not found", str(cm.exception))
            
        asyncio.run(run())

if __name__ == "__main__":
    unittest.main()
