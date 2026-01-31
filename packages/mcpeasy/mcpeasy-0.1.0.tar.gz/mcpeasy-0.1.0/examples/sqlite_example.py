"""
SQLite MCP Server example.

This example shows how to use MCPEasy with a SQLite MCP server.
"""

import asyncio
from mcpeasy import connect


async def main():
    print("🗄️  SQLite MCP Server Example\n")
    
    # Connect to SQLite MCP server
    client = connect("python -m mcp_servers.sqlite_server")
    print("✅ Connected to SQLite MCP server\n")
    
    # Example 1: Get statistics
    print("📊 Example 1: Get Memory Statistics")
    print("-" * 50)
    response = await client.call("get_memory_stats", {})
    if response.success:
        print(response.content)
    print()
    
    # Example 2: Search memories
    print("🔍 Example 2: Search Memories")
    print("-" * 50)
    response = await client.call("search_memories", {
        "keyword": "coding",
        "limit": 5
    })
    if response.success:
        print(response.content)
    print()
    
    # Example 3: Run SQL query
    print("💻 Example 3: SQL Query")
    print("-" * 50)
    response = await client.call("query_memories", {
        "sql": "SELECT COUNT(*) as total FROM memories"
    })
    if response.success:
        print(response.content)
    print()
    
    # Clean up
    await client.close()
    print("👋 Done!")


if __name__ == "__main__":
    asyncio.run(main())
