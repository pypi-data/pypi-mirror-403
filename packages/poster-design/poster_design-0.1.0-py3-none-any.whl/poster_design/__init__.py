"""
Poster Design Library

A powerful poster design library with optional MCP integration for LLM agents.

This library provides two modes of operation:
1. Python Script Mode: Direct import and use in Python scripts
2. MCP Agent Mode: Natural language-driven design through MCP tools

Core API (always available):
    Canvas: Main canvas class for poster creation
    TextElement: Text element with styling options
    ImageElement: Image element with filters and effects
    ShapeElement: Shape elements (rectangle, circle, triangle)

Example:
    >>> from poster_design import Canvas, TextElement
    >>> canvas = Canvas(preset="instagram_post")
    >>> canvas.set_background("#FF6B6B")
    >>> title = TextElement(text="Hello", font_size=72)
    >>> canvas.add(title, position="center")
    >>> canvas.export("output.png")
"""

# Version
from poster_design.__version__ import __version__

# Core API exports
from poster_design.core.canvas import Canvas
from poster_design.core.elements import TextElement, ImageElement, ShapeElement, Element

# Preset backgrounds
try:
    from poster_design.core.backgrounds import list_preset_backgrounds
except ImportError:
    list_preset_backgrounds = None

# These will be implemented in later phases
try:
    from poster_design.core.layout import LayoutManager
except ImportError:
    LayoutManager = None

try:
    from poster_design.core.styles import StyleSystem
except ImportError:
    StyleSystem = None

__all__ = [
    "__version__",
    "Canvas",
    "TextElement",
    "ImageElement",
    "ShapeElement",
    "Element",
    "list_preset_backgrounds",
    "LayoutManager",
    "StyleSystem",
]
