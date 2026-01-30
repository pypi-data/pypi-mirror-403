"""Quote layout renderer."""

from typing import Any, Dict

from pptx.enum.text import PP_ALIGN
from pptx.slide import Slide
from pptx.presentation import Presentation
from pptx.util import Inches, Pt

from slidegen.layouts.base import BaseLayoutRenderer


class QuoteLayoutRenderer(BaseLayoutRenderer):
    """Renderer for quote slide layout."""

    def render(
        self, slide: Slide, data: Dict[str, Any], presentation: Presentation
    ) -> None:
        """
        Render a quote slide.
        
        Args:
            slide: The slide to render to
            data: Slide data with 'quote' field containing 'text' and optional 'attribution'
            presentation: The parent presentation
        """
        quote_data = data.get("quote", {})
        quote_text = quote_data.get("text", "")
        attribution = quote_data.get("attribution", "")

        if not quote_text:
            return

        # Calculate font size based on quote length
        quote_font_size = self._calculate_quote_font_size(quote_text)

        # Quote positioning (centered, upper portion)
        slide_width = self.SLIDE_WIDTH
        slide_height = self.SLIDE_HEIGHT
        quote_width = slide_width - (2 * self.MARGIN)
        quote_left = self.MARGIN
        quote_top = slide_height * 0.25  # Upper third

        # Add quote text
        self.add_text_box(
            slide=slide,
            left=quote_left,
            top=quote_top,
            width=quote_width,
            height=Inches(2.0),
            text=quote_text,
            font_size=quote_font_size,
            bold=True,
            align=PP_ALIGN.CENTER,
        )

        # Add attribution if provided
        if attribution:
            attribution_top = quote_top + Inches(2.5)
            attribution_font_size = max(18, quote_font_size - 8)
            
            self.add_text_box(
                slide=slide,
                left=quote_left,
                top=attribution_top,
                width=quote_width,
                height=Inches(0.5),
                text=f"— {attribution}",
                font_size=attribution_font_size,
                bold=False,
                align=PP_ALIGN.CENTER,
            )

    def _calculate_quote_font_size(self, quote_text: str) -> int:
        """
        Calculate appropriate font size for quote based on length.
        
        Args:
            quote_text: Quote text
            
        Returns:
            Font size in points
        """
        length = len(quote_text)
        if length <= 50:
            return 44
        elif length <= 100:
            return 36
        elif length <= 200:
            return 28
        else:
            return 24

