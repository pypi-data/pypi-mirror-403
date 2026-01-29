# Agent CLI SDK

[![CI](https://github.com/rbbtsn0w/agent-cli-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/rbbtsn0w/agent-cli-sdk/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> **Note:** This project is currently in **Technical Preview**.

The `agent-cli-sdk` provides a **universal, programmable interface** for interacting with AI Agent CLIs like **GitHub Copilot** and **Google Gemini**. 

By leveraging your local CLI tools as the "runtime engine," this SDK allows you to build sophisticated agentic applications while reusing existing authentication, session persistence, and local context without managing complex API keys or HTTP clients manually.

## 🚀 Key Features

*   **Universal Agent Interface:** Write your business logic once using `UniversalAgent` and switch between drivers (`CopilotDriver`, `GeminiDriver`, `MockDriver`) seamlessly.
*   **CLI as a Runtime:** Reuses local binary capabilities (auth, tool execution, context awareness).
*   **Full Protocol Support:**
    *   **GitHub Copilot:** Full JSON-RPC support (LSP-style framing) with bidirectional tool execution.
    *   **Google Gemini:** Robust CLI wrapper with streaming JSON event parsing.
*   **ReAct Loop & Custom Tools:** Register any Python function as a tool; the SDK handles the thought-action-observation loop automatically.
*   **Stateful Sessions:** Built-in support for capturing and resuming CLI session IDs across application restarts.

## 📦 Installation

```bash
pip install agent-cli-sdk
```

*Ensure you have the corresponding CLI installed:*
- **Gemini:**  `brew install gemini-cli` shoud be login
- **Copilot:** `brew install copilot-cli` shoud be login

## 🛠 Quick Start

One logic, any engine. Here is how you run a simple chat with Gemini:

```python
import asyncio
from agent_sdk.core.agent import UniversalAgent
from agent_sdk.drivers.gemini_driver import GeminiDriver

async def main():
    # 1. Choose your engine
    driver = GeminiDriver() 
    
    # 2. Initialize the Universal Agent
    agent = UniversalAgent(driver)

    # 3. Stream responses
    print("User: Explain quantum computing.")
    async for event in agent.stream("Explain quantum computing."):
        if event.type.name == "CONTENT":
            print(event.payload, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🎮 Explore Universal Demos

We provide a **Guided Launcher** to explore all SDK capabilities across different drivers.

```bash
python3 examples/demo_launcher.py
```

The launcher will:
1.  **Auto-detect** your environment (checking if `gemini` or `copilot` is installed).
2.  Allow you to **select a Driver Engine**.
3.  Let you **select a Task** (Chat, Custom Tools, Session Persistence, etc.) to run on that engine.

## 🏗 Architecture

The SDK follows a modular "Driver-Controller" pattern:

- **`UniversalAgent`**: The high-level controller. Manages message history, tool registration, and the ReAct execution loop.
- **`AgentDriver`**: The abstraction layer.
    - **`CopilotDriver`**: Implements JSON-RPC 2.0 over Stdio (LSP framing). Supports server-side requests (the CLI asking the SDK to run a tool).
    - **`GeminiDriver`**: Implements the CLI wrapper pattern with `-o stream-json` support.
- **`JsonRpcClient`**: A robust, async-first JSON-RPC client designed for high-concurrency CLI communication.

## 🧪 Development & Testing

We maintain a high-quality codebase with extensive test coverage.

*   **Unit & Integration Tests:** 100% pass rate across 29 core test cases.
*   **Code Coverage:** **82%** (targeting 90%+).
*   **Stability:** Built-in execution timeouts and automated cleanup for subprocesses.

### Running Tests
```bash
# Run all tests with coverage report
pytest --cov=src/agent_sdk tests/ --ignore=tests/e2e --cov-report=term-missing --timeout=5
```

### E2E Testing
E2E tests require authenticated local CLIs:
```bash
# Run Gemini E2E
pytest tests/e2e/test_gemini_e2e.py
```

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
