"""
Core poster design modules.

This package contains the core SDK which is completely independent
of MCP and can be used standalone.
"""

from poster_design.core.canvas import Canvas
from poster_design.core.elements import (
    Element,
    TextElement,
    ImageElement,
    ShapeElement,
)

# These will be implemented in later tasks
LayoutManager = None
StyleSystem = None
TemplateManager = None
AssetManager = None

__all__ = [
    "Canvas",
    "TextElement",
    "ImageElement",
    "ShapeElement",
    "Element",
    "LayoutManager",
    "StyleSystem",
    "TemplateManager",
    "AssetManager",
]
