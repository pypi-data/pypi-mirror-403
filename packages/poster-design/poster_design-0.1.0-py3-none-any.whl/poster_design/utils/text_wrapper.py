"""
Text wrapping utilities for poster design.

This module provides functions to wrap text to fit within specified width,
handling both Chinese and English text appropriately.
"""

from typing import List, Tuple
import re

from PIL import ImageFont

from poster_design.utils.fonts import load_font


def wrap_text(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> List[str]:
    """Wrap text to fit within max_width pixels.

    This function intelligently wraps text:
    - Preserves explicit line breaks (\n)
    - Splits Chinese text by character
    - Splits English text by words
    - Returns list of lines, each fitting within max_width

    Args:
        text: The text to wrap
        font: The font to use for measuring text width
        max_width: Maximum width in pixels

    Returns:
        List of wrapped lines

    Examples:
        >>> from PIL import ImageFont
        >>> font = ImageFont.load_default()
        >>> lines = wrap_text("Hello world", font, 100)
        >>> len(lines) > 0
        True
    """
    if not text:
        return []

    # Split by explicit line breaks first
    paragraphs = text.split('\n')
    wrapped_lines = []

    for paragraph in paragraphs:
        if not paragraph:
            wrapped_lines.append("")
            continue

        # Wrap each paragraph
        lines = _wrap_paragraph(paragraph, font, max_width)
        wrapped_lines.extend(lines)

    return wrapped_lines


def _wrap_paragraph(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> List[str]:
    """Wrap a single paragraph (no embedded newlines).

    Args:
        text: The paragraph text
        font: The font to use
        max_width: Maximum width in pixels

    Returns:
        List of wrapped lines
    """
    if not text:
        return []

    lines = []
    current_line = ""

    # Check if text contains CJK characters
    has_cjk = _contains_cjk(text)

    if has_cjk:
        # For CJK text, split by character
        for char in text:
            test_line = current_line + char
            text_width = _get_text_width(test_line, font)

            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
    else:
        # For English text, split by words
        words = text.split(' ')
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            text_width = _get_text_width(test_line, font)

            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                # Word might be too long, split it
                if _get_text_width(word, font) > max_width:
                    split_words = _split_long_word(word, font, max_width)
                    lines.extend(split_words[:-1])
                    current_line = split_words[-1]
                else:
                    current_line = word

    # Add the last line
    if current_line:
        lines.append(current_line)

    return lines if lines else [""]


def _contains_cjk(text: str) -> bool:
    """Check if text contains CJK characters.

    Args:
        text: The text to check

    Returns:
        True if text contains CJK characters
    """
    # CJK Unified Ideographs range
    for char in text:
        codepoint = ord(char)
        if 0x4E00 <= codepoint <= 0x9FFF:
            return True
    return False


def _get_text_width(text: str, font: ImageFont.FreeTypeFont) -> int:
    """Get the width of text when rendered with the given font.

    Args:
        text: The text to measure
        font: The font to use

    Returns:
        Width in pixels
    """
    try:
        # Pillow >= 10.0.0
        left, top, right, bottom = font.getbbox(text)
        return right - left
    except AttributeError:
        # Older Pillow versions
        return font.getsize(text)[0]


def _split_long_word(
    word: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> List[str]:
    """Split a word that's too long for max_width.

    Args:
        word: The word to split
        font: The font to use
        max_width: Maximum width

    Returns:
        List of word fragments
    """
    fragments = []
    current_fragment = ""

    for char in word:
        test_fragment = current_fragment + char
        if _get_text_width(test_fragment, font) <= max_width:
            current_fragment = test_fragment
        else:
            if current_fragment:
                fragments.append(current_fragment)
            current_fragment = char

    if current_fragment:
        fragments.append(current_fragment)

    return fragments if fragments else [word]


def calculate_line_position(
    line_width: int,
    canvas_width: int,
    align: str,
) -> int:
    """Calculate x position for a line based on alignment.

    Args:
        line_width: Width of the rendered line
        canvas_width: Width of the canvas
        align: Alignment type ('left', 'center', 'right')

    Returns:
        X position for the line
    """
    if align == "center":
        return (canvas_width - line_width) // 2
    elif align == "right":
        return canvas_width - line_width
    else:  # left
        return 0
