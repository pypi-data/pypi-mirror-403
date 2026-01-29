# GitHub Copilot SDK Integration Analysis

## 1. Architecture Overview

The GitHub Copilot SDK acts as a **Client** that controls a local **Copilot Agent**. This agent is the same binary used by the CLI, but running in a specialized "Server Mode" (JSON-RPC).

### The "Sidecar" Pattern
1.  **The App (Python/Node)**: Import the SDK.
2.  **The SDK**: Spawns a subprocess.
    *   Command: `github-copilot-cli` (or configured path).
    *   Arguments: Typically `--stdio` or implicit server mode.
3.  **Communication**:
    *   **STDIN**: SDK sends JSON-RPC Requests (e.g., `initialize`, `conversation/create`).
    *   **STDOUT**: SDK reads JSON-RPC Responses and Notifications.

## 2. Protocol Details (JSON-RPC 2.0)

Unlike a simple CLI wrapper (which sends a string and gets a string), the Copilot SDK maintains a **stateful, bidirectional connection**.

### Lifecycle
1.  **Initialize**:
    *   SDK -> CLI: `initialize` (Capabilities, Client Info).
    *   CLI -> SDK: `initialized` (Server ready).
2.  **Conversation**:
    *   SDK -> CLI: `conversation/create`.
    *   SDK -> CLI: `conversation/turn` (User content).
3.  **Execution (The "ReAct" Loop)**:
    *   CLI -> SDK: `window/logMessage` (Thoughts).
    *   CLI -> SDK: `tool/execute` (Request SDK to run a client-side tool).
    *   SDK -> CLI: `tool/executeResult` (Return tool output).
    *   CLI -> SDK: `conversation/turnResult` (Final answer).

## 3. Key Differences from `gemini` CLI

| Feature | `gemini` CLI | `github-copilot-cli` |
| :--- | :--- | :--- |
| **Mode** | Interactive REPL / One-shot | Long-running JSON-RPC Server |
| **Communication** | JSONL Stream (Events) | JSON-RPC (Request/Response) |
| **Tool Execution** | **Internal** (CLI runs tools itself) | **Delegated** (CLI asks SDK to run tools) |

## 4. Implementation Strategy for `agent-cli-sdk`

To fully align with the official Copilot SDK, our `CopilotDriver` must:

1.  **Spawn Subprocess**: Use `asyncio.create_subprocess_exec`.
2.  **Manage State**: Store `request_id` map to match responses.
3.  **Handle Server Requests**: Listen for `tool/execute` calls from the CLI and dispatch them to Python functions defined in `UniversalAgent`.

## 5. Setup Requirements

Users must have the CLI installed:
```bash
npm install -g @githubnext/github-copilot-cli
```
(Or the specific binary required by the SDK).

## 6. Verification Steps
To verify our implementation matches the official SDK:
1.  Install the official CLI.
2.  Run our `CopilotDriver` pointing to that binary.
3.  Observe the handshake (initialize) and chat flow.
