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
    print(f"--- Cookbook: PR Visualization ({driver.__class__.__name__}) ---")
    
    agent = UniversalAgent(driver, system_instruction="You are a helpful DevOps assistant.")

    # 1. Define Tool: Get PR
    @agent.tool
    def get_pr_diff(pr_id: int):
        """Fetches the code diff for a given PR ID."""
        print(f"[System] Fetching diff for PR #{pr_id}...")
        # Mock diff
        return """
        diff --git a/main.py b/main.py
        index 834a..223b 100644
        ---
        +++ b/main.py
        @@ -1,2 +1,2 @@
        -print(\"Hello\")
        +print(\"Hello World\")
        """

    # 2. Define Tool: Visualize
    @agent.tool
    def generate_ascii_chart(data: str):
        """Generates an ASCII visualization of the data."""
        print(f"[System] Generating chart...")
        return f"""
        +-------------------+
        | PR Visualization  |
        +-------------------+ 
        | Lines Added:   1  | [=]
        | Lines Removed: 1  | [-]
        +-------------------+
        """

    # 3. Complex Query requiring multiple steps
    query = "Visualize the changes in PR #42."
    print(f"\nUser: {query}")
    
    try:
        await driver.start()
        async for event in agent.stream(query):
            if event.type.name == "CONTENT":
                print(f"{event.payload}", end="", flush=True)
            elif event.type.name == "TOOL_CALL":
                print(f"\n[Agent] Calling: {event.payload['name']}")
        await driver.stop()
    except Exception as e:
        print(f"\n[Error]: {e}")

    print("\n\n[Done]")

if __name__ == "__main__":
    asyncio.run(main())
