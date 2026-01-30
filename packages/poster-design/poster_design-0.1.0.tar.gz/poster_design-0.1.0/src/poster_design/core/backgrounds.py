"""
Preset background images for poster design.

This module provides a registry of built-in background images
that users can reference by name.
"""

from typing import Dict, Optional
from pathlib import Path

# Preset background registry
# Maps preset names to relative paths within the package
PRESET_BACKGROUNDS: Dict[str, str] = {
    # Blue series
    "blue_1": "assets/backgrounds/blue_1.jpeg",
    "blue_2": "assets/backgrounds/blue_2.jpeg",
    "blue_3": "assets/backgrounds/blue_3.jpeg",
    "blue_4": "assets/backgrounds/blue_4.jpeg",
    "blue_5": "assets/backgrounds/blue_5.jpeg",
    "blue_6": "assets/backgrounds/blue_6.jpeg",
    "blue_7": "assets/backgrounds/blue_7.jpeg",
    "blue_8": "assets/backgrounds/blue_8.jpeg",
    # Colorful series
    "colorful_1": "assets/backgrounds/colorful_1.jpeg",
    "colorful_2": "assets/backgrounds/colorful_2.jpeg",
    "colorful_3": "assets/backgrounds/colorful_3.jpeg",
    "colorful_4": "assets/backgrounds/colorful_4.jpeg",
    "colorful_5": "assets/backgrounds/colorful_5.jpeg",
    # Dark series
    "dark_1": "assets/backgrounds/dark_1.jpeg",
    "dark_blue_1": "assets/backgrounds/dark_blue_1.jpeg",
    "dark_green_1": "assets/backgrounds/dark_green_1.jpeg",
    "dark_green_2": "assets/backgrounds/dark_green_2.jpeg",
    # Green series
    "green_1": "assets/backgrounds/green_1.jpg",
    "green_2": "assets/backgrounds/green_2.jpeg",
    "green_3": "assets/backgrounds/green_3.jpeg",
    "green_4": "assets/backgrounds/green_4.jpeg",
    "green_5": "assets/backgrounds/green_5.jpeg",
    "green_6": "assets/backgrounds/green_6.jpeg",
    "green_7": "assets/backgrounds/green_7.jpeg",
    "green_8": "assets/backgrounds/green_8.jpeg",
    # Orange series
    "orange_1": "assets/backgrounds/orange_1.jpeg",
    # Pink series
    "pink_1": "assets/backgrounds/pink_1.jpeg",
    "pink_2": "assets/backgrounds/pink_2.jpeg",
    "pink_3": "assets/backgrounds/pink_3.jpeg",
    "pink_4": "assets/backgrounds/pink_4.jpeg",
    "pink_5": "assets/backgrounds/pink_5.jpeg",
    # White series
    "white_1": "assets/backgrounds/white_1.jpeg",
}


def get_preset_background(name: str) -> Optional[str]:
    """Get the file path for a preset background.

    Args:
        name: Preset name (e.g., 'paper_texture')

    Returns:
        Absolute path to the background image, or None if not found

    Examples:
        >>> from poster_design.core.backgrounds import get_preset_background
        >>> path = get_preset_background("paper_texture")
        >>> print(path)
        /path/to/package/assets/backgrounds/paper_texture.png
    """
    if name not in PRESET_BACKGROUNDS:
        return None

    path = PRESET_BACKGROUNDS[name]

    # If it's an absolute path (user-registered), return as-is
    if Path(path).is_absolute():
        return path

    # For relative paths (built-in presets), construct full path
    module_dir = Path(__file__).parent.parent
    full_path = module_dir / path

    # Return the path even if file doesn't exist yet (during development)
    return str(full_path)


def list_preset_backgrounds() -> list[str]:
    """List all available preset background names.

    Returns:
        List of preset names

    Examples:
        >>> from poster_design.core.backgrounds import list_preset_backgrounds
        >>> list_preset_backgrounds()
        ['paper_texture', 'wood_grain', 'fabric_linen', 'marble', 'geometric']
    """
    return list(PRESET_BACKGROUNDS.keys())


def register_preset_background(name: str, path: str) -> None:
    """Register a custom preset background.

    This allows users to add their own backgrounds that can be
    referenced by name in set_background(preset=...).

    Args:
        name: Name for the preset
        path: Path to the image file

    Examples:
        >>> from poster_design.core.backgrounds import register_preset_background
        >>> register_preset_background("my_texture", "/path/to/texture.jpg")
        >>> # Now can use: canvas.set_background(preset="my_texture")
    """
    PRESET_BACKGROUNDS[name] = path
