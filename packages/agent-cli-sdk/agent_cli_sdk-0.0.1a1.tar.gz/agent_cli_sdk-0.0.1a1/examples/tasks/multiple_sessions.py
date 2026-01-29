import asyncio
import sys
import os

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_sdk.core.agent import UniversalAgent
from utils import get_driver_from_args

async def main():
    driver1 = get_driver_from_args()
    driver2 = get_driver_from_args()
    
    print(f"--- Cookbook: Multiple Sessions ({driver1.__class__.__name__}) ---")
    
    # Setup two distinct agents
    agent1 = UniversalAgent(driver1, system_instruction="You are a mathematician.")
    agent2 = UniversalAgent(driver2, system_instruction="You are a poet.")

    try:
        await driver1.start()
        await driver2.start()

        print("\n[Chat with Agent 1]")
        res1 = await agent1.chat("Solve 123 * 456")
        print(f"Math: {res1}")

        print("\n[Chat with Agent 2]")
        res2 = await agent2.chat("Write a 3-word poem about rain.")
        print(f"Poet: {res2}")

        await driver1.stop()
        await driver2.stop()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
