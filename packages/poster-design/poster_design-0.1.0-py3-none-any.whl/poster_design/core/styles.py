"""
Style system for poster design.

This module provides classes for managing styles, themes, and
color schemes.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List

from poster_design.utils.colors import generate_gradient


@dataclass
class TextStyle:
    """Text styling configuration.

    Attributes:
        font_family: Font family name
        font_size: Font size in pixels
        color: Text color as hex string
        bold: Whether text is bold
        italic: Whether text is italic
        line_height: Line height multiplier
        align: Text alignment
    """

    font_family: str = "Arial"
    font_size: int = 24
    color: str = "#000000"
    bold: bool = False
    italic: bool = False
    line_height: float = 1.2
    align: str = "left"

    def to_dict(self) -> Dict[str, any]:
        """Convert style to dictionary.

        Returns:
            Dictionary representation of the style
        """
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color": self.color,
            "bold": self.bold,
            "italic": self.italic,
            "line_height": self.line_height,
            "align": self.align,
        }


@dataclass
class ColorScheme:
    """Color scheme for consistent design.

    Attributes:
        primary: Primary color
        secondary: Secondary color
        accent: Accent color
        background: Background color
        text: Text color
    """

    primary: str
    secondary: str
    accent: str
    background: str
    text: str

    def to_dict(self) -> Dict[str, str]:
        """Convert scheme to dictionary.

        Returns:
            Dictionary representation of the scheme
        """
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "text": self.text,
        }


class StyleSystem:
    """Manages styles and themes for poster design."""

    def __init__(self):
        """Initialize the style system."""
        self._themes: Dict[str, Dict[str, any]] = {}
        self._schemes: Dict[str, ColorScheme] = {}
        self._register_default_schemes()

    def _register_default_schemes(self) -> None:
        """Register default color schemes."""
        self._schemes["light"] = ColorScheme(
            primary="#2196F3",
            secondary="#FFC107",
            accent="#FF5722",
            background="#FFFFFF",
            text="#000000",
        )

        self._schemes["dark"] = ColorScheme(
            primary="#BB86FC",
            secondary="#03DAC6",
            accent="#CF6679",
            background="#121212",
            text="#FFFFFF",
        )

        self._schemes["nature"] = ColorScheme(
            primary="#4CAF50",
            secondary="#8BC34A",
            accent="#FF9800",
            background="#F1F8E9",
            text="#1B5E20",
        )

    def register_theme(self, name: str, theme: Dict[str, any]) -> None:
        """Register a new theme.

        Args:
            name: Theme name
            theme: Theme configuration dict
        """
        self._themes[name] = theme

    def get_theme(self, name: str) -> Optional[Dict[str, any]]:
        """Get a theme by name.

        Args:
            name: Theme name

        Returns:
            Theme dict if found, None otherwise
        """
        return self._themes.get(name)

    def register_scheme(self, name: str, scheme: ColorScheme) -> None:
        """Register a color scheme.

        Args:
            name: Scheme name
            scheme: ColorScheme object
        """
        self._schemes[name] = scheme

    def get_scheme(self, name: str) -> Optional[ColorScheme]:
        """Get a color scheme by name.

        Args:
            name: Scheme name

        Returns:
            ColorScheme if found, None otherwise
        """
        return self._schemes.get(name)

    def list_schemes(self) -> List[str]:
        """List all registered color schemes.

        Returns:
            List of scheme names
        """
        return list(self._schemes.keys())

    def list_themes(self) -> List[str]:
        """List all registered themes.

        Returns:
            List of theme names
        """
        return list(self._themes.keys())

    def apply_theme(
        self,
        element,
        theme_name: str
    ) -> None:
        """Apply a theme to an element.

        Args:
            element: Element to apply theme to
            theme_name: Name of theme to apply

        Raises:
            KeyError: If theme not found
        """
        theme = self.get_theme(theme_name)
        if theme is None:
            raise KeyError(f"Theme not found: {theme_name}")

        # Apply theme properties to element
        for key, value in theme.items():
            if hasattr(element, key):
                setattr(element, key, value)
