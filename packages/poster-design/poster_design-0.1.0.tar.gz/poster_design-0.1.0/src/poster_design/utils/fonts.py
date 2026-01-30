"""
Font management utility for poster design.

This module provides functions to detect text language and select
appropriate fonts for rendering, including support for Chinese characters.
"""

import re
import platform
from pathlib import Path
from typing import Optional, Tuple

from PIL import ImageFont


# Common CJK character ranges
CJK_RANGES = [
    (0x4E00, 0x9FFF),   # CJK Unified Ideographs
    (0x3400, 0x4DBF),   # CJK Unified Ideographs Extension A
    (0x20000, 0x2A6DF), # CJK Unified Ideographs Extension B
    (0x2A700, 0x2B73F), # CJK Unified Ideographs Extension C
    (0x2B740, 0x2B81F), # CJK Unified Ideographs Extension D
    (0x2B820, 0x2CEAF), # CJK Unified Ideographs Extension E
    (0x2CEB0, 0x2EBEF), # CJK Unified Ideographs Extension F
    (0x3000, 0x303F),   # CJK Symbols and Punctuation
    (0xFF00, 0xFFEF),   # Halfwidth and Fullwidth Forms
]

# Platform-specific font paths for CJK fonts
PLATFORM_FONTS = {
    "Darwin": {  # macOS
        "chinese": [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ],
        "fallback": "/System/Library/Fonts/Helvetica.ttc",
    },
    "Linux": {
        "chinese": [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        ],
        "fallback": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    },
    "Windows": {
        "chinese": [
            "C:\\Windows\\Fonts\\msyh.ttc",  # Microsoft YaHei
            "C:\\Windows\\Fonts\\simhei.ttf",
            "C:\\Windows\\Fonts\\simsun.ttc",
        ],
        "fallback": "C:\\Windows\\Fonts\\arial.ttf",
    }
}


def contains_cjk(text: str) -> bool:
    """Check if text contains CJK (Chinese/Japanese/Korean) characters.

    Args:
        text: The text to check

    Returns:
        True if text contains CJK characters, False otherwise
    """
    for char in text:
        codepoint = ord(char)
        for start, end in CJK_RANGES:
            if start <= codepoint <= end:
                return True
    return False


def get_platform() -> str:
    """Get the current platform name.

    Returns:
        Platform name: 'Darwin' for macOS, 'Linux', or 'Windows'
    """
    return platform.system()


def find_chinese_font() -> Optional[str]:
    """Find a suitable Chinese font on the system.

    Returns:
        Path to a Chinese font file, or None if not found
    """
    system = get_platform()
    fonts_config = PLATFORM_FONTS.get(system, PLATFORM_FONTS["Darwin"])

    for font_path in fonts_config["chinese"]:
        if Path(font_path).exists():
            return font_path

    return None


def load_font(
    font_family: str,
    font_size: int,
    text: Optional[str] = None,
) -> ImageFont.FreeTypeFont:
    """Load an appropriate font for rendering text.

    This function intelligently selects a font based on:
    1. The requested font family
    2. The text content (to detect if CJK characters are present)
    3. System availability

    Args:
        font_family: Requested font family name (e.g., "Arial")
        font_size: Font size in pixels
        text: The text to be rendered (used for CJK detection)

    Returns:
        PIL ImageFont object ready for rendering
    """
    # If text contains CJK, prioritize finding a CJK-capable font
    if text and contains_cjk(text):
        # First try to find a Chinese font directly
        chinese_font_path = find_chinese_font()
        if chinese_font_path:
            try:
                return ImageFont.truetype(chinese_font_path, font_size)
            except OSError:
                pass  # Chinese font failed to load, continue below

    # Try to load the requested font directly
    try:
        font = ImageFont.truetype(font_family, font_size)
        # If text is provided and contains CJK, verify the font can render it
        if text and contains_cjk(text):
            # Try to render a test character and verify it produces output
            test_char = next((c for c in text if contains_cjk(c)), '中')
            try:
                # Get the bounding box - if font can't render, size will be 0 or very small
                left, top, right, bottom = font.getbbox(test_char)
                width = right - left
                height = bottom - top
                # If the character renders with reasonable size, font supports CJK
                if width > 0 and height > font_size * 0.3:
                    return font
                # Otherwise, fall through to use Chinese font
            except (OSError, AttributeError):
                pass  # Font doesn't support CJK, fall through
        else:
            return font
    except OSError:
        pass  # Requested font not available, fall through

    # Last resort: try Chinese font again if we haven't yet
    if text and contains_cjk(text):
        chinese_font_path = find_chinese_font()
        if chinese_font_path:
            try:
                return ImageFont.truetype(chinese_font_path, font_size)
            except OSError:
                pass  # Chinese font failed to load

    # Final fallback to default font
    try:
        return ImageFont.load_default(font_size)
    except TypeError:
        # Older Pillow versions don't support size parameter
        return ImageFont.load_default()


def get_text_size(
    text: str,
    font: ImageFont.FreeTypeFont,
) -> Tuple[int, int]:
    """Get the size of text when rendered with a font.

    Args:
        text: The text to measure
        font: The font to use

    Returns:
        Tuple of (width, height) in pixels
    """
    try:
        # Pillow >= 10.0.0
        left, top, right, bottom = font.getbbox(text)
        return (right - left, bottom - top)
    except AttributeError:
        # Older Pillow versions
        return font.getsize(text)
