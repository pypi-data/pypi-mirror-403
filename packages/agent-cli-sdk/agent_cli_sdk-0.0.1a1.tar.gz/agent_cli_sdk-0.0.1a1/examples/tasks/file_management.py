import asyncio
import sys
import os

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_sdk.core.agent import UniversalAgent
from utils import get_driver_from_args
from agent_sdk.core.types import AgentEvent

async def main():
    driver = get_driver_from_args()
    print(f"--- Cookbook: Local Files ({driver.__class__.__name__}) ---")
    
    # Setup
    agent = UniversalAgent(driver)

    # 1. Prepare file
    filename = "test_note.txt"
    with open(filename, "w") as f:
        f.write("Secret Password: Banana")

    try:
        # 2. Register Tool
        @agent.tool
        def read_file_content(path: str):
            """Reads the content of a local file."""
            print(f"[System] Reading file: {path}")
            if not os.path.exists(path):
                return "File not found"
            with open(path, "r") as f:
                return f.read()

        # 3. Chat
        query = f"Read the content of '{filename}' and tell me what the secret is."
        print(f"\nUser: {query}")
        
        await driver.start()
        async for event in agent.stream(query):
            if event.type.name == "CONTENT":
                print(f"Agent: {event.payload}", end="", flush=True)
            elif event.type.name == "TOOL_CALL":
                print(f"\n[Agent] Calling: {event.payload['name']}({event.payload['arguments']})")
            elif event.type.name == "ERROR":
                print(f"\n❌ SDK Error: {event.payload}")
        await driver.stop()

    except Exception as e:
        print(f"\n[Error]: {e}")
    finally:
        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)
        print("\n\n[System] Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(main())