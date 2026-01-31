"""
Basic usage example of MCPEasy.

This example shows how to connect to an MCP server and call tools.
"""

import asyncio
from mcpeasy import connect


async def main():
    print("🚀 MCPEasy Basic Usage Example\n")
    
    # Connect to MCP server
    # Replace this with your MCP server command
    client = connect("python -m mcp_servers.sqlite_server")
    print("✅ Connected to MCP server\n")
    
    # List available tools
    print("📋 Available tools:")
    tools = await client.list_tools()
    for tool in tools.tools:
        print(f"   • {tool.name}: {tool.description[:60]}...")
    print()
    
    # Call a tool
    print("🔧 Calling get_memory_stats tool...")
    response = await client.call("get_memory_stats", {})
    
    if response.success:
        print("✅ Success!")
        print(f"\n{response.content}\n")
    else:
        print(f"❌ Error: {response.error}\n")
    
    # Clean up
    await client.close()
    print("👋 Connection closed")


if __name__ == "__main__":
    asyncio.run(main())
