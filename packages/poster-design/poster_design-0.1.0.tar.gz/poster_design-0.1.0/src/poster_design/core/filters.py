"""
Image filter classes for poster design.

This module provides filter classes that can be applied to ImageElement
objects for various image effects.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Blur:
    """Blur filter for images.

    Attributes:
        radius: Blur radius in pixels
    """

    radius: int

    def __post_init__(self):
        """Validate blur radius."""
        if self.radius < 0:
            raise ValueError("Blur radius must be non-negative")
        if self.radius > 100:
            raise ValueError("Blur radius must not exceed 100")


@dataclass
class Brightness:
    """Brightness adjustment filter.

    Attributes:
        factor: Brightness multiplier (0.0 = black, 1.0 = original, 2.0 = twice as bright)
    """

    factor: float

    def __post_init__(self):
        """Validate brightness factor."""
        if not 0.0 <= self.factor <= 2.0:
            raise ValueError("Brightness factor must be between 0.0 and 2.0")


@dataclass
class Contrast:
    """Contrast adjustment filter.

    Attributes:
        factor: Contrast multiplier (0.0 = no contrast, 1.0 = original, 2.0 = high contrast)
    """

    factor: float

    def __post_init__(self):
        """Validate contrast factor."""
        if not 0.0 <= self.factor <= 2.0:
            raise ValueError("Contrast factor must be between 0.0 and 2.0")


@dataclass
class Grayscale:
    """Grayscale filter - converts image to black and white.

    This filter has no parameters.
    """

    pass


@dataclass
class Saturation:
    """Saturation adjustment filter.

    Attributes:
        factor: Saturation multiplier (0.0 = grayscale, 1.0 = original, 2.0 = oversaturated)
    """

    factor: float

    def __post_init__(self):
        """Validate saturation factor."""
        if not 0.0 <= self.factor <= 2.0:
            raise ValueError("Saturation factor must be between 0.0 and 2.0")


@dataclass
class Sepia:
    """Sepia tone filter - gives images a warm, vintage look.

    Attributes:
        intensity: Sepia intensity from 0 to 100
    """

    intensity: int = 80

    def __post_init__(self):
        """Validate sepia intensity."""
        if not 0 <= self.intensity <= 100:
            raise ValueError("Sepia intensity must be between 0 and 100")


@dataclass
class Invert:
    """Invert filter - inverts all colors.

    This filter has no parameters.
    """

    pass


@dataclass
class Sharpen:
    """Sharpen filter for enhancing edges.

    Attributes:
        factor: Sharpen intensity (0.0 = no effect, 1.0 = normal, 2.0 = strong)
    """

    factor: float = 1.0

    def __post_init__(self):
        """Validate sharpen factor."""
        if not 0.0 <= self.factor <= 2.0:
            raise ValueError("Sharpen factor must be between 0.0 and 2.0")
