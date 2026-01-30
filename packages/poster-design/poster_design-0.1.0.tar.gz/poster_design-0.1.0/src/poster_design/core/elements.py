"""
Element classes for poster design.

This module defines the base Element class and specific element types
like TextElement, ImageElement, and ShapeElement.
"""

import uuid
from typing import Optional, Any, Dict
from dataclasses import dataclass, field

from poster_design.core.models import ElementType, Position, Size


class Element:
    """Base class for all design elements.

    Elements are the building blocks of a poster design. Each element
    has a unique ID, position, size, and various properties.

    Attributes:
        element_type: The type of element
        position: Position of the element on the canvas
        size: Dimensions of the element
        z_index: Rendering order (higher values render on top)
        opacity: Transparency value (0.0 = transparent, 1.0 = opaque)
        rotation: Rotation angle in degrees
    """

    def __init__(
        self,
        element_type: ElementType,
        position: tuple[float, float] = (0, 0),
        size: Optional[tuple[float, float]] = None,
        z_index: int = 0,
        opacity: float = 1.0,
        rotation: float = 0.0,
    ):
        self._id = f"{element_type.value}_{uuid.uuid4().hex[:8]}"
        self.type = element_type
        self.position = Position(x=position[0], y=position[1])
        if size:
            self.size = Size(width=size[0], height=size[1])
        else:
            self.size = Size(width=100, height=100)
        self.z_index = z_index
        self.opacity = opacity
        self.rotation = rotation

    @property
    def id(self) -> str:
        """Get the unique element ID."""
        return self._id


class TextElement(Element):
    """Text element for adding text to the canvas.

    Attributes:
        text: The text content
        font_family: Font family name
        font_size: Font size in pixels
        color: Text color as hex string
        align: Text alignment (left, center, right)
        bold: Whether text is bold
        italic: Whether text is italic
        line_height: Line height multiplier
    """

    def __init__(
        self,
        text: str,
        font_family: str = "Arial",
        font_size: int = 24,
        color: str = "#000000",
        align: str = "left",
        bold: bool = False,
        italic: bool = False,
        line_height: float = 1.2,
        **kwargs,
    ):
        super().__init__(element_type=ElementType.TEXT, **kwargs)
        self.text = text
        self.font_family = font_family
        self.font_size = font_size
        self.color = color
        self.align = align
        self.bold = bold
        self.italic = italic
        self.line_height = line_height
        self.shadow = None
        self.stroke = None
        self.gradient = None

    def add_shadow(self, color: str, blur: int, offset: tuple[int, int]) -> None:
        """Add a shadow effect to the text.

        Args:
            color: Shadow color as hex string
            blur: Blur radius in pixels
            offset: Shadow offset as (x, y) tuple
        """
        self.shadow = {"color": color, "blur": blur, "offset": offset}

    def add_stroke(self, color: str, width: int) -> None:
        """Add a stroke (outline) to the text.

        Args:
            color: Stroke color as hex string
            width: Stroke width in pixels
        """
        self.stroke = {"color": color, "width": width}

    def set_gradient(self, colors: list[str]) -> None:
        """Apply a gradient to the text.

        Args:
            colors: List of hex color strings for the gradient
        """
        self.gradient = colors


class ImageElement(Element):
    """Image element for adding images to the canvas.

    Attributes:
        source: Image source (local path or URL)
        fit: How to fit the image (cover, contain, fill)
    """

    def __init__(
        self,
        source: str,
        fit: str = "cover",
        **kwargs,
    ):
        # Determine size from kwargs or defaults
        if "size" not in kwargs:
            kwargs["size"] = (200, 200)
        super().__init__(element_type=ElementType.IMAGE, **kwargs)
        self.source = source
        self.fit = fit
        self.filters = []
        self.clip_shape = None
        self.border = None

    def apply_filter(self, filter_obj: Any) -> None:
        """Apply a filter to the image.

        Args:
            filter_obj: Filter object (Blur, Brightness, etc.)
        """
        self.filters.append(filter_obj)

    def clip_to_shape(self, shape: str) -> None:
        """Clip the image to a shape.

        Args:
            shape: Shape name (circle, rectangle, etc.)
        """
        self.clip_shape = shape

    def add_border(self, width: int, color: str) -> None:
        """Add a border to the image.

        Args:
            width: Border width in pixels
            color: Border color as hex string
        """
        self.border = {"width": width, "color": color}


class ShapeElement(Element):
    """Shape element for adding shapes to the canvas.

    Attributes:
        shape_type: Type of shape (rectangle, circle, triangle, polygon)
        fill_color: Fill color as hex string
        border_color: Border color as hex string
        border_width: Border width in pixels
        corner_radius: Corner radius for rounded rectangles
        polygon_points: Points for polygon shapes
    """

    def __init__(
        self,
        shape_type: str,
        fill_color: str = "#000000",
        border_color: Optional[str] = None,
        border_width: int = 0,
        corner_radius: int = 0,
        polygon_points: Optional[list[tuple[float, float]]] = None,
        **kwargs,
    ):
        # Determine size from kwargs or defaults
        if "size" not in kwargs:
            kwargs["size"] = (100, 100)
        super().__init__(element_type=ElementType.SHAPE, **kwargs)
        self.shape_type = shape_type
        self.fill_color = fill_color
        self.border_color = border_color
        self.border_width = border_width
        self.corner_radius = corner_radius
        self.polygon_points = polygon_points
