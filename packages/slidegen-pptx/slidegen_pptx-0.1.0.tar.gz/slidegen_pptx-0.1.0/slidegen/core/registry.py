"""Layout renderer registry for plugin architecture."""

from typing import Any, Dict, List, Optional, Protocol

from pptx.slide import Slide
from pptx.presentation import Presentation


class LayoutRenderer(Protocol):
    """Protocol for layout renderers."""

    def render(self, slide: Slide, data: Dict[str, Any], presentation: Presentation) -> None:
        """
        Render a slide with the given data.
        
        Args:
            slide: The pptx Slide object to render to
            data: Slide data from schema
            presentation: The parent Presentation object
        """
        ...


class LayoutRegistry:
    """Registry for layout renderers."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._renderers: Dict[str, LayoutRenderer] = {}

    def register(self, layout_type: str, renderer: LayoutRenderer) -> None:
        """
        Register a layout renderer.
        
        Args:
            layout_type: The layout type name (e.g., "title", "bullet_list")
            renderer: The renderer instance or class
        """
        self._renderers[layout_type] = renderer

    def get_renderer(self, layout_type: str) -> Optional[LayoutRenderer]:
        """
        Get a renderer for a layout type.
        
        Args:
            layout_type: The layout type name
            
        Returns:
            The renderer if found, None otherwise
        """
        return self._renderers.get(layout_type)

    def list_layouts(self) -> List[str]:
        """
        List all registered layout types.
        
        Returns:
            List of layout type names
        """
        return list(self._renderers.keys())

