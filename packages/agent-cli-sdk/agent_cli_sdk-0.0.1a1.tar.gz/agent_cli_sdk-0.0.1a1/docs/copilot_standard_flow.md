# Copilot CLI SDK Standard Operation Flow

## 1. Environment Setup
The SDK expects the official GitHub Copilot CLI to be installed and authenticated.
```bash
# Install
brew install copilot-cli # or npm install -g @githubnext/github-copilot-cli
# Authenticate
copilot auth
```

## 2. SDK Initialization (The Official Way)
The Python SDK initializes by spawning the CLI as a subprocess.

### Execution Command
The default command used is:
`copilot agent`

### Handshake Sequence
1.  **Launch**: `subprocess.Popen(["copilot", "agent"], ...)`
2.  **Initialize**: Client sends `initialize` request.
3.  **Capabilities Negotiation**: Client and Server exchange supported features (e.g., `textDocument/read`, `workspace/executeCommand`).

## 3. Communication Loop
1.  **User Prompt**: Client sends `conversation/turn`.
2.  **Streaming**: Server sends multiple `notification` messages with `content_delta`.
3.  **Tool Execution**:
    *   If the model needs to read a file, the Server sends a `request` to the Client: `workspace/executeCommand` with arguments like `{"command": "read_file", "args": {"path": "..."}}`.
    *   The **Client (SDK)** executes the local Python/System function.
    *   The **Client** returns the result to the Server via a JSON-RPC response.

## 4. Integration in `agent-cli-sdk`
Our `CopilotDriver` follows this exact flow:
*   It uses `JsonRpcClient` to manage the stdio pipe.
*   It sends the same `initialize` and `chat/start` (mapped to `conversation/turn`) messages.
*   It is designed to handle the incoming `server_request` for tool execution.
