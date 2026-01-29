import argparse
from agent_sdk.drivers.gemini_driver import GeminiDriver
from agent_sdk.drivers.copilot_driver import CopilotDriver
from agent_sdk.drivers.mock_driver import MockDriver

def get_driver_from_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--driver", type=str, default="mock", choices=["gemini", "copilot", "mock"])
    args, unknown = parser.parse_known_args()
    
    if args.driver == "gemini":
        return GeminiDriver()
    elif args.driver == "copilot":
        # Note: In a real scenario, you might need a custom executable path
        return CopilotDriver(executable_path="copilot")
    else:
        return MockDriver()
