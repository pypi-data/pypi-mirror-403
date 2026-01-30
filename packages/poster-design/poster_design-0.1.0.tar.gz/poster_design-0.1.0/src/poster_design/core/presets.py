"""
Canvas preset definitions.

This module contains predefined canvas sizes for common use cases.
"""

from typing import Dict, Tuple


# Canvas presets: name -> (width, height, dpi)
CANVAS_PRESETS: Dict[str, Tuple[int, int, int]] = {
    # Social Media
    "instagram_post": (1080, 1080, 72),
    "instagram_story": (1080, 1920, 72),
    "facebook_post": (1200, 630, 72),
    "twitter_post": (1200, 675, 72),
    "linkedin_post": (1200, 627, 72),
    "pinterest_post": (1000, 1500, 72),

    # Chinese Platforms
    "wechat_cover": (900, 500, 72),
    "weibo_post": (1080, 1260, 72),
    "douyin_cover": (1080, 1920, 72),

    # Print
    "a4_portrait": (2480, 3508, 300),
    "a4_landscape": (3508, 2480, 300),
    "a3_portrait": (3508, 4960, 300),
    "a3_landscape": (4960, 3508, 300),
    "letter_portrait": (2550, 3300, 300),
    "letter_landscape": (3300, 2550, 300),

    # Common Ratios
    "square_1080": (1080, 1080, 72),
    "square_2048": (2048, 2048, 72),
    "landscape_16_9": (1920, 1080, 72),
    "portrait_9_16": (1080, 1920, 72),
    "landscape_4_3": (1920, 1440, 72),
    "portrait_3_4": (1440, 1920, 72),
}


def get_preset(name: str) -> Tuple[int, int, int]:
    """Get a preset by name.

    Args:
        name: Preset name

    Returns:
        Tuple of (width, height, dpi)

    Raises:
        KeyError: If preset not found
    """
    if name not in CANVAS_PRESETS:
        raise KeyError(f"Unknown preset: {name}")
    return CANVAS_PRESETS[name]


def list_presets() -> list[str]:
    """List all available preset names.

    Returns:
        List of preset names
    """
    return list(CANVAS_PRESETS.keys())


def add_preset(name: str, width: int, height: int, dpi: int = 72) -> None:
    """Add a custom preset.

    Args:
        name: Preset name
        width: Canvas width
        height: Canvas height
        dpi: DPI (default 72)
    """
    CANVAS_PRESETS[name] = (width, height, dpi)
