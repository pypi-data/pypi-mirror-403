# Tool Specification: health_check

**Tool Name**: `health_check`
**Version**: 1.0.0
**Module**: `tools/health_check/`

## Overview

The health_check tool reports the health status of the MCP server, including server information, uptime, and list of available tools.

## Interface

### Input Parameters

None required.

### Output Schema

```json
{
  "type": "object",
  "required": ["status", "server_name", "version", "tools_available"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["healthy", "degraded", "unhealthy"],
      "description": "Server health status"
    },
    "server_name": {
      "type": "string",
      "description": "Name of the MCP server"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Server version (semver format)"
    },
    "uptime_seconds": {
      "type": "number",
      "minimum": 0,
      "description": "Time since server started in seconds"
    },
    "tools_available": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of available tool names"
    }
  }
}
```

### Example Response

```json
{
  "status": "healthy",
  "server_name": "optix-mcp-server",
  "version": "0.1.0",
  "uptime_seconds": 123.45,
  "tools_available": ["health_check"]
}
```

## Status Determination

| Condition | Status |
|-----------|--------|
| At least one tool available | `healthy` |
| No tools available (all disabled) | `degraded` |
| Server error state | `unhealthy` |

## Implementation

### Core Function

The business logic is in `core.py`:

```python
def health_check_impl(
    server_name: str,
    version: str,
    uptime_seconds: float,
    available_tools: list[str],
    disabled_tools: Optional[list[str]] = None,
) -> dict:
```

This function:
- Has **no MCP dependencies**
- Can be called directly for testing
- Returns a dictionary (not JSON string)

### MCP Registration

The MCP wrapper in `server.py`:
- Collects runtime data (uptime, config, tools)
- Calls `health_check_impl()` with the data
- Serializes result to JSON string

## Testing

### Unit Tests

Located in `tests/unit/tools/test_health_check.py`:
- `test_health_check_impl_direct_call` - Function callable without MCP
- `test_health_check_impl_returns_expected_structure` - Correct output format
- `test_health_check_impl_degraded_when_no_tools` - Status logic
- `test_health_check_impl_filters_disabled_tools` - Disabled tool filtering

### Integration Tests

Located in `tests/integration/test_server_startup.py`:
- `test_health_check_returns_valid_response` - End-to-end validation

## Error Handling

This tool does not raise exceptions under normal operation. If the server is in an error state, the `status` field will be `unhealthy`.

## Changelog

- **1.0.0** (2026-01-08): Initial implementation with MCP-agnostic architecture
