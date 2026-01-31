# MCP Time Server

This is a simple MCP (Model Context Protocol) Server that provides a tool to get the current time with optional timezone support.

## Features

- Provides a `get_current_time` tool to retrieve the current time
- Supports optional timezone parameter
- Returns time in ISO 8601 format
- Handles unknown timezone errors gracefully

## Requirements

- Python 3.7+
- `mcp` Python SDK
- `pytz` library (for timezone support)

## Installation

```bash
pip install mcp-time-server
```

## Usage

1. Run the server:

```bash
mcp-time-server
```

2. The server will start and listen for requests

## Tool Usage

The server provides a single tool called `get_current_time` with the following parameters:

- `timezone` (optional): A string representing the timezone (e.g., "Asia/Shanghai", "America/New_York")

### Example Requests

#### Without timezone:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "callTool",
  "params": {
    "toolCall": {
      "name": "get_current_time",
      "arguments": {}
    }
  }
}
```

#### With timezone:
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "callTool",
  "params": {
    "toolCall": {
      "name": "get_current_time",
      "arguments": {
        "timezone": "Asia/Shanghai"
      }
    }
  }
}
```

### Example Responses

#### Without timezone:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "toolResult": {
      "content": "2024-01-30T12:34:56.789012"
    }
  }
}
```

#### With timezone:
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "result": {
    "toolResult": {
      "content": "2024-01-30T20:34:56.789012+08:00"
    }
  }
}
```

#### Error response (unknown timezone):
```json
{
  "jsonrpc": "2.0",
  "id": "3",
  "result": {
    "toolResult": {
      "content": "Error: Unknown timezone 'Invalid/Timezone'"
    }
  }
}
```

## Configuration

The server runs with default configuration using the streamable-http transport, which is suitable for local development and testing.

For production deployment, you may want to configure additional options such as HTTP transport or authentication.

## License

This project is licensed under the MIT License.
