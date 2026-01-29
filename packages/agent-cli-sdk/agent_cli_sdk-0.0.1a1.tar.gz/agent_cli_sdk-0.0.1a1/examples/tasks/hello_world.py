import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
# Add examples to path for utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_sdk.core.agent import UniversalAgent
from utils import get_driver_from_args

async def main():
    driver = get_driver_from_args()
    driver_name = driver.__class__.__name__
    
    print(f"=== Universal Hello World ({driver_name}) ===")
    
    try:
        agent = UniversalAgent(driver)
        await driver.start()
        
        query = "Give me a one-sentence greeting!"
        print(f"User: {query}")
        print("Agent: ", end="", flush=True)
        
        async for event in agent.stream(query):
            if event.type.name == "CONTENT":
                print(event.payload, end="", flush=True)
        
        print("\n[Done]")
        await driver.stop()
        
    except Exception as e:
        print(f"\n[Error]: {e}")

if __name__ == "__main__":
    asyncio.run(main())
