# optix-mcp-server

MCP server for source code analysis.

## Installation

### Option 1: Quick Install with Wizard (Recommended)

The easiest way to install Optix MCP Server is using the installation wizard.

#### Prerequisites

- macOS 12+ or Ubuntu 20.04+
- curl (pre-installed on most systems)

#### One-Command Install

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the installation wizard
uvx --from optix-mcp-server optix install
```

The wizard will guide you through:
1. Selecting AI agents to configure (Claude Code, Cursor, VS Code, Codex CLI, OpenCode)
2. Choosing installation scope (global or local/project)
3. Optional expert analysis setup (requires OpenAI API key)
4. Optional dashboard configuration

#### Wizard Options

| Flag | Description |
|------|-------------|
| `--agents <list>` | Comma-separated agents: claude,cursor,codex,vscode,opencode |
| `--scope <scope>` | Installation scope: global or local |
| `--expert` | Enable expert analysis feature |
| `--no-expert` | Disable expert analysis feature |
| `--quiet, -q` | Suppress non-essential output |
| `--verbose, -v` | Enable detailed output |

#### Examples

```bash
# Interactive mode (recommended for first-time users)
uvx --from optix-mcp-server optix install

# Non-interactive: Install for Claude Code only, global scope
uvx --from optix-mcp-server optix install --agents claude --scope global

# Enable expert analysis during installation
uvx --from optix-mcp-server optix install --expert
```

#### Verify Installation

```bash
# Check configuration status
uvx --from optix-mcp-server optix health
```

### Option 2: Development Setup

For contributors or those who need to modify the source code.

#### Prerequisites

- Python 3.10 or higher (3.13.11 recommended via pyenv)
- pip or uv package manager
- Git

#### Clone and Setup Environment

```bash
# Clone repository
git clone <repository-url>
cd optix-mcp-server

# Setup Python version (if using pyenv)
pyenv install 3.13.11
pyenv local 3.13.11

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### Install Dependencies

```bash
# Install package with dev dependencies
pip install -e ".[dev]"

# Or with uv (recommended)
uv pip install -e ".[dev]"
```

#### Configure Environment (Optional)

For features requiring API keys (like `security_audit` tool with LLM expert analysis):

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Example:
# OPENAI_API_KEY=sk-...
```

The server automatically loads variables from `.env` file using `python-dotenv`.

#### Start Server

```bash
# Start with default settings (stdio transport)
python server.py

# Start with custom settings via environment variables
export SERVER_NAME=my-server
export LOG_LEVEL=DEBUG
python server.py
```

#### Quick Verification (Development)

Run this to verify your development setup is correct:

```bash
# 1. Check Python
python --version

# 2. Check dependencies
python -c "from mcp.server.fastmcp import FastMCP; print('MCP OK')"

# 3. Check tools
python -c "import server; from tools import get_available_tools; print(get_available_tools())"

# 4. Run tests
pytest tests/ -v --tb=short
```

Expected output: All tests pass, `health_check` in available tools list.

## Environment Variables

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_NAME` | optix-mcp-server | Server name for MCP |
| `OPTIX_LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARN) |
| `LOG_LEVEL` | INFO | Fallback logging level if OPTIX_LOG_LEVEL not set |
| `TRANSPORT` | stdio | Transport type (stdio, sse, http) |
| `DISABLED_TOOLS` | (empty) | Comma-separated list of tools to disable |

### API Keys (Optional)

Required for specific features like LLM expert analysis in audit tools (`security_audit`, `devops_audit`, `a11y_audit`, `principal_audit`):

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models |

### Expert Analysis Configuration

Optional settings for LLM-based expert validation of audit findings:

| Variable | Default | Description |
|----------|---------|-------------|
| `EXPERT_ANALYSIS_ENABLED` | false | Enable expert LLM analysis of audit findings |
| `EXPERT_ANALYSIS_TIMEOUT` | 30 | Timeout for expert analysis in seconds |
| `EXPERT_ANALYSIS_MAX_FINDINGS` | 50 | Maximum number of findings to analyze |

**Note**: Expert analysis requires `EXPERT_ANALYSIS_ENABLED=true` and a valid `OPENAI_API_KEY`. The expert analysis feature works with all audit tools (`security_audit`, `devops_audit`, `a11y_audit`, `principal_audit`) to provide LLM-validated assessments of findings, identify additional concerns, and prioritize remediation efforts.

**Configuration via `.env` file** (recommended):
1. Copy `.env.example` to `.env`
2. Add your API keys
3. The server automatically loads `.env` using `python-dotenv`

## Logging Configuration

### Setting Log Level

Control logging verbosity via the `OPTIX_LOG_LEVEL` environment variable:

```bash
# In .env file or shell
export OPTIX_LOG_LEVEL=DEBUG  # Most verbose - detailed execution info
export OPTIX_LOG_LEVEL=INFO   # Default - summary info
export OPTIX_LOG_LEVEL=WARN   # Warnings only
```

### Log Output

Logs are written to:
- **File**: `logs/optix.log` (for real-time monitoring)
- **Stderr**: Always enabled for immediate feedback

Log format:
```
2026-01-18 10:30:45 - INFO - [security_audit] Step 1 completed: 3 findings
```

### Real-Time Log Monitoring

Monitor logs in real-time while the server is running:

```bash
# All logs from all tools
./watch-logs.sh all

