# Contributing to Agent CLI SDK

First off, thank you for considering contributing to the Agent CLI SDK! It's people like you who make this a great tool for the AI community.

## 🚀 Getting Started

### Development Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/rbbtsn0w/agent-cli-sdk.git
    cd agent-cli-sdk
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -e .[test]
    ```

## 🛠 Adding a New Driver

One of the best ways to contribute is by adding support for a new AI CLI (e.g., ChatGPT CLI, Claude CLI).

### Steps to Implement a Driver:

1.  **Inherit from `AgentDriver`**: Create a new file in `src/agent_sdk/drivers/`.
2.  **Choose a pattern**:
    -   **LSP/JSON-RPC**: If the CLI supports a long-running server mode, use `JsonRpcClient`.
    -   **CLI Wrapper**: If the CLI is turn-based, inherit from `CliJsonDriver`.
3.  **Implement required methods**:
    -   `start()`: Initialize the process or handshake.
    -   `chat(messages)`: An async generator yielding `StreamEvent`.
    -   `stop()`: Clean up resources.
4.  **Register events**: Map the CLI's specific JSON output to `AgentEvent` types (CONTENT, THOUGHT, TOOL_CALL, etc.).

## 🧪 Testing

We use `pytest` for testing. High code coverage is expected for all PRs.

```bash
# Run unit and integration tests
pytest tests/ --ignore=tests/e2e

# Run tests with coverage report
pytest --cov=src/agent_sdk tests/ --ignore=tests/e2e --cov-report=term-missing
```

### E2E Tests
E2E tests require the actual CLI tools to be installed and authenticated on your system.

```bash
# Run Gemini E2E
pytest tests/e2e/test_gemini_e2e.py
```

## 📜 Pull Request Process

1.  **Fork** the repo and create your branch from `main`.
2.  **Add tests** for your changes.
3.  **Ensure CI passes**.
4.  **Update documentation** (including this file if you're adding major features).
5.  **Submit** your PR with a clear description of the changes.

## ⚖️ License

By contributing, you agree that your contributions will be licensed under its MIT License.