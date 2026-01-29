import inspect
from typing import Any, Callable, Dict, get_type_hints


def python_type_to_json_type(py_type: Any) -> str:
    if py_type is str:
        return "string"
    elif py_type is int:
        return "integer"
    elif py_type is float:
        return "number"
    elif py_type is bool:
        return "boolean"
    elif py_type is list:
        return "array"
    elif py_type is dict:
        return "object"
    # Default fallback
    return "string"


def generate_tool_schema(func: Callable) -> Dict[str, Any]:
    """
    Generates a JSON Schema for a Python function's arguments.
    Follows the OpenAI/Gemini tool definition convention.
    """
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name == "self" or param_name == "cls":
            continue

        param_type = type_hints.get(param_name, str)  # Default to string if no hint
        json_type = python_type_to_json_type(param_type)

        properties[param_name] = {
            "type": json_type,
            "description": f"Parameter {param_name}",  # Ideally parse from docstring
        }

        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    return {"type": "object", "properties": properties, "required": required}