# Filter by specific tool
./watch-logs.sh security  # security_audit only
./watch-logs.sh a11y      # a11y_audit only
./watch-logs.sh devops    # devops_audit only
./watch-logs.sh health    # health_check only
```

## Development Workflow

### Running Tests

> **Note**: Ensure the virtual environment is activated before running tests.
> If you see `ModuleNotFoundError: No module named 'mcp'`, run `source .venv/bin/activate` first.

```bash
# Activate venv (if not already active)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Full test suite
pytest tests/ -v

# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/tools/test_health_check.py -v
```

### Adding a New Tool

Tools in optix-mcp-server are MCP-agnostic, meaning they can be tested independently without MCP context.

1. **Create tool directory**:
   ```
   tools/
   └── my_tool/
       ├── __init__.py
       ├── core.py      # Business logic (no MCP imports)
       └── spec.md      # Documentation
   ```

2. **Implement in `core.py`** (no MCP imports):
   ```python
   def my_tool_impl(param: str) -> dict:
       """Pure business logic."""
       return {"result": param.upper()}
   ```

3. **Register in `server.py`**:
   ```python
   from tools.my_tool.core import my_tool_impl
   from tools import register_tool

   @mcp.tool()
   def my_tool(param: str) -> str:
       return json.dumps(my_tool_impl(param))

   register_tool("my_tool", impl=my_tool_impl, description="My tool description")
   ```

4. **Add unit test** in `tests/unit/tools/test_my_tool.py`:
   ```python
   from tools.my_tool.core import my_tool_impl

   def test_my_tool_impl():
       result = my_tool_impl("hello")
       assert result["result"] == "HELLO"
   ```

## Troubleshooting

### Server won't start

1. **Check Python version**: `python --version` (needs 3.10+)
2. **Verify dependencies**: `pip list | grep mcp`
3. **Check configuration**:
   ```bash
   python -c "from config.defaults import ServerConfiguration; print(ServerConfiguration.from_env())"
   ```

### Tests failing

1. **Ensure dev dependencies installed**: `pip install -e ".[dev]"` or `uv pip install -e ".[dev]"`
2. **Check pytest version**: `pytest --version` (needs 7.0+)
3. **Run single test for details**: `pytest tests/unit/tools/test_health_check.py -v`

### Import errors

**ModuleNotFoundError: No module named 'mcp'**
- Virtual environment not activated. Run: `source .venv/bin/activate`
- Dependencies not installed. Run: `pip install -e ".[dev]"`

**Other import errors**
1. **Ensure package is installed in editable mode**: `pip install -e .`
2. **Check PYTHONPATH** includes project root
3. **Verify `__init__.py` files** exist in all packages

### Configuration errors

If you see "server_name must be alphanumeric with hyphens allowed":
- Ensure `SERVER_NAME` environment variable uses only letters, numbers, and hyphens
- Example valid names: `my-server`, `optix-mcp-server`, `server123`

## Project Structure

```
optix-mcp-server/
├── server.py              # MCP server entry point
├── config/
│   └── defaults.py        # Configuration classes
├── tools/
│   ├── __init__.py        # Tool registry
│   ├── base.py            # Tool Protocol interface
│   └── health_check/      # health_check tool
│       ├── __init__.py
│       ├── core.py        # Business logic (MCP-agnostic)
│       └── spec.md        # Tool specification
└── tests/
    ├── integration/       # Integration tests
    │   ├── conftest.py    # Test fixtures
    │   └── test_server_startup.py
    └── unit/              # Unit tests
        └── tools/
            ├── test_health_check.py
            └── test_registry.py
```
