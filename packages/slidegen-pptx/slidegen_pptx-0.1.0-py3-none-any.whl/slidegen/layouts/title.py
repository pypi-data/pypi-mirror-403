"""Title slide layout renderer."""

from typing import Any, Dict

from pptx.enum.text import PP_ALIGN
from pptx.slide import Slide
from pptx.presentation import Presentation
from pptx.util import Inches, Pt

from slidegen.layouts.base import BaseLayoutRenderer


class TitleLayoutRenderer(BaseLayoutRenderer):
    """Renderer for title slide layout."""

    def render(
        self, slide: Slide, data: Dict[str, Any], presentation: Presentation
    ) -> None:
        """
        Render a title slide.
        
        Args:
            slide: The slide to render to
            data: Slide data with 'title' and optional 'subtitle'
            presentation: The parent presentation
        """
        title = data.get("title", "")
        subtitle = data.get("subtitle", "")

        # Calculate font sizes based on content length
        title_font_size = self._calculate_title_font_size(title)
        subtitle_font_size = self._calculate_subtitle_font_size(subtitle)

        # Center position for title
        slide_width = self.SLIDE_WIDTH
        slide_height = self.SLIDE_HEIGHT

        # Title positioning (centered, upper third)
        title_top = slide_height * 0.3
        title_width = slide_width - (2 * self.MARGIN)
        title_left = self.MARGIN

        if title:
            self.add_text_box(
                slide=slide,
                left=title_left,
                top=title_top,
                width=title_width,
                height=Inches(1.5),
                text=title,
                font_size=title_font_size,
                bold=True,
                align=PP_ALIGN.CENTER,
            )

        # Subtitle positioning (centered, below title)
        if subtitle:
            subtitle_top = title_top + Inches(1.8) if title else slide_height * 0.4
            self.add_text_box(
                slide=slide,
                left=title_left,
                top=subtitle_top,
                width=title_width,
                height=Inches(0.8),
                text=subtitle,
                font_size=subtitle_font_size,
                bold=False,
                align=PP_ALIGN.CENTER,
            )

    def _calculate_title_font_size(self, title: str) -> int:
        """
        Calculate appropriate font size for title based on length.
        
        Args:
            title: Title text
            
        Returns:
            Font size in points
        """
        length = len(title)
        if length <= 20:
            return 60
        elif length <= 40:
            return 48
        elif length <= 60:
            return 36
        else:
            return 28

    def _calculate_subtitle_font_size(self, subtitle: str) -> int:
        """
        Calculate appropriate font size for subtitle based on length.
        
        Args:
            subtitle: Subtitle text
            
        Returns:
            Font size in points
        """
        length = len(subtitle)
        if length <= 30:
            return 32
        elif length <= 60:
            return 28
        else:
            return 24

