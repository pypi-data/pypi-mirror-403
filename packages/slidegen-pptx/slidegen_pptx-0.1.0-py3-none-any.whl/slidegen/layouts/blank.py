"""Blank layout renderer."""

from typing import Any, Dict

from pptx.slide import Slide
from pptx.presentation import Presentation

from slidegen.layouts.base import BaseLayoutRenderer


class BlankLayoutRenderer(BaseLayoutRenderer):
    """Renderer for blank slide layout."""

    def render(
        self, slide: Slide, data: Dict[str, Any], presentation: Presentation
    ) -> None:
        """
        Render a blank slide.
        
        Args:
            slide: The slide to render to
            data: Slide data (blank layout has no required fields)
            presentation: The parent presentation
        """
        # Blank layout renders nothing - it's a canvas for custom content
        # Users can add custom content programmatically if needed
        pass

