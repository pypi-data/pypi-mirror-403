# mcp-timer

MCP Timer Server - Wait and scheduled timing tools for AI agents.

## Installation

```bash
uvx mcp-timer
```

## Tools

- `wait(seconds)` - Wait for specified seconds
- `wait_until(target_time, next_day_if_passed=False)` - Wait until specified time (HH:MM:SS or YYYY-MM-DD HH:MM:SS)

## MCP Configuration

```json
{
  "mcpServers": {
    "timer": {
      "command": "uvx",
      "args": ["mcp-timer"]
    }
  }
}
```

## License

MIT
