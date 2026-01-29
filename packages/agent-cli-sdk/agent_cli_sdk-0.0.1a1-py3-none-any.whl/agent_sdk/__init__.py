"""
Agent CLI SDK - Universal interface for AI Agent CLIs (Copilot, Gemini, etc.)
"""

__version__ = "0.0.1a1"

from agent_sdk.core.agent import UniversalAgent
from agent_sdk.core.driver import AgentDriver
from agent_sdk.core.types import AgentEvent, EventType, ToolDefinition
from agent_sdk.drivers.copilot_driver import CopilotDriver
from agent_sdk.drivers.gemini_driver import GeminiDriver
from agent_sdk.drivers.mock_driver import MockDriver

__all__ = [
    "__version__",
    "UniversalAgent",
    "AgentDriver",
    "AgentEvent",
    "EventType",
    "ToolDefinition",
    "CopilotDriver",
    "GeminiDriver",
    "MockDriver",
]
