"""
Core data models for poster design.

This module defines the fundamental data structures used throughout
the poster design library. All models use Pydantic for validation
and serialization.

These models are completely independent of MCP and can be used
standalone in the core SDK.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from enum import Enum


class Position(BaseModel):
    """Represents a 2D position with x and y coordinates.

    Attributes:
        x: X coordinate (can be negative for off-canvas positioning)
        y: Y coordinate (can be negative for off-canvas positioning)
    """

    x: float
    y: float


class Size(BaseModel):
    """Represents the size of an element or canvas.

    Attributes:
        width: Width in pixels (must be positive)
        height: Height in pixels (must be positive)
    """

    width: float
    height: float


class Color(BaseModel):
    """Represents a color with hex value and optional RGBA.

    Attributes:
        hex: Hexadecimal color string (e.g., "#FF0000")
        rgba: Optional RGBA tuple as (r, g, b, a)
    """

    hex: str
    rgba: Optional[tuple[int, int, int, float]] = None

    @field_validator("hex")
    @classmethod
    def validate_hex_format(cls, v: str) -> str:
        """Validate hex color format."""
        if not v.startswith("#"):
            raise ValueError("Hex color must start with #")
        if len(v) not in (4, 7):  # #RGB or #RRGGBB
            raise ValueError("Hex color must be 4 or 7 characters long")
        return v


class ElementType(str, Enum):
    """Enumeration of supported element types."""

    TEXT = "text"
    IMAGE = "image"
    SHAPE = "shape"


class Element(BaseModel):
    """Base model for all design elements.

    Elements are the building blocks of a poster design. Each element
    has a position, size, and various properties.

    Attributes:
        id: Unique identifier for the element
        type: The type of element (text, image, or shape)
        position: Position of the element on the canvas
        size: Dimensions of the element
        z_index: Rendering order (higher values render on top)
        opacity: Transparency value (0.0 = transparent, 1.0 = opaque)
        rotation: Rotation angle in degrees
        properties: Additional type-specific properties
    """

    id: str
    type: ElementType
    position: Position
    size: Size
    z_index: int = 0
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)
    rotation: float = 0.0
    properties: Dict[str, Any] = Field(default_factory=dict)


class CanvasState(BaseModel):
    """Immutable snapshot of canvas state.

    CanvasState represents a complete snapshot of a canvas at a point
    in time. It can be used for checkpoints, undo/redo, and state
    serialization.

    Attributes:
        id: Unique identifier for the canvas
        width: Canvas width in pixels
        height: Canvas height in pixels
        background: Background configuration dict
        elements: List of all elements on the canvas
        metadata: Additional canvas metadata
    """

    id: str
    width: int
    height: int
    background: Dict[str, Any]
    elements: list[Element] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}  # Make immutable for snapshots
