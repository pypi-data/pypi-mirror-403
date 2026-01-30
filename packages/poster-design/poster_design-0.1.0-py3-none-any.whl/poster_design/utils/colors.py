"""
Color manipulation utility functions.

This module provides functions for converting between color formats,
blending colors, and generating gradients.
"""

import re
from typing import List


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string to RGB tuple.

    Args:
        hex_color: Hex color string (e.g., "#FF0000" or "#F00")

    Returns:
        Tuple of (red, green, blue) values (0-255)

    Raises:
        ValueError: If the hex color is invalid
    """
    # Remove # if present
    hex_color = hex_color.lstrip("#")

    # Validate hex format
    if not re.match(r"^[A-Fa-f0-9]{3}$|^[A-Fa-f0-9]{6}$", hex_color):
        raise ValueError(f"Invalid hex color: {hex_color}")

    # Expand short format (#RGB -> #RRGGBB)
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)

    # Convert to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (r, g, b)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color string.

    Args:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)

    Returns:
        Hex color string (e.g., "#FF0000")

    Raises:
        ValueError: If RGB values are out of range
    """
    # Validate ranges
    for val, name in [(r, "red"), (g, "green"), (b, "blue")]:
        if not 0 <= val <= 255:
            raise ValueError(f"{name} value must be between 0 and 255, got {val}")

    return f"#{r:02X}{g:02X}{b:02X}"


def blend_colors(color1: str, color2: str, ratio: float) -> str:
    """Blend two hex colors together.

    Args:
        color1: First hex color
        color2: Second hex color
        ratio: Blend ratio (0.0 = color1, 1.0 = color2)

    Returns:
        Blended hex color string

    Raises:
        ValueError: If colors are invalid
    """
    # Clamp ratio between 0 and 1
    ratio = max(0.0, min(1.0, ratio))

    # Convert to RGB
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)

    # Blend
    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)

    return rgb_to_hex(r, g, b)


def generate_gradient(colors: List[str], steps: int) -> List[str]:
    """Generate a gradient between multiple colors.

    Args:
        colors: List of hex color strings
        steps: Number of color steps in the gradient

    Returns:
        List of hex color strings forming the gradient

    Raises:
        ValueError: If colors list is empty or steps is invalid
    """
    if not colors:
        raise ValueError("Colors list cannot be empty")
    if steps < 1:
        raise ValueError("Steps must be at least 1")
    if len(colors) == 1:
        return [colors[0]] * steps

    # If we have N colors, we need (N-1) segments
    num_segments = len(colors) - 1
    steps_per_segment = max(1, steps // num_segments)

    gradient = []

    for i in range(num_segments):
        # Calculate how many steps for this segment
        if i == num_segments - 1:
            # Last segment gets remaining steps
            segment_steps = steps - len(gradient)
        else:
            segment_steps = steps_per_segment

        # Generate gradient for this segment
        for j in range(segment_steps):
            if segment_steps == 1:
                ratio = 0.5
            else:
                ratio = j / (segment_steps - 1)

            blended = blend_colors(colors[i], colors[i + 1], ratio)
            gradient.append(blended)

    # Ensure we return exactly the requested number of steps
    return gradient[:steps]
