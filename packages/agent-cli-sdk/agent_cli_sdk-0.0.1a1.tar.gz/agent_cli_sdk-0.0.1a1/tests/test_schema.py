import unittest
from agent_sdk.utils.schema import generate_tool_schema

class TestSchema(unittest.TestCase):
    def test_generate_tool_schema_simple(self):
        def my_func(a: int, b: str = "default"):
            """Sample docstring."""
            pass
            
        schema = generate_tool_schema(my_func)
        
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["properties"]["a"]["type"], "integer")
        self.assertEqual(schema["properties"]["b"]["type"], "string")
        self.assertIn("a", schema["required"])
        self.assertNotIn("b", schema["required"])

    def test_generate_tool_schema_list(self):
        def list_func(items: list):
            pass
        
        schema = generate_tool_schema(list_func)
        self.assertEqual(schema["properties"]["items"]["type"], "array")

if __name__ == "__main__":
    unittest.main()