"""
MCP tool handlers for poster design.

This module provides handler functions for all MCP tools,
wrapping the core poster design SDK.
"""

from typing import Optional, Union, Tuple, List, Dict, Any
from poster_design import Canvas, TextElement, ImageElement, ShapeElement
from poster_design.core.layout import LayoutManager
from poster_design.mcp.session import SessionManager


class ToolHandlers:
    """Handles all MCP tool calls."""

    def __init__(self, session_timeout: float = 300.0):
        """Initialize tool handlers.

        Args:
            session_timeout: Session timeout in seconds
        """
        self._sessions = SessionManager(default_timeout=session_timeout)

    def _get_canvas(self, session_id: str, canvas_id: str) -> Optional[Canvas]:
        """Get a canvas from a session.

        Args:
            session_id: Session identifier
            canvas_id: Canvas identifier

        Returns:
            Canvas object or None if not found
        """
        session = self._sessions.get_session(session_id)
        if session is None:
            return None
        return session.get_canvas(canvas_id)

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID.

        Args:
            prefix: ID prefix

        Returns:
            Unique ID string
        """
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def create_canvas(
        self,
        session_id: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        preset: Optional[str] = None,
        dpi: int = 72,
    ) -> Dict[str, Any]:
        """Create a new canvas.

        Args:
            session_id: Session identifier
            width: Canvas width (or None if using preset)
            height: Canvas height (or None if using preset)
            preset: Preset name (or None for custom size)
            dpi: DPI setting

        Returns:
            Response dict with success, canvas_id, error
        """
        try:
            session = self._sessions.get_or_create_session(session_id)

            # Create canvas
            if preset:
                canvas = Canvas(preset=preset, dpi=dpi)
            elif width and height:
                canvas = Canvas(width=width, height=height, dpi=dpi)
            else:
                return {
                    "success": False,
                    "error": "Must specify either preset or both width and height",
                }

            canvas_id = self._generate_id("canvas")
            session.add_canvas(canvas_id, canvas)

            return {
                "success": True,
                "canvas_id": canvas_id,
                "data": {
                    "width": canvas.width,
                    "height": canvas.height,
                    "dpi": canvas.dpi,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def set_background(
        self,
        session_id: str,
        canvas_id: str,
        background_type: str,
        color: Optional[str] = None,
        gradient: Optional[List[str]] = None,
        image: Optional[str] = None,
        preset: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set canvas background.

        Args:
            session_id: Session identifier
            canvas_id: Canvas identifier
            background_type: Type of background (color, gradient, image, preset)
            color: Solid color value
            gradient: Gradient color list
            image: Image path
            preset: Preset background name

        Returns:
            Response dict with success, error
        """
        try:
            canvas = self._get_canvas(session_id, canvas_id)
            if canvas is None:
                return {
                    "success": False,
                    "error": f"Canvas not found: {canvas_id}",
                }

            if background_type == "color":
                canvas.set_background(color=color)
            elif background_type == "gradient":
                canvas.set_background(gradient=gradient)
            elif background_type == "image":
                canvas.set_background(image=image)
            elif background_type == "preset":
                canvas.set_background(preset=preset)
            else:
                return {
                    "success": False,
                    "error": f"Unknown background type: {background_type}",
                }

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def add_text(
        self,
        session_id: str,
        canvas_id: str,
        text: str,
        font_size: int = 24,
        color: str = "#000000",
        font_family: str = "Arial",
        bold: bool = False,
        italic: bool = False,
        position: Union[str, Tuple[int, int]] = "center",
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> Dict[str, Any]:
        """Add text element to canvas.

        Args:
            session_id: Session identifier
            canvas_id: Canvas identifier
            text: Text content
            font_size: Font size in pixels
            color: Text color
            font_family: Font family name
            bold: Whether text is bold
            italic: Whether text is italic
            position: Position (alias or coordinates)
            offset_x: X offset from position
            offset_y: Y offset from position

        Returns:
            Response dict with success, element_id, error
        """
        try:
            canvas = self._get_canvas(session_id, canvas_id)
            if canvas is None:
                return {
                    "success": False,
                    "error": f"Canvas not found: {canvas_id}",
                }

            # Create text element
            elem = TextElement(
                text=text,
                font_size=font_size,
                color=color,
                font_family=font_family,
                bold=bold,
                italic=italic,
            )

            # Add to canvas
            element_id = canvas.add(elem, position=position, offset_x=offset_x, offset_y=offset_y)

            return {
                "success": True,
                "element_id": element_id,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def add_image(
        self,
        session_id: str,
        canvas_id: str,
        source: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        fit: str = "cover",
        position: Union[str, Tuple[int, int]] = "center",
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> Dict[str, Any]:
        """Add image element to canvas.

        Args:
            session_id: Session identifier
            canvas_id: Canvas identifier
            source: Image path or URL
            width: Image width (None for original)
            height: Image height (None for original)
            fit: Fit mode (cover, contain, fill)
            position: Position (alias or coordinates)
            offset_x: X offset from position
            offset_y: Y offset from position

        Returns:
            Response dict with success, element_id, error
        """
        try:
            canvas = self._get_canvas(session_id, canvas_id)
            if canvas is None:
                return {
                    "success": False,
                    "error": f"Canvas not found: {canvas_id}",
                }

            # Create image element
            size = None
            if width and height:
                size = (width, height)

            elem = ImageElement(source=source, size=size, fit=fit)

            # Add to canvas
            element_id = canvas.add(elem, position=position, offset_x=offset_x, offset_y=offset_y)

            return {
                "success": True,
                "element_id": element_id,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def add_shape(
        self,
        session_id: str,
        canvas_id: str,
        shape_type: str,
        width: int = 100,
        height: int = 100,
        fill_color: str = "#000000",
        border_color: str = "#000000",
        border_width: int = 0,
        position: Union[str, Tuple[int, int]] = "center",
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> Dict[str, Any]:
        """Add shape element to canvas.

        Args:
            session_id: Session identifier
            canvas_id: Canvas identifier
            shape_type: Type of shape (rectangle, circle, triangle, etc.)
            width: Shape width
            height: Shape height
            fill_color: Fill color
            border_color: Border color
            border_width: Border width
            position: Position (alias or coordinates)
            offset_x: X offset from position
            offset_y: Y offset from position

        Returns:
            Response dict with success, element_id, error
        """
        try:
            canvas = self._get_canvas(session_id, canvas_id)
            if canvas is None:
                return {
                    "success": False,
                    "error": f"Canvas not found: {canvas_id}",
                }

            # Create shape element
            elem = ShapeElement(
                shape_type=shape_type,
                size=(width, height),
                fill_color=fill_color,
                border_color=border_color,
                border_width=border_width,
            )

            # Add to canvas
            element_id = canvas.add(elem, position=position, offset_x=offset_x, offset_y=offset_y)

            return {
                "success": True,
                "element_id": element_id,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def remove_element(
        self,
        session_id: str,
        canvas_id: str,
        element_id: str,
    ) -> Dict[str, Any]:
        """Remove an element from canvas.

        Args:
            session_id: Session identifier
            canvas_id: Canvas identifier
            element_id: Element identifier

        Returns:
            Response dict with success, error
        """
        try:
            canvas = self._get_canvas(session_id, canvas_id)
            if canvas is None:
                return {
                    "success": False,
                    "error": f"Canvas not found: {canvas_id}",
                }

            result = canvas.remove(element_id)

            return {
                "success": result,
                "error": None if result else "Element not found",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def align_elements(
        self,
        session_id: str,
        canvas_id: str,
        alignment: str,
        element_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Align elements on canvas.

        Args:
            session_id: Session identifier
            canvas_id: Canvas identifier
            alignment: Alignment type (left, center, right, top, middle, bottom)
            element_ids: List of element IDs (None for all elements)

        Returns:
            Response dict with success, error
        """
        try:
            canvas = self._get_canvas(session_id, canvas_id)
            if canvas is None:
                return {
                    "success": False,
                    "error": f"Canvas not found: {canvas_id}",
                }

            # Get elements to align
            if element_ids:
                elements = [canvas.get_element(eid) for eid in element_ids]
                elements = [e for e in elements if e is not None]
            else:
                elements = list(canvas.elements.values())

            if not elements:
                return {
                    "success": False,
                    "error": "No elements to align",
                }

            LayoutManager.align_elements(elements, alignment, canvas.size)

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def distribute_elements(
        self,
        session_id: str,
        canvas_id: str,
        direction: str,
        spacing: float = 0,
        element_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Distribute elements on canvas.

        Args:
            session_id: Session identifier
            canvas_id: Canvas identifier
            direction: Distribution direction (horizontal, vertical)
            spacing: Spacing between elements
            element_ids: List of element IDs (None for all elements)

        Returns:
            Response dict with success, error
        """
        try:
            canvas = self._get_canvas(session_id, canvas_id)
            if canvas is None:
                return {
                    "success": False,
                    "error": f"Canvas not found: {canvas_id}",
                }

            # Get elements to distribute
            if element_ids:
                elements = [canvas.get_element(eid) for eid in element_ids]
                elements = [e for e in elements if e is not None]
            else:
                elements = list(canvas.elements.values())

            if not elements:
                return {
                    "success": False,
                    "error": "No elements to distribute",
                }

            LayoutManager.distribute_elements(elements, direction, canvas.size, spacing)

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def export_poster(
        self,
        session_id: str,
        canvas_id: str,
        output_path: str,
        format: str = "png",
        dpi: Optional[int] = None,
        quality: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Export canvas to file.

        Args:
            session_id: Session identifier
            canvas_id: Canvas identifier
            output_path: Output file path
            format: Output format (png, jpg, pdf)
            dpi: DPI for export
            quality: Quality for JPG (1-100)

        Returns:
            Response dict with success, error
        """
        try:
            canvas = self._get_canvas(session_id, canvas_id)
            if canvas is None:
                return {
                    "success": False,
                    "error": f"Canvas not found: {canvas_id}",
                }

            # Build export kwargs
            kwargs = {"format": format}
            if dpi:
                kwargs["dpi"] = dpi
            if quality and format.lower() in ("jpg", "jpeg"):
                kwargs["quality"] = quality

            canvas.export(output_path, **kwargs)

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_canvas_info(
        self,
        session_id: str,
        canvas_id: str,
    ) -> Dict[str, Any]:
        """Get information about a canvas.

        Args:
            session_id: Session identifier
            canvas_id: Canvas identifier

        Returns:
            Response dict with success, data, error
        """
        try:
            canvas = self._get_canvas(session_id, canvas_id)
            if canvas is None:
                return {
                    "success": False,
                    "error": f"Canvas not found: {canvas_id}",
                }

            return {
                "success": True,
                "data": {
                    "width": canvas.width,
                    "height": canvas.height,
                    "dpi": canvas.dpi,
                    "element_count": len(canvas.elements),
                    "background_type": canvas.background.get("type", "none"),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def list_canvases(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """List all canvases in a session.

        Args:
            session_id: Session identifier

        Returns:
            Response dict with success, data, error
        """
        try:
            session = self._sessions.get_session(session_id)
            if session is None:
                return {
                    "success": False,
                    "error": f"Session not found: {session_id}",
                }

            canvases = []
            for canvas_id, canvas in session.canvases.items():
                canvases.append({
                    "canvas_id": canvas_id,
                    "width": canvas.width,
                    "height": canvas.height,
                    "element_count": len(canvas.elements),
                })

            return {
                "success": True,
                "data": {"canvases": canvases},
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def delete_canvas(
        self,
        session_id: str,
        canvas_id: str,
    ) -> Dict[str, Any]:
        """Delete a canvas.

        Args:
            session_id: Session identifier
            canvas_id: Canvas identifier

        Returns:
            Response dict with success, error
        """
        try:
            session = self._sessions.get_session(session_id)
            if session is None:
                return {
                    "success": False,
                    "error": f"Session not found: {session_id}",
                }

            if canvas_id not in session.canvases:
                return {
                    "success": False,
                    "error": f"Canvas not found: {canvas_id}",
                }

            session.remove_canvas(canvas_id)

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
