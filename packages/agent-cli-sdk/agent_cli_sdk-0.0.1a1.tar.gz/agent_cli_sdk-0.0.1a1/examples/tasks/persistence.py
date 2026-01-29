import asyncio
import sys
import os

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_sdk.core.agent import UniversalAgent
from utils import get_driver_from_args

async def main():
    driver = get_driver_from_args()
    print(f"--- Universal Session Persistence Demo ({driver.__class__.__name__}) ---")

    # Step 1: Tell the agent something
    print("\n[Turn 1] User: My secret code is 12345.")
    agent1 = UniversalAgent(driver)
    await driver.start()
    await agent1.chat("My secret code is 12345.")
    session_id = driver.session_id
    print(f"[System] Captured Session ID: {session_id}")
    await driver.stop()

    print("\n--- (Simulating Application Restart) ---\\n")

    # Step 2: Resume the session
    driver2 = get_driver_from_args()
    driver2.session_id = session_id
    agent2 = UniversalAgent(driver2)
    
    await driver2.start()
    query = "What was my secret code?"
    print(f"[Turn 2] User: {query}")
    response = await agent2.chat(query)
    print(f"Agent: {response}")
    await driver2.stop()

if __name__ == "__main__":
    asyncio.run(main())
