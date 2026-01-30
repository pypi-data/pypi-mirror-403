"""
Layout management system for poster design.

This module provides classes for aligning, distributing, and
arranging elements on a canvas.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass, field

from poster_design.core.elements import Element
from poster_design.core.models import Position


class LayoutManager:
    """Manages element layout operations."""

    @staticmethod
    def align_elements(
        elements: List[Element],
        alignment: str,
        canvas_size: Tuple[int, int],
    ) -> None:
        """Align elements to a specific alignment.

        Args:
            elements: List of elements to align
            alignment: Alignment type (left, center, right, top, middle, bottom)
            canvas_size: Canvas size as (width, height)

        Raises:
            ValueError: If alignment is not recognized
        """
        if not elements:
            return

        canvas_width, canvas_height = canvas_size
        alignment = alignment.lower()

        if alignment == "left":
            # Align left edges
            min_x = min(e.position.x for e in elements)
            for elem in elements:
                elem.position.x = min_x

        elif alignment == "center":
            # Center horizontally - align all element centers to canvas center
            center_x = canvas_width / 2
            for elem in elements:
                elem.position.x = center_x - elem.size.width / 2

        elif alignment == "right":
            # Align right edges
            max_x = max(e.position.x + e.size.width for e in elements)
            for elem in elements:
                elem.position.x = max_x - elem.size.width

        elif alignment == "top":
            # Align top edges
            min_y = min(e.position.y for e in elements)
            for elem in elements:
                elem.position.y = min_y

        elif alignment == "middle":
            # Center vertically - align all element centers to canvas center
            center_y = canvas_height / 2
            for elem in elements:
                elem.position.y = center_y - elem.size.height / 2

        elif alignment == "bottom":
            # Align bottom edges
            max_y = max(e.position.y + e.size.height for e in elements)
            for elem in elements:
                elem.position.y = max_y - elem.size.height

        else:
            raise ValueError(f"Unknown alignment: {alignment}")

    @staticmethod
    def distribute_elements(
        elements: List[Element],
        direction: str,
        canvas_size: Tuple[int, int],
        spacing: float = 0,
    ) -> None:
        """Distribute elements evenly.

        Args:
            elements: List of elements to distribute
            direction: Distribution direction (horizontal, vertical)
            canvas_size: Canvas size as (width, height)
            spacing: Spacing between elements

        Raises:
            ValueError: If direction is not recognized
        """
        # Validate direction first
        direction = direction.lower()
        if direction not in ("horizontal", "vertical"):
            raise ValueError(f"Unknown distribution direction: {direction}")

        if len(elements) < 2:
            return

        if direction == "horizontal":
            # Sort by x position
            sorted_elems = sorted(elements, key=lambda e: e.position.x)
            total_width = sum(e.size.width for e in sorted_elems)
            total_spacing = spacing * (len(elements) - 1)
            start_x = (canvas_size[0] - total_width - total_spacing) / 2

            current_x = start_x
            for elem in sorted_elems:
                elem.position.x = current_x
                current_x += elem.size.width + spacing

        elif direction == "vertical":
            # Sort by y position
            sorted_elems = sorted(elements, key=lambda e: e.position.y)
            total_height = sum(e.size.height for e in sorted_elems)
            total_spacing = spacing * (len(elements) - 1)
            start_y = (canvas_size[1] - total_height - total_spacing) / 2

            current_y = start_y
            for elem in sorted_elems:
                elem.position.y = current_y
                current_y += elem.size.height + spacing


@dataclass
class GridLayout:
    """Grid layout for arranging elements.

    Attributes:
        rows: Number of rows in the grid
        cols: Number of columns in the grid
        padding: Padding around the grid
        spacing: Spacing between grid cells
    """

    rows: int
    cols: int
    padding: int = 0
    spacing: int = 0
    cells: list = field(default_factory=list)

    def __post_init__(self):
        """Initialize grid cells."""
        self.cells = [None] * (self.rows * self.cols)

    def add(self, element: Element, row: int, col: int) -> None:
        """Add an element to a specific grid cell.

        Args:
            element: Element to add
            row: Row index (0-based)
            col: Column index (0-based)

        Raises:
            IndexError: If row or col is out of bounds
        """
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            raise IndexError(f"Grid position ({row}, {col}) out of bounds")

        index = row * self.cols + col
        self.cells[index] = element

    def get_position(self, row: int, col: int, canvas_size: Tuple[int, int]) -> Tuple[float, float]:
        """Get the position for a grid cell.

        Args:
            row: Row index (0-based)
            col: Column index (0-based)
            canvas_size: Canvas size as (width, height)

        Returns:
            Position as (x, y) tuple
        """
        canvas_width, canvas_height = canvas_size

        # Calculate available space
        available_width = canvas_width - (2 * self.padding)
        available_height = canvas_height - (2 * self.padding)

        # Calculate cell sizes
        cell_width = (available_width - (self.cols - 1) * self.spacing) / self.cols
        cell_height = (available_height - (self.rows - 1) * self.spacing) / self.rows

        # Calculate position
        x = self.padding + col * (cell_width + self.spacing)
        y = self.padding + row * (cell_height + self.spacing)

        return (x, y)

    def get_cell_size(self, canvas_size: Tuple[int, int]) -> Tuple[float, float]:
        """Get the size of each cell in the grid.

        Args:
            canvas_size: Canvas size as (width, height)

        Returns:
            Cell size as (width, height) tuple
        """
        canvas_width, canvas_height = canvas_size

        available_width = canvas_width - (2 * self.padding)
        available_height = canvas_height - (2 * self.padding)

        cell_width = (available_width - (self.cols - 1) * self.spacing) / self.cols
        cell_height = (available_height - (self.rows - 1) * self.spacing) / self.rows

        return (cell_width, cell_height)


def auto_layout(
    canvas,
    layout_type: str = "balanced",
    padding: int = 40,
) -> None:
    """Automatically layout elements on the canvas.

    Args:
        canvas: Canvas object
        layout_type: Layout algorithm (grid, flow, balanced)
        padding: Padding around elements

    Raises:
        ValueError: If layout_type is not recognized
    """
    elements = list(canvas.elements.values())
    if not elements:
        return

    layout_type = layout_type.lower()

    if layout_type == "grid":
        # Arrange in a grid
        count = len(elements)
        cols = int(count ** 0.5) or 1
        rows = (count + cols - 1) // cols

        grid = GridLayout(rows=rows, cols=cols, padding=padding, spacing=20)

        cell_width, cell_height = grid.get_cell_size(canvas.size)

        for i, elem in enumerate(elements):
            row = i // cols
            col = i % cols
            x, y = grid.get_position(row, col, canvas.size)
            elem.position.x = x + (cell_width - elem.size.width) / 2
            elem.position.y = y + (cell_height - elem.size.height) / 2

    elif layout_type == "flow":
        # Flow elements horizontally, wrap to next row
        x = padding
        y = padding
        max_y = padding

        for elem in elements:
            if x + elem.size.width > canvas.width - padding:
                # Move to next row
                x = padding
                y = max_y + 20

            elem.position.x = x
            elem.position.y = y

            x += elem.size.width + 20
            max_y = max(max_y, y + elem.size.height)

    elif layout_type == "balanced":
        # Center all elements
        LayoutManager.align_elements(elements, "center", canvas.size)

    else:
        raise ValueError(f"Unknown layout type: {layout_type}")
