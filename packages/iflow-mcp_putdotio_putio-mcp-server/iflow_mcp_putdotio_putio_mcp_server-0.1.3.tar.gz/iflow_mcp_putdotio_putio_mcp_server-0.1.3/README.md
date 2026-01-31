# putio-mcp-server
MCP server for interacting with put.io

## Features

- List active transfers
- Add new transfers via URL or magnet link
- Cancel existing transfers
- Get browser links for completed transfers

## Prerequisites

- [Claude Desktop](https://modelcontextprotocol.io/quickstart/user)
- Python 3.x
- [uvx](https://docs.astral.sh/uv/getting-started/installation/)
- Put.io account and API token ([guide](https://help.put.io/en/articles/5972538-how-to-get-an-oauth-token-from-put-io))

## Setup

Put following config in your `claude_desktop_config.json`.

Don't forget to replace `<your-putio-api-token>` with your own API token.


```json
{
  "mcpServers": {
    "putio": {
      "command": "uvx",
      "args": [
        "putio-mcp-server"
      ],
      "env": {
        "PUTIO_TOKEN": "<your-putio-api-token>"
      }
    }
  }
}
```
