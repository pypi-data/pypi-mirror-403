"""
MCPEasy - The simplest way to use Model Context Protocol in Python

Easy-to-use wrapper around the official Anthropic MCP SDK.
"""

__version__ = "0.1.0"
__author__ = "Nitish Raj"
__license__ = "MIT"

from .client import MCPClient, connect
from .types import MCPResponse

__all__ = ["MCPClient", "connect", "MCPResponse"]
