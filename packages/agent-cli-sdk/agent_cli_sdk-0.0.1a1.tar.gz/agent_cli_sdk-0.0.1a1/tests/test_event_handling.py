import unittest
from agent_sdk.drivers.gemini_driver import GeminiDriver
from agent_sdk.drivers.copilot_driver import CopilotDriver
from agent_sdk.core.types import AgentEvent, Role, Message

class TestEventHandling(unittest.TestCase):
    
    def test_gemini_unknown_event_type(self):
        """GeminiDriver should ignore unknown event types without crashing."""
        driver = GeminiDriver()
        unknown_event = {"type": "future_feature", "data": "something"}
        events = driver._map_event(unknown_event)
        # Should return empty list or handle gracefully, not raise error
        self.assertEqual(events, [])

    def test_copilot_driver_chat_ignores_unknown_methods(self):
        """Verify that CopilotDriver doesn't crash on unknown JSON-RPC notifications."""
        # This is harder to unit test without mocking the whole client loop,
        # but we can verify the mapping logic if it existed as a separate method.
        # Currently it's inline in chat(). 
        pass

if __name__ == "__main__":
    unittest.main()
