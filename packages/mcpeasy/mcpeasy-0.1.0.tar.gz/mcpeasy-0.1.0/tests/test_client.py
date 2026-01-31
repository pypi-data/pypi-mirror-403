"""
Tests for MCPEasy client.
"""

import pytest
from mcpeasy import connect, MCPResponse


class TestMCPClient:
    """Test suite for MCPClient."""
    
    def test_connect_returns_client(self):
        """Test that connect() returns a client instance."""
        client = connect("python -m mcp_servers.sqlite_server")
        assert client is not None
        assert hasattr(client, 'call')
        assert hasattr(client, 'list_tools')
        assert hasattr(client, 'close')
    
    def test_command_parsing(self):
        """Test that commands are parsed correctly."""
        client = connect("python -m my_server --arg value")
        assert client.command == ["python", "-m", "my_server", "--arg", "value"]
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing tools from an MCP server."""
        client = connect("python -m mcp_servers.sqlite_server")
        tools = await client.list_tools()
        
        assert tools is not None
        assert hasattr(tools, 'tools')
        assert len(tools.tools) > 0
        
        # Check tool names
        tool_names = [t.name for t in tools.tools]
        assert "get_memory_stats" in tool_names
        assert "search_memories" in tool_names
        assert "query_memories" in tool_names
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_call_tool(self):
        """Test calling a tool."""
        client = connect("python -m mcp_servers.sqlite_server")
        response = await client.call("get_memory_stats", {})
        
        assert isinstance(response, MCPResponse)
        assert response.success is True or response.success is False
        assert isinstance(response.content, str)
        
        if not response.success:
            assert response.error is not None
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_call_with_arguments(self):
        """Test calling a tool with arguments."""
        client = connect("python -m mcp_servers.sqlite_server")
        response = await client.call("search_memories", {
            "keyword": "test",
            "limit": 5
        })
        
        assert isinstance(response, MCPResponse)
        assert isinstance(response.content, str)
        
        await client.close()


class TestMCPResponse:
    """Test suite for MCPResponse."""
    
    def test_response_creation(self):
        """Test creating response objects."""
        response = MCPResponse(success=True, content="Hello")
        assert response.success is True
        assert response.content == "Hello"
        assert response.error is None
    
    def test_response_with_error(self):
        """Test response with error."""
        response = MCPResponse(success=False, content="", error="Something went wrong")
        assert response.success is False
        assert response.content == ""
        assert response.error == "Something went wrong"
