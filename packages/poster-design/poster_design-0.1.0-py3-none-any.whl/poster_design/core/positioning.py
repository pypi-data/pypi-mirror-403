"""
Position resolution for semantic element placement.

This module provides functions to resolve semantic position names
(like "center", "top-left", etc.) to actual coordinates.
"""

from typing import Tuple


def resolve_position(
    alias: str,
    canvas_size: Tuple[int, int],
    element_size: Tuple[int, int],
) -> Tuple[float, float]:
    """Resolve a semantic position alias to actual coordinates.

    Args:
        alias: Position alias (center, top-left, etc.)
        canvas_size: Canvas size as (width, height)
        element_size: Element size as (width, height)

    Returns:
        Position as (x, y) tuple

    Raises:
        ValueError: If alias is not recognized
    """
    canvas_width, canvas_height = canvas_size
    elem_width, elem_height = element_size

    alias = alias.lower().replace("-", "_").replace(" ", "_")

    if alias == "center":
        x = (canvas_width - elem_width) / 2
        y = (canvas_height - elem_height) / 2
    elif alias == "top_center" or alias == "top-center":
        x = (canvas_width - elem_width) / 2
        y = 0
    elif alias == "bottom_center" or alias == "bottom-center":
        x = (canvas_width - elem_width) / 2
        y = canvas_height - elem_height
    elif alias == "left_center" or alias == "left-center":
        x = 0
        y = (canvas_height - elem_height) / 2
    elif alias == "right_center" or alias == "right-center":
        x = canvas_width - elem_width
        y = (canvas_height - elem_height) / 2
    elif alias == "top_left" or alias == "top-left":
        x = 0
        y = 0
    elif alias == "top_right" or alias == "top-right":
        x = canvas_width - elem_width
        y = 0
    elif alias == "bottom_left" or alias == "bottom-left":
        x = 0
        y = canvas_height - elem_height
    elif alias == "bottom_right" or alias == "bottom-right":
        x = canvas_width - elem_width
        y = canvas_height - elem_height
    else:
        raise ValueError(f"Unknown position alias: {alias}")

    return (x, y)


def calculate_offset(
    position: Tuple[float, float],
    offset_x: float,
    offset_y: float,
) -> Tuple[float, float]:
    """Calculate position with offsets.

    Args:
        position: Base position as (x, y)
        offset_x: X offset
        offset_y: Y offset

    Returns:
        New position as (x, y) tuple
    """
    x, y = position
    return (x + offset_x, y + offset_y)
