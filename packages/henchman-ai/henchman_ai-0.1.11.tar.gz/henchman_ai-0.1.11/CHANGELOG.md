# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.11] - 2026-01-30

### Fixed

- **Rich Markup Escaping**
  - Fixed crash when error messages contain Rich-like markup tags (e.g., `[/dim]`)
  - Added `escape()` to `success()`, `info()`, `warning()`, `error()`, and `heading()` methods in OutputRenderer
  - Prevents `MarkupError` when displaying exception messages that contain bracket sequences

- **RAG Concurrency**
  - Fixed HNSW segment writer errors when multiple henchman instances start simultaneously
  - Lock is now acquired during `RagSystem.__init__` before ChromaDB initialization
  - Added retry logic (3 attempts with backoff) for transient ChromaDB errors
  - Instances that cannot acquire the lock switch to read-only mode gracefully

- **RAG Lock Function**
  - Fixed `acquire_rag_lock()` to return the `RagLock` object instead of the raw file handle
  - Prevents premature file closure when the lock object goes out of scope

- **Test Fixes**
  - Fixed RAG concurrency integration tests to properly mock all dependencies
  - Updated tests to use correct patch paths for module-level vs inline imports

## [0.1.10] - 2026-01-28

### Added

- **RAG Home Directory Storage**
  - RAG indices now stored in `~/.henchman/rag_indices/` instead of project directories
  - Automatic migration of existing project-based indices to home directory
  - Repository identification using git remote URLs and paths for consistent caching
  - New `/rag clear-all` command to clear ALL RAG indices
  - New `/rag cleanup` command to remove old project-based indices

### Changed

- **RAG Configuration**
  - Removed `index_path` setting from RagSettings
  - Added `cache_dir` setting for custom cache location (defaults to `~/.henchman/rag_indices/`)
  - Updated RAG system to use centralized cache instead of project-based storage

### Fixed

- **Code Quality**
  - Updated all RAG tests to work with new home directory storage
  - Fixed test assertions for manifest file locations
  - Enhanced test coverage for repository identification

## [0.1.9] - 2026-01-28

### Added

- **Error Handling & Recovery**
  - Added retry utilities with exponential backoff (`henchman.utils.retry`)
  - NETWORK tools now automatically retry on transient failures (ConnectionError, TimeoutError, OSError)
  - Configurable retry settings: `network_retries`, `retry_base_delay`, `retry_max_delay` in ToolSettings
  - `RetryConfig` dataclass for fine-grained retry configuration
  - `with_retry` decorator and `retry_async` function for custom retry logic

- **Batch Operations**
  - Added `execute_batch()` method to ToolRegistry for parallel tool execution
  - Independent tool calls now execute concurrently using `asyncio.gather()`
  - `BatchResult` dataclass with success/failure counts and individual results
  - Batch execution continues even when some tools fail

## [0.1.8] - 2024-01-XX

### Fixed

- **Safety & Stability**
  - Added safety limits to tools and compactor to prevent excessive resource usage
  - Switched safety limits from character-based to token-based for better model compatibility
  - Fixed indentation and syntax issues in tool implementations
  - Enhanced Python 3.10 compatibility (asyncio.TimeoutError handling)

- **User Interface**
  - Ctrl+C now exits cleanly when waiting for user input at the prompt (prompt_toolkit key binding)
  - Escape key now exits gracefully (no crash) when pressed on empty buffer
  - Added newline after Henchman finishes talking or after tool execution for improved readability

### Added

- **Testing & Quality**
  - Comprehensive integration tests for token management, tool calls, and validation
  - Enhanced test coverage for keyboard interrupt handling
  - Added tests for Ctrl+C and Escape key behavior in input bindings
  - GitHub Actions workflows for CI/CD pipeline

- **Documentation**
  - MkDocs documentation site with Material theme
  - Updated implementation plans and progress reports

## [0.1.7] - 2024-01-XX

### Fixed
- Switched safety limits from character-based to token-based
- Fixed indentation and syntax issues

## [0.1.6] - 2024-01-XX

### Fixed
- Added safety limits to tools and compactor

## [0.1.5] - 2024-01-XX

### Added
- Integration tests for token management

## [0.1.4] - 2024-01-XX

### Added
- Enhanced test coverage

## [0.1.3] - 2024-01-XX

### Added
- Keyboard interrupt handling improvements

## [0.1.2] - 2024-01-XX

### Added
- Python 3.10 compatibility fixes

## [0.1.1] - 2024-01-XX

### Added
- GitHub Actions workflows
- CHANGELOG file

## [0.1.0] - 2024-01-XX

### Added

- **Core Agent System**
  - Agent class with streaming event architecture
  - Event-driven processing (CONTENT, THOUGHT, TOOL_CALL_REQUEST, etc.)
  - Tool execution with confirmation workflow
  - Session management with auto-save

- **Provider System**
  - DeepSeek provider (default)
  - OpenAI-compatible base provider
  - Anthropic provider with native API
  - Ollama provider for local models
  - Provider registry for dynamic provider creation

- **Built-in Tools**
  - `read_file` - Read file contents
  - `write_file` - Write to files
  - `edit_file` - Surgical file edits
  - `ls` - List directory contents
  - `glob` - Find files by pattern
  - `grep` - Search file contents
  - `shell` - Execute shell commands
  - `web_fetch` - Fetch web pages

- **Interactive REPL**
  - Rich terminal UI with theming
  - Slash commands (/help, /quit, /clear, /tools, /chat)
  - File references with @filename syntax
  - Shell command execution with !command syntax
  - Session save/resume functionality

- **MCP Integration**
  - McpClient for single server connections
  - McpManager for multiple servers
  - Trusted/untrusted server modes
  - /mcp list and /mcp status commands

- **Extension System**
  - Extension base class
  - Entry point discovery
  - Local extension loading from ~/.henchman/extensions/
  - /extensions list command

- **Configuration**
  - Hierarchical YAML settings
  - Environment variable overrides
  - HENCHMAN.md context file discovery
  - Workspace and user-level settings

- **Documentation**
  - MkDocs site with Material theme
  - Getting started guide
  - Provider documentation
  - Tool reference
  - MCP integration guide
  - Extension development guide
  - API reference

- **Quality**
  - 100% test coverage (567+ tests)
  - Type hints throughout
  - Google-style docstrings
  - Ruff linting and formatting
  - Mypy type checking

### Changed

- Rebranded from mlg-cli to henchman-ai

[Unreleased]: https://github.com/MGPowerlytics/henchman-ai/compare/v0.1.8...HEAD
[0.1.8]: https://github.com/MGPowerlytics/henchman-ai/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/MGPowerlytics/henchman-ai/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/MGPowerlytics/henchman-ai/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/MGPowerlytics/henchman-ai/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/MGPowerlytics/henchman-ai/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/MGPowerlytics/henchman-ai/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/MGPowerlytics/henchman-ai/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/MGPowerlytics/henchman-ai/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/MGPowerlytics/henchman-ai/releases/tag/v0.1.0
