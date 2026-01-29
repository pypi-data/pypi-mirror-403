# Changelog

All notable changes to this project will be documented in this file.

## [0.0.1a1] - 2026-01-23

### Added
- Initial technical preview release.
- **Core:** `UniversalAgent` with ReAct loop implementation.
- **Drivers:**
    - `CopilotDriver`: Support for GitHub Copilot CLI (JSON-RPC over stdio).
    - `GeminiDriver`: Support for Google Gemini CLI (streaming JSON).
    - `MockDriver`: For testing and simulation.
- **Features:**
    - Session persistence support.
    - Customizable tool registration.
    - Cross-platform support (macOS/Linux).