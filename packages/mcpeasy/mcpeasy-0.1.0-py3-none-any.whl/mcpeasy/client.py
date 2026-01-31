"""
MCPEasy Client - Simple wrapper around the official MCP SDK.

This module provides an easy-to-use interface for connecting to and
interacting with MCP (Model Context Protocol) servers.
"""

import asyncio
import os
from typing import Optional, List
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from .types import MCPResponse


class MCPClient:
    """
    Easy-to-use MCP client that works with ANY MCP server.
    
    This client:
    - Spawns MCP servers as separate processes
    - Communicates via stdin/stdout (stdio)
    - Handles all the async complexity for you
    - Provides simple call() and list_tools() methods
    
    Example:
        >>> client = connect("python -m my_mcp_server")
        >>> tools = await client.list_tools()
        >>> response = await client.call("my_tool", {"arg": "value"})
        >>> print(response.content)
        >>> await client.close()
    """

    def __init__(self, command: List[str]):
        """
        Initialize the MCP client.
        
        Args:
            command: Command to start the MCP server as a list
                    e.g., ["python", "-m", "my_mcp_server"]
        """
        self.command = command
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def _start(self):
        """Start the MCP server and initialize the session."""
        if self.session:
            return

        # Prepare parameters
        cmd = self.command[0]
        args = self.command[1:]
        
        # Pass environment to ensure PYTHONPATH is correct
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        # Add current working directory to PYTHONPATH
        cwd = os.getcwd()
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{cwd}:{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = cwd
        
        # Use simple Stdio parameters
        server_params = StdioServerParameters(command=cmd, args=args, env=env)
        
        # Enter the stdio_client context
        read, write = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        
        # Enter the ClientSession context
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        
        # Initialize the session with timeout
        try:
            await asyncio.wait_for(self.session.initialize(), timeout=10.0)
        except asyncio.TimeoutError:
            raise Exception("MCP Session initialization timed out.")

    async def call(self, tool: str, args: dict) -> MCPResponse:
        """
        Call a tool on the MCP server.
        
        Args:
            tool: Name of the tool to call
            args: Arguments to pass to the tool
            
        Returns:
            MCPResponse with success status, content, and optional error
            
        Example:
            >>> response = await client.call("search", {"query": "hello"})
            >>> if response.success:
            ...     print(response.content)
        """
        try:
            await self._start()
            result = await self.session.call_tool(tool, args)

            if result.content:
                # TextContent has 'text' attribute
                return MCPResponse(True, result.content[0].text)
            return MCPResponse(False, "", "Empty response")

        except Exception as e:
            return MCPResponse(False, "", str(e))

    async def list_tools(self):
        """
        List all available tools on the MCP server.
        
        Returns:
            ListToolsResult object from the MCP SDK
            
        Example:
            >>> tools = await client.list_tools()
            >>> for tool in tools.tools:
            ...     print(f"Tool: {tool.name}")
        """
        await self._start()
        return await self.session.list_tools()

    async def close(self):
        """Clean up the client and close all connections."""
        await self.exit_stack.aclose()
        self.session = None


def connect(cmd: str) -> MCPClient:
    """
    Create and return an MCP client (convenience function).
    
    Args:
        cmd: Command string to start the server
             e.g., "python -m my_mcp_server"
             
    Returns:
        MCPClient instance ready to use
        
    Example:
        >>> client = connect("python -m mcp_servers.sqlite_server")
        >>> response = await client.call("query", {"sql": "SELECT * FROM users"})
        >>> await client.close()
    """
    return MCPClient(cmd.split())
