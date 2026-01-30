"""
Canvas class for poster creation and management.

This module provides the Canvas class which is the main interface
for creating and managing poster designs.
"""

import uuid
from pathlib import Path
from typing import Optional, Union, Dict, Any
from PIL import Image, ImageDraw, ImageFont

from poster_design.core.models import Element as ElementModel
from poster_design.core.elements import Element, TextElement
from poster_design.core.positioning import resolve_position
from poster_design.utils.fonts import load_font, get_text_size
from poster_design.utils.text_wrapper import wrap_text, calculate_line_position


class Canvas:
    """Main canvas class for poster design.

    The Canvas class manages the poster creation process including
    background, elements, and export functionality.

    Attributes:
        width: Canvas width in pixels
        height: Canvas height in pixels
        dpi: Dots per inch for the canvas
    """

    # Preset canvas sizes with (width, height, dpi)
    PRESETS: Dict[str, tuple[int, int, int]] = {
        "instagram_post": (1080, 1080, 72),
        "instagram_story": (1080, 1920, 72),
        "facebook_post": (1200, 630, 72),
        "wechat_cover": (900, 500, 72),
        "a4_portrait": (2480, 3508, 300),
        "a4_landscape": (3508, 2480, 300),
    }

    def __init__(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        preset: Optional[str] = None,
        dpi: int = 72,
    ):
        # Validate arguments
        if preset is not None:
            if width is not None or height is not None:
                raise ValueError(
                    "Cannot specify both preset and custom dimensions"
                )
            if preset not in self.PRESETS:
                raise ValueError(f"Unknown preset: {preset}")
            width, height, dpi = self.PRESETS[preset]
        elif width is None or height is None:
            raise ValueError(
                "Must specify either preset or both width and height"
            )

        self.width = width
        self.height = height
        self.dpi = dpi
        self.background: Dict[str, Any] = {"type": "color", "value": "#FFFFFF"}
        self.elements: Dict[str, Element] = {}
        self.checkpoints: Dict[str, Dict[str, Any]] = {}
        self._id = f"canvas_{uuid.uuid4().hex[:8]}"

    @property
    def size(self) -> tuple[int, int]:
        """Get canvas size as (width, height) tuple."""
        return (self.width, self.height)

    @property
    def center(self) -> tuple[float, float]:
        """Get canvas center point as (x, y) tuple."""
        return (self.width / 2, self.height / 2)

    def set_background(
        self,
        color: Optional[str] = None,
        gradient: Optional[list[str]] = None,
        image: Optional[str] = None,
        preset: Optional[str] = None,
    ) -> None:
        """Set the canvas background.

        Args:
            color: Solid color as hex string
            gradient: List of hex colors for gradient
            image: Path to background image
            preset: Name of preset background (e.g., 'paper_texture')

        Raises:
            ValueError: If multiple or no background types are specified
            ValueError: If preset name is not found
        """
        provided = [
            spec is not None
            for spec in [color, gradient, image, preset]
        ]
        if sum(provided) == 0:
            raise ValueError("Must specify at least one background type")
        if sum(provided) > 1:
            raise ValueError("Cannot specify multiple background types")

        if preset is not None:
            from poster_design.core.backgrounds import get_preset_background
            image_path = get_preset_background(preset)
            if image_path is None:
                raise ValueError(f"Unknown preset background: {preset}")
            self.background = {"type": "image", "source": image_path}
        elif color:
            self.background = {"type": "color", "value": color}
        elif gradient:
            self.background = {"type": "gradient", "colors": gradient}
        elif image:
            self.background = {"type": "image", "source": image}

    def add(
        self,
        element: Element,
        position: Union[tuple[float, float], str] = (0, 0),
        offset_x: float = 0,
        offset_y: float = 0,
        max_width: Optional[int] = None,
    ) -> str:
        """Add an element to the canvas.

        Args:
            element: The element to add
            position: Position as (x, y) tuple or semantic position (e.g., "center")
            offset_x: X offset from position
            offset_y: Y offset from position
            max_width: Maximum width for text elements (enables wrapping)

        Returns:
            The ID of the added element
        """
        # Resolve semantic positions
        if isinstance(position, str):
            x, y = resolve_position(
                position, (self.width, self.height), (element.size.width, element.size.height)
            )
        else:
            x, y = position

        # Apply offsets
        x += offset_x
        y += offset_y

        # Update element position
        element.position.x = x
        element.position.y = y

        # Store max_width for text elements
        if max_width is not None and element.type.value == "text":
            if not hasattr(element, "max_width"):
                element.max_width = max_width
            else:
                element.max_width = max_width

        # Store element
        element_id = element.id
        self.elements[element_id] = element
        return element_id

    def get_element(self, element_id: str) -> Optional[Element]:
        """Get an element by ID.

        Args:
            element_id: The element ID to look up

        Returns:
            The element if found, None otherwise
        """
        return self.elements.get(element_id)

    def remove(self, element_id: str) -> bool:
        """Remove an element from the canvas.

        Args:
            element_id: The ID of the element to remove

        Returns:
            True if element was removed, False if not found
        """
        if element_id in self.elements:
            del self.elements[element_id]
            return True
        return False

    def get_sorted_elements(self) -> list[Element]:
        """Get elements sorted by z-index.

        Returns:
            List of elements sorted by z-index (lowest first)
        """
        return sorted(
            self.elements.values(),
            key=lambda e: e.z_index
        )

    def save_checkpoint(self, name: str) -> None:
        """Save a checkpoint of the current canvas state.

        Args:
            name: Name for the checkpoint
        """
        self.checkpoints[name] = {
            "background": self.background.copy(),
            "elements": {
                elem_id: {
                    "type": elem.type,
                    "position": (elem.position.x, elem.position.y),
                    "size": (elem.size.width, elem.size.height),
                    "z_index": elem.z_index,
                    "opacity": elem.opacity,
                    "rotation": elem.rotation,
                }
                for elem_id, elem in self.elements.items()
            },
        }

    def restore_checkpoint(self, name: str) -> None:
        """Restore a previously saved checkpoint.

        Args:
            name: Name of the checkpoint to restore

        Raises:
            KeyError: If checkpoint not found
        """
        if name not in self.checkpoints:
            raise KeyError(f"Checkpoint not found: {name}")

        checkpoint = self.checkpoints[name]
        self.background = checkpoint["background"]

        # Note: Full element restoration would require recreating elements
        # For now, we just clear and restore basic properties
        self.elements.clear()

    def export(
        self,
        path: str,
        format: str = "png",
        dpi: Optional[int] = None,
        quality: int = 95,
    ) -> None:
        """Export the canvas to an image file.

        Args:
            path: Output file path
            format: Output format (png, jpg, pdf)
            dpi: DPI for export (defaults to canvas DPI)
            quality: Quality for lossy formats (1-100)
        """
        # Create parent directories if needed
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create image
        export_dpi = dpi if dpi is not None else self.dpi
        img = self._render()

        # Save based on format
        format_lower = format.lower()
        if format_lower == "png":
            img.save(output_path, "PNG", dpi=(export_dpi, export_dpi))
        elif format_lower in ("jpg", "jpeg"):
            img.save(output_path, "JPEG", quality=quality, dpi=(export_dpi, export_dpi))
        elif format_lower == "pdf":
            img.save(output_path, "PDF", resolution=export_dpi)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _render(self) -> Image.Image:
        """Render the canvas to a PIL Image.

        Returns:
            Rendered PIL Image
        """
        # Create base image with background
        img = self._render_background()

        # Render elements (placeholder - actual rendering in Phase 3)
        draw = ImageDraw.Draw(img)
        for element in self.get_sorted_elements():
            self._render_element(draw, element)

        return img

    def _render_background(self) -> Image.Image:
        """Render the background.

        Returns:
            PIL Image with background
        """
        if self.background["type"] == "color":
            color = self.background["value"]
            return Image.new("RGB", (self.width, self.height), color)

        elif self.background["type"] == "gradient":
            # Simple gradient rendering
            colors = self.background["colors"]
            img = Image.new("RGB", (self.width, self.height))
            pixels = img.load()

            for y in range(self.height):
                # Calculate color for this row
                ratio = y / self.height
                r = int(self._interpolate(
                    int(colors[0][1:3], 16),
                    int(colors[-1][1:3], 16),
                    ratio
                ))
                g = int(self._interpolate(
                    int(colors[0][3:5], 16),
                    int(colors[-1][3:5], 16),
                    ratio
                ))
                b = int(self._interpolate(
                    int(colors[0][5:7], 16),
                    int(colors[-1][5:7], 16),
                    ratio
                ))
                for x in range(self.width):
                    pixels[x, y] = (r, g, b)

            return img

        elif self.background["type"] == "image":
            # Load and fit background image
            source_path = self.background["source"]
            bg_img = Image.open(source_path)
            return bg_img.resize((self.width, self.height))

        # Default white background
        return Image.new("RGB", (self.width, self.height), "white")

    def _render_element(self, draw: ImageDraw.ImageDraw, element: Element) -> None:
        """Render an element to the draw context.

        Args:
            draw: PIL ImageDraw context
            element: Element to render
        """
        if element.type.value == "text":
            self._render_text(draw, element)
        # Other element types will be implemented in full rendering

    def _render_text(self, draw: ImageDraw.ImageDraw, element: Element) -> None:
        """Render a text element with automatic wrapping.

        Args:
            draw: PIL ImageDraw context
            element: Text element to render
        """
        if not isinstance(element, TextElement):
            return

        x = int(element.position.x)
        y = int(element.position.y)
        text = element.text

        # Use intelligent font loading that handles CJK characters
        font = load_font(
            font_family=element.font_family,
            font_size=element.font_size,
            text=text,  # Pass text to detect if CJK font is needed
        )

        # Determine max width for wrapping
        # If element has max_width attribute, use it; otherwise use canvas width with margin
        element_max_width = getattr(element, "max_width", None)
        if element_max_width is None:
            # Default to canvas width with margin
            margin = 40  # Default margin on each side
            element_max_width = self.width - (2 * margin)

        # Wrap text to fit within max width
        wrapped_lines = wrap_text(text, font, element_max_width)

        # Get line height for spacing
        line_height = element.line_height
        font_height = element.font_size * line_height

        # Margin for text (ensure text doesn't touch edges)
        text_margin = 20

        # Render each line
        for i, line in enumerate(wrapped_lines):
            if not line:  # Empty line
                continue

            # Calculate x position based on alignment
            try:
                bbox_left, top, bbox_right, bottom = font.getbbox(line)
                line_width = bbox_right - bbox_left
            except AttributeError:
                line_width = font.getsize(line)[0]

            # Calculate line x position with margin consideration
            available_width = self.width - (2 * text_margin)
            line_x = calculate_line_position(line_width, available_width, element.align) + text_margin

            # Adjust starting y position for multi-line text
            # For multi-line text, adjust so the block is centered on the original y
            if len(wrapped_lines) > 1:
                total_height = len(wrapped_lines) * font_height
                line_y = y - (total_height // 2) + (i * font_height)
            else:
                line_y = y

            draw.text((line_x, line_y), line, fill=element.color, font=font)

    def _interpolate(self, start: int, end: int, ratio: float) -> int:
        """Interpolate between two values.

        Args:
            start: Start value
            end: End value
            ratio: Interpolation ratio (0-1)

        Returns:
            Interpolated value
        """
        return int(start + (end - start) * ratio)
