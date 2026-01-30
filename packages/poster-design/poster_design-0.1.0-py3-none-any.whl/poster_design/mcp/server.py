"""
MCP server for poster design.

This module provides the MCP server implementation that exposes
poster design functionality as MCP tools.
"""

import asyncio
import json
import sys
from typing import Any, Optional

# MCP package is optional - only required when using MCP integration
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None

from poster_design.mcp.handlers import ToolHandlers


class PosterDesignServer:
    """MCP server for poster design functionality."""

    def __init__(self):
        """Initialize the MCP server."""
        if not MCP_AVAILABLE:
            raise ImportError(
                "MCP package is not installed. "
                "Install with: pip install poster-design[mcp]"
            )

        self.server = Server("poster-design")
        self.handlers = ToolHandlers()
        self._setup_tools()

    def _setup_tools(self):
        """Register all MCP tools."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="create_canvas",
                    description="Create a new poster canvas with specified dimensions or preset",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier for multi-user scenarios"
                            },
                            "width": {
                                "type": "number",
                                "description": "Canvas width in pixels"
                            },
                            "height": {
                                "type": "number",
                                "description": "Canvas height in pixels"
                            },
                            "preset": {
                                "type": "string",
                                "description": "Preset name (instagram_post, instagram_story, etc.)",
                                "enum": ["instagram_post", "instagram_story", "facebook_post",
                                        "wechat_cover", "a4_portrait", "a4_landscape"]
                            },
                            "dpi": {
                                "type": "number",
                                "description": "DPI setting",
                                "default": 72
                            }
                        }
                    }
                ),
                Tool(
                    name="set_background",
                    description="Set the background of a canvas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "canvas_id": {"type": "string"},
                            "background_type": {
                                "type": "string",
                                "enum": ["color", "gradient", "image", "preset"]
                            },
                            "color": {
                                "type": "string",
                                "description": "Solid color as hex string"
                            },
                            "gradient": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of colors for gradient"
                            },
                            "image": {
                                "type": "string",
                                "description": "Path to background image"
                            },
                            "preset": {
                                "type": "string",
                                "description": "Preset name for built-in backgrounds (e.g., 'paper_texture')"
                            }
                        },
                        "required": ["session_id", "canvas_id", "background_type"]
                    }
                ),
                Tool(
                    name="add_text",
                    description="Add a text element to the canvas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "canvas_id": {"type": "string"},
                            "text": {"type": "string"},
                            "font_size": {"type": "number", "default": 24},
                            "color": {"type": "string", "default": "#000000"},
                            "font_family": {"type": "string", "default": "Arial"},
                            "bold": {"type": "boolean", "default": False},
                            "italic": {"type": "boolean", "default": False},
                            "position": {
                                "oneOf": [
                                    {"type": "string",
                                     "enum": ["center", "top-center", "bottom-center",
                                             "left-center", "right-center",
                                             "top-left", "top-right",
                                             "bottom-left", "bottom-right"]},
                                    {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2}
                                ]
                            },
                            "offset_x": {"type": "number", "default": 0},
                            "offset_y": {"type": "number", "default": 0}
                        },
                        "required": ["session_id", "canvas_id", "text"]
                    }
                ),
                Tool(
                    name="add_image",
                    description="Add an image element to the canvas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "canvas_id": {"type": "string"},
                            "source": {"type": "string"},
                            "width": {"type": "number"},
                            "height": {"type": "number"},
                            "fit": {
                                "type": "string",
                                "enum": ["cover", "contain", "fill"],
                                "default": "cover"
                            },
                            "position": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2}
                                ]
                            },
                            "offset_x": {"type": "number", "default": 0},
                            "offset_y": {"type": "number", "default": 0}
                        },
                        "required": ["session_id", "canvas_id", "source"]
                    }
                ),
                Tool(
                    name="add_shape",
                    description="Add a shape element to the canvas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "canvas_id": {"type": "string"},
                            "shape_type": {
                                "type": "string",
                                "enum": ["rectangle", "circle", "triangle", "polygon"]
                            },
                            "width": {"type": "number", "default": 100},
                            "height": {"type": "number", "default": 100},
                            "fill_color": {"type": "string", "default": "#000000"},
                            "border_color": {"type": "string", "default": "#000000"},
                            "border_width": {"type": "number", "default": 0},
                            "position": {"type": "string"},
                            "offset_x": {"type": "number", "default": 0},
                            "offset_y": {"type": "number", "default": 0}
                        },
                        "required": ["session_id", "canvas_id", "shape_type"]
                    }
                ),
                Tool(
                    name="remove_element",
                    description="Remove an element from the canvas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "canvas_id": {"type": "string"},
                            "element_id": {"type": "string"}
                        },
                        "required": ["session_id", "canvas_id", "element_id"]
                    }
                ),
                Tool(
                    name="align_elements",
                    description="Align elements on the canvas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "canvas_id": {"type": "string"},
                            "alignment": {
                                "type": "string",
                                "enum": ["left", "center", "right", "top", "middle", "bottom"]
                            },
                            "element_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of element IDs (null for all elements)"
                            }
                        },
                        "required": ["session_id", "canvas_id", "alignment"]
                    }
                ),
                Tool(
                    name="distribute_elements",
                    description="Distribute elements evenly on the canvas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "canvas_id": {"type": "string"},
                            "direction": {
                                "type": "string",
                                "enum": ["horizontal", "vertical"]
                            },
                            "spacing": {"type": "number", "default": 0},
                            "element_ids": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["session_id", "canvas_id", "direction"]
                    }
                ),
                Tool(
                    name="export_poster",
                    description="Export the canvas to a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "canvas_id": {"type": "string"},
                            "output_path": {"type": "string"},
                            "format": {
                                "type": "string",
                                "enum": ["png", "jpg", "pdf"],
                                "default": "png"
                            },
                            "dpi": {"type": "number"},
                            "quality": {
                                "type": "number",
                                "description": "Quality for JPG (1-100)",
                                "minimum": 1,
                                "maximum": 100
                            }
                        },
                        "required": ["session_id", "canvas_id", "output_path"]
                    }
                ),
                Tool(
                    name="get_canvas_info",
                    description="Get information about a canvas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "canvas_id": {"type": "string"}
                        },
                        "required": ["session_id", "canvas_id"]
                    }
                ),
                Tool(
                    name="list_canvases",
                    description="List all canvases in a session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"}
                        },
                        "required": ["session_id"]
                    }
                ),
                Tool(
                    name="delete_canvas",
                    description="Delete a canvas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "canvas_id": {"type": "string"}
                        },
                        "required": ["session_id", "canvas_id"]
                    }
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls."""
            try:
                # Call the appropriate handler
                handler = getattr(self.handlers, name)
                result = handler(**arguments)

                # Format response
                response_text = json.dumps({
                    "tool": name,
                    "result": result
                }, indent=2)

                return [TextContent(type="text", text=response_text)]

            except Exception as e:
                error_response = json.dumps({
                    "tool": name,
                    "error": str(e)
                }, indent=2)
                return [TextContent(type="text", text=error_response)]

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point for the MCP server."""
    if not MCP_AVAILABLE:
        print(
            "Error: MCP package is not installed.\n"
            "Install with: pip install poster-design[mcp]",
            file=sys.stderr
        )
        sys.exit(1)

    server = PosterDesignServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
