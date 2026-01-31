# MCPEasy 🚀

**The simplest way to use Model Context Protocol in Python**

A high-level, easy-to-use wrapper around the official [Anthropic MCP SDK](https://github.com/modelcontextprotocol/python-sdk).

[![PyPI version](https://badge.fury.io/py/mcpeasy.svg)](https://badge.fury.io/py/mcpeasy)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why MCPEasy?

The official MCP SDK is powerful but low-level. **MCPEasy** makes it dead simple to:

- ✅ Connect to any MCP server with one line of code
- ✅ Call tools without worrying about async complexity
- ✅ Handle subprocess management automatically
- ✅ Get started in seconds, not hours

## Installation

```bash
pip install mcpeasy
```

## Quick Start

```python
import asyncio
from mcpeasy import connect

async def main():
    # Connect to any MCP server
    client = connect("python -m my_mcp_server")
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {[t.name for t in tools.tools]}")
    
    # Call a tool
    response = await client.call("my_tool", {"arg": "value"})
    
    if response.success:
        print(response.content)
    else:
        print(f"Error: {response.error}")
    
    # Clean up
    await client.close()

asyncio.run(main())
```

**That's it!** 🎉

## Comparison: Official SDK vs MCPEasy

### Official MCP SDK (Low-level)

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def use_mcp():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "my_mcp_server"],
        env=os.environ.copy()
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("tool_name", {})
            # ... handle result
```

### MCPEasy (High-level) ✨

```python
from mcpeasy import connect

client = connect("python -m my_mcp_server")
result = await client.call("tool_name", {})
```

**90% less code!**

## Features

- 🎯 **Simple API** - Just `connect()` and `call()`
- 🔄 **Async/Await** - Built on Python's asyncio
- 🛠️ **Tool Discovery** - List all available tools
- 🐛 **Error Handling** - Clear error messages
- 📦 **Process Management** - Automatic subprocess handling
- 🔌 **Works with ANY MCP server** - SQLite, web search, custom servers

## Examples

### Example 1: SQLite MCP Server

```python
from mcpeasy import connect

# Connect to SQLite MCP server
client = connect("python -m mcp_servers.sqlite_server")

# Get database statistics
response = await client.call("get_memory_stats", {})
print(response.content)

# Run SQL query
response = await client.call("query_memories", {
    "sql": "SELECT * FROM memories WHERE category = 'personal'"
})
print(response.content)

await client.close()
```

### Example 2: Web Search MCP Server

```python
from mcpeasy import connect

# Connect to DuckDuckGo MCP server
client = connect("python -m mcp_servers.duckduckgo_server")

# Search the web
response = await client.call("web_search", {
    "query": "Python programming",
    "count": 5
})
print(response.content)

await client.close()
```

### Example 3: Custom MCP Server

```python
from mcpeasy import connect

# Connect to your custom server
client = connect("python -m my_custom_server")

# List what it can do
tools = await client.list_tools()
for tool in tools.tools:
    print(f"📌 {tool.name}: {tool.description}")

# Call your custom tool
response = await client.call("custom_tool", {"param": "value"})

await client.close()
```

## API Reference

### `connect(command: str) -> MCPClient`

Create an MCP client.

**Parameters:**
- `command` (str): Command to start the MCP server (e.g., `"python -m my_server"`)

**Returns:**
- `MCPClient`: Ready-to-use client instance

### `MCPClient.call(tool: str, args: dict) -> MCPResponse`

Call a tool on the MCP server.

**Parameters:**
- `tool` (str): Name of the tool to call
- `args` (dict): Arguments to pass to the tool

**Returns:**
- `MCPResponse`: Object with `.success`, `.content`, and `.error` attributes

### `MCPClient.list_tools() -> ListToolsResult`

List all available tools.

**Returns:**
- `ListToolsResult`: Object with `.tools` list

### `MCPClient.close() -> None`

Close the client and clean up resources.

## Requirements

- Python 3.10+
- Official MCP SDK (`mcp` package)

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/mcpeasy.git
cd mcpeasy

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Build package
python -m build
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on top of the official [Anthropic MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- Inspired by the need for simpler MCP tooling

## Links

- **Documentation**: https://github.com/yourusername/mcpeasy
- **PyPI**: https://pypi.org/project/mcpeasy/
- **Issues**: https://github.com/yourusername/mcpeasy/issues
- **MCP Specification**: https://modelcontextprotocol.io/

## Star History

If you find this useful, please ⭐ star the repository!

---

**Made with ❤️ for the MCP community**
