"""
Input validation utility functions.

This module provides validation functions for various user inputs
including colors, dimensions, fonts, and file paths.
"""

import re
from pathlib import Path
from typing import Optional


def validate_color(color: str) -> bool:
    """Validate a hex color string.

    Args:
        color: The color string to validate (e.g., "#FF0000")

    Returns:
        True if the color is a valid hex color, False otherwise
    """
    if not color or not isinstance(color, str):
        return False

    # Support both #RGB and #RRGGBB formats
    hex_pattern = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    return bool(hex_pattern.match(color))


def validate_dimensions(value: int, min_val: int = 1, max_val: int = 10000) -> bool:
    """Validate a dimension value is within acceptable range.

    Args:
        value: The dimension value to validate
        min_val: Minimum allowed value (default: 1)
        max_val: Maximum allowed value (default: 10000)

    Returns:
        True if the value is within range, False otherwise
    """
    if not isinstance(value, (int, float)):
        return False

    try:
        int_value = int(value)
    except (ValueError, TypeError):
        return False

    return min_val <= int_value <= max_val


def validate_font(font_name: str) -> bool:
    """Validate a font name.

    This checks if the font name is non-empty and potentially valid.
    For production use, consider using fontconfig or platform-specific
    font validation to check if the font actually exists on the system.

    Args:
        font_name: The font name to validate

    Returns:
        True if the font name appears valid, False otherwise
    """
    if not font_name or not isinstance(font_name, str):
        return False

    # Check if string is empty or only whitespace
    if not font_name.strip():
        return False

    # Basic sanity check - no control characters
    if any(ord(c) < 32 for c in font_name):
        return False

    # Check for common valid font names (basic whitelist approach)
    # This is a simplified approach - in production you'd use system font APIs
    common_fonts = {
        "Arial", "Helvetica", "Times New Roman", "Georgia", "Verdana",
        "Courier New", "Tahoma", "Trebuchet MS", "Arial Black", "Impact",
        "Comic Sans MS", "Lucida Console", "Lucida Sans Unicode",
        "Palatino Linotype", "Segoe UI", "Roboto", "Open Sans",
        "Lato", "Montserrat", "Oswald", "Raleway", "Poppins",
        "Source Sans Pro", "PT Sans", "Noto Sans", "Ubuntu",
        # Add common Chinese fonts
        "SimSun", "SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei",
    }

    # Check if it's a known font or looks like a font name
    # (contains only reasonable characters, no digits for simple fonts)
    stripped = font_name.strip()
    if stripped in common_fonts:
        return True

    # For other names, be more permissive but require proper format
    # Font names typically contain letters, spaces, and some special chars
    # but not standalone digits or obviously made-up names
    if re.match(r"^[\w\s\-\.'']+$", stripped):
        # Reject obviously fake names with random numbers
        if re.search(r"\d{3,}", stripped):
            return False
        return True

    return False


def validate_path(path: str) -> bool:
    """Validate a file path or URL.

    For absolute paths, checks if the file exists.
    For relative paths, validates the format but doesn't check existence.

    Args:
        path: The path or URL to validate

    Returns:
        True if the path is valid, False otherwise
    """
    if not path or not isinstance(path, str):
        return False

    path = path.strip()

    # Check for empty string
    if not path:
        return False

    # Check for URL (http or https only - no ftp, etc.)
    if "://" in path:
        if path.startswith("http://") or path.startswith("https://"):
            # Basic URL validation
            url_pattern = re.compile(
                r"^https?://"  # http:// or https://
                r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
                r"localhost|"  # localhost
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
                r"(?::\d+)?"  # optional port
                r"(?:/?|[/?]\S+)$",
                re.IGNORECASE,
            )
            return bool(url_pattern.match(path))
        # Other protocols (ftp, etc.) are not supported
        return False

    # Check for local file path
    try:
        p = Path(path)

        # Must look like a valid path (no spaces in weird places, etc.)
        # Reject paths with spaces that aren't valid file paths
        if " " in path and not any(path.startswith(prefix) for prefix in ["./", "../", "/"]):
            # String like "not a path" should fail
            return False

        # Basic path validation - check it has a valid structure
        str_path = str(p)
        # Must contain valid filename characters
        if not str_path or str_path in (".", ".."):
            return False

        # Reject invalid URL-like strings
        if path.startswith("://"):
            return False

        # For absolute paths (not starting with ./ or ../), check if parent exists
        if path.startswith("/") or (len(path) >= 2 and path[1] == ":"):
            # Absolute path - check if parent directory exists
            # The file itself doesn't need to exist (it might be created later)
            parent = p.parent
            return parent.exists() and parent.is_dir()

        # For relative paths, just validate format
        return True
    except (OSError, ValueError):
        return False
