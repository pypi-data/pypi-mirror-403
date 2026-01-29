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
    print(f"--- Universal Tool Use Demo ({driver.__class__.__name__}) ---")

    agent = UniversalAgent(driver, system_instruction="You are a weather assistant.")

    @agent.tool
    def get_weather(location: str):
        """Returns the current weather for a location."""
        return f"Sunny and 25°C in {location}"

    try:
        await driver.start()
        user_query = "What's the weather in Paris?"
        print(f"\nUser: {user_query}")
        
        async for event in agent.stream(user_query):
            if event.type.name == "THOUGHT":
                print(f"🤖 Thought: {event.payload}")
            elif event.type.name == "TOOL_CALL":
                print(f"🛠️  Tool Call: {event.payload['name']}({event.payload['arguments']})")
            elif event.type.name == "TOOL_RESULT":
                print(f"✅ Tool Result: {event.payload['result']}")
            elif event.type.name == "CONTENT":
                print(f"💬 Agent: {event.payload}")

        await driver.stop()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())