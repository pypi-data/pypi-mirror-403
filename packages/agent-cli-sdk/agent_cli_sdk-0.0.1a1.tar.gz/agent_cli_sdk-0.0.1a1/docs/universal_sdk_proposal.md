# Proposal: Universal Agent SDK (The "Awesome" CLI SDK)

## 1. Executive Summary
**Goal:** Create a unified SDK that allows developers to control *multiple* AI CLI agents (Gemini, GitHub Copilot, etc.) through a single, consistent programming interface.
**Core Concept:** The "Adapter Pattern". The SDK provides a standard `Agent` interface, and "Drivers" handle the specific communication protocols (JSON-RPC for Copilot, REST/Pipe for Gemini).

## 2. Architecture: The Adapter Pattern

### The Core (The "Interface")
The developer interacts *only* with these high-level objects:
*   `UniversalAgent`: The main controller.
*   `ToolDefinition`: A standard way to define functions (normalized schema).
*   `Message`: A standard message format (User/System/Assistant/Tool).

### The Drivers (The "Adapters")
Hidden behind the scenes, specific drivers translate the Core commands into CLI-specific actions:

1.  **Copilot Driver:**
    *   Connects via `stdio` to the `github-copilot-cli`.
    *   Protocol: **JSON-RPC**.
2.  **Gemini Driver:**
    *   Connects via `stdio` (pipe) or HTTP to `gemini-cli`.
    *   Protocol: **REST** or **Custom Pipe**.
3.  **Mock/Echo Driver:**
    *   For testing applications without incurring costs.

## 3. Proposed API Usage

```python
from awesome_agent_sdk import AgentFactory, DriverType

# 1. Choose your "Backend" (Gemini or Copilot)
# Switching agents is just one line of code!
driver = DriverType.GEMINI 
# driver = DriverType.COPILOT

agent = AgentFactory.create(
    driver=driver,
    system_instruction="You are a coding assistant."
)

# 2. Define a generic tool (works for BOTH agents)
@agent.tool
def get_weather(city: str):
    return "Sunny"

# 3. Chat (The code remains identical regardless of the driver)
response = await agent.chat("What's the weather in Tokyo?")
print(response.text)
```

## 4. Comparison: Single SDK vs. Universal SDK

| Feature | Gemini SDK (Original Plan) | Universal SDK (New Plan) |
| :--- | :--- | :--- |
| **Scope** | Gemini Only | Any CLI (Gemini, Copilot, Local Models) |
| **Complexity** | Low (Direct mapping) | Medium (Requires normalization layer) |
| **Value** | Deep integration with Gemini features | Flexibility, No Lock-in, Broader Appeal |
| **Maintenance** | Single API to track | Multiple APIs/CLIs to track |

## 5. Challenges & Solutions
*   **Challenge:** Different capabilities (e.g., Copilot is optimized for code, Gemini for multimodal).
    *   *Solution:* Use a "Capabilities" flag. If a user tries to send an Image to Copilot (which might not support it), throw a helpful `CapabilityError`.
*   **Challenge:** Installation.
    *   *Solution:* The SDK detects which CLIs are installed on the user's system and enables the corresponding drivers.

## 6. Recommendation
Proceed with the **Universal SDK** approach. It positions the project as a critical piece of infrastructure ("The Glue") rather than just a wrapper.
