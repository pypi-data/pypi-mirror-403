import unittest
import asyncio
from typing import List, AsyncGenerator, Any
from agent_sdk.core.agent import UniversalAgent
from agent_sdk.core.types import Message, Role, AgentEvent, StreamEvent, ToolDefinition
from agent_sdk.core.driver import AgentDriver

class MockReActDriver(AgentDriver):
    """
    A controllable driver to simulate ReAct turns.
    """
    def __init__(self):
        self.turns = 0
        self.tools = []

    async def start(self): pass
    async def stop(self): pass
    def set_system_prompt(self, prompt): pass
    def set_tools(self, tools): self.tools = tools
    async def send_tool_result(self, call_id: str, result: Any) -> None: pass

    async def chat(self, messages: List[Message]) -> AsyncGenerator[StreamEvent, None]:
        last_msg = messages[-1]
        
        # Turn 1: User asks -> Driver calls tool
        if self.turns == 0:
            yield StreamEvent(type=AgentEvent.THOUGHT, payload="Thinking...")
            yield StreamEvent(type=AgentEvent.TOOL_CALL, payload={
                "id": "call_1",
                "name": "my_tool",
                "arguments": {"x": 10}
            })
            self.turns += 1
            yield StreamEvent(type=AgentEvent.DONE, payload={})
            
        # Turn 2: Tool result -> Driver answers
        elif self.turns == 1 and last_msg.role == Role.TOOL:
            yield StreamEvent(type=AgentEvent.THOUGHT, payload="Got result.")
            yield StreamEvent(type=AgentEvent.CONTENT, payload=f"Result is {last_msg.content}")
            self.turns += 1
            yield StreamEvent(type=AgentEvent.DONE, payload={})

class TestUniversalAgent(unittest.TestCase):
    
    def test_react_loop(self):
        driver = MockReActDriver()
        agent = UniversalAgent(driver)
        
        @agent.tool
        def my_tool(x: int):
            return x * 2
            
        async def run_test():
            response = await agent.chat("Calculate 10 * 2")
            return response
            
        result = asyncio.run(run_test())
        self.assertEqual(result, "Result is 20")
        self.assertEqual(driver.turns, 2)

if __name__ == "__main__":
    unittest.main()
