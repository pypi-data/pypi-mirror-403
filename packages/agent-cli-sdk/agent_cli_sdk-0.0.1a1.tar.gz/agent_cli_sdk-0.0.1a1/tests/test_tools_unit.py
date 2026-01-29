import unittest
from agent_sdk.utils.schema import generate_tool_schema

class TestDefineTool(unittest.TestCase):
    
    def test_creates_tool_with_correct_schema(self):
        def my_tool(query: str, count: int = 5):
            """Search for something."""
            pass
            
        schema = generate_tool_schema(my_tool)
        
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["properties"]["query"]["type"], "string")
        self.assertEqual(schema["properties"]["count"]["type"], "integer")
        # query is required, count has default so not required
        self.assertIn("query", schema["required"])
        self.assertNotIn("count", schema["required"])

    def test_infers_types_from_hints(self):
        def typed_func(active: bool, tags: list):
            pass
        
        schema = generate_tool_schema(typed_func)
        self.assertEqual(schema["properties"]["active"]["type"], "boolean")
        self.assertEqual(schema["properties"]["tags"]["type"], "array")

if __name__ == "__main__":
    unittest.main()
