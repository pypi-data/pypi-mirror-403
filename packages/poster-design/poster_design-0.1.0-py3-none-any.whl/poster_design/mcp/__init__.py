"""
MCP (Model Context Protocol) integration for poster design.

This module provides optional MCP server functionality that wraps
the core poster design SDK. The core SDK has NO dependencies on this module.
"""

__version__ = "0.1.0"

from poster_design.mcp.session import SessionManager, Session
from poster_design.mcp.handlers import ToolHandlers

__all__ = [
    "SessionManager",
    "Session",
    "ToolHandlers",
]
