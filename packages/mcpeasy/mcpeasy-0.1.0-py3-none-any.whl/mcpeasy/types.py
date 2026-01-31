"""Data types for MCPEasy."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MCPResponse:
    """Response from an MCP tool call.
    
    Attributes:
        success: Whether the tool call succeeded
        content: The response content (text)
        error: Error message if the call failed
    """
    success: bool
    content: str
    error: Optional[str] = None
