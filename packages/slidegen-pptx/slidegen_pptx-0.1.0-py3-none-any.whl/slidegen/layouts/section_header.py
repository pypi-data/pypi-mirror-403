"""Section header layout renderer."""

from typing import Any, Dict

from pptx.enum.text import PP_ALIGN
from pptx.slide import Slide
from pptx.presentation import Presentation

from slidegen.layouts.base import BaseLayoutRenderer


class SectionHeaderLayoutRenderer(BaseLayoutRenderer):
    """Renderer for section header slide layout."""

    def render(
        self, slide: Slide, data: Dict[str, Any], presentation: Presentation
    ) -> None:
        """
        Render a section header slide.
        
        Args:
            slide: The slide to render to
            data: Slide data with 'text' or 'title' field
            presentation: The parent presentation
        """
        # Section header can use either 'text' or 'title' field
        text = data.get("text") or data.get("title", "")

        if not text:
            return

        # Calculate font size based on content length
        font_size = self._calculate_font_size(text)

        # Center position (full slide, centered)
        slide_width = self.SLIDE_WIDTH
        slide_height = self.SLIDE_HEIGHT
        text_width = slide_width - (2 * self.MARGIN)
        text_left = self.MARGIN
        text_top = (slide_height / 2) - Inches(0.5)  # Vertically centered

        self.add_text_box(
            slide=slide,
            left=text_left,
            top=text_top,
            width=text_width,
            height=Inches(1.0),
            text=text,
            font_size=font_size,
            bold=True,
            align=PP_ALIGN.CENTER,
        )

    def _calculate_font_size(self, text: str) -> int:
        """
        Calculate appropriate font size for section header based on length.
        
        Args:
            text: Section header text
            
        Returns:
            Font size in points
        """
        length = len(text)
        if length <= 15:
            return 54
        elif length <= 30:
            return 44
        elif length <= 50:
            return 36
        else:
            return 28

