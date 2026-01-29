import asyncio
import sys
import os

# Ensure we can import the src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_sdk.core.agent import UniversalAgent
from utils import get_driver_from_args
from agent_sdk.core.types import AgentEvent

async def main():
    driver = get_driver_from_args()
    print(f"--- Cookbook: Error Handling ({driver.__class__.__name__}) ---")
    
    # 1. Setup
    agent = UniversalAgent(driver)

    # 2. Define a Faulty Tool
    @agent.tool
    def get_user_data(user_id: str):
        """Fetches data for a user. Guaranteed to fail."""
        print(f"[System] Attempting to fetch data for {user_id}...")
        raise ConnectionError("Database is down!")

    # 3. Run the flow
    query = "Get data for user 'admin' and tell me if it worked."
    print(f"\nUser: {query}")
    
    try:
        await driver.start()
        async for event in agent.stream(query):
            if event.type.name == "CONTENT":
                print(f"Agent: {event.payload}", end="", flush=True)
            elif event.type.name == "TOOL_CALL":
                print(f"\n[Agent] Calling: {event.payload['name']}({event.payload['arguments']})")
            elif event.type.name == "TOOL_RESULT":
                print(f"\n[SDK] Tool Result: {event.payload['result']}")
        await driver.stop()
    except Exception as e:
        print(f"\n[Error]: {e}")

if __name__ == "__main__":
    asyncio.run(main())
