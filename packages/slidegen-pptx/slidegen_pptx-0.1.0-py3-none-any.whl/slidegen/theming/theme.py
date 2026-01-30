"""Theme management for slide generation."""

from pathlib import Path
from typing import Dict, Optional

from pptx import Presentation
from pptx.util import RGBColor


class Theme:
    """Theme configuration for slide styling."""

    def __init__(
        self,
        name: str = "default",
        background_color: Optional[str] = None,
        text_color: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        font_family: Optional[str] = None,
        font_size: Optional[int] = None,
    ):
        """
        Initialize a theme.
        
        Args:
            name: Theme name
            background_color: Background color (hex format, e.g., "#FFFFFF")
            text_color: Text color (hex format)
            primary_color: Primary accent color (hex format)
            secondary_color: Secondary accent color (hex format)
            font_family: Font family name
            font_size: Default font size in points
        """
        self.name = name
        self.background_color = background_color
        self.text_color = text_color
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.font_family = font_family
        self.font_size = font_size

    def get_background_rgb(self) -> Optional[RGBColor]:
        """Get background color as RGBColor object."""
        if self.background_color:
            return self._hex_to_rgb(self.background_color)
        return None

    def get_text_rgb(self) -> Optional[RGBColor]:
        """Get text color as RGBColor object."""
        if self.text_color:
            return self._hex_to_rgb(self.text_color)
        return None

    def get_primary_rgb(self) -> Optional[RGBColor]:
        """Get primary color as RGBColor object."""
        if self.primary_color:
            return self._hex_to_rgb(self.primary_color)
        return None

    def get_secondary_rgb(self) -> Optional[RGBColor]:
        """Get secondary color as RGBColor object."""
        if self.secondary_color:
            return self._hex_to_rgb(self.secondary_color)
        return None

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> RGBColor:
        """
        Convert hex color string to RGBColor.
        
        Args:
            hex_color: Hex color string (e.g., "#FF0000")
            
        Returns:
            RGBColor object
        """
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return RGBColor(r, g, b)

    @classmethod
    def default(cls) -> "Theme":
        """Get default theme."""
        return cls(
            name="default",
            background_color="#FFFFFF",
            text_color="#000000",
            primary_color="#0078D4",  # Microsoft blue
            secondary_color="#00BCF2",  # Light blue
            font_family="Calibri",
            font_size=18,
        )

    @classmethod
    def corporate(cls) -> "Theme":
        """Get corporate theme."""
        return cls(
            name="corporate",
            background_color="#FFFFFF",
            text_color="#1F1F1F",
            primary_color="#1E3A8A",  # Dark blue
            secondary_color="#3B82F6",  # Blue
            font_family="Calibri",
            font_size=18,
        )

    @classmethod
    def dark(cls) -> "Theme":
        """Get dark theme."""
        return cls(
            name="dark",
            background_color="#1F1F1F",
            text_color="#FFFFFF",
            primary_color="#60A5FA",  # Light blue
            secondary_color="#34D399",  # Green
            font_family="Calibri",
            font_size=18,
        )


def load_theme(theme_path: Optional[str] = None, theme_name: Optional[str] = None) -> Theme:
    """
    Load a theme from a PowerPoint template file or by name.
    
    Args:
        theme_path: Path to PowerPoint template file (.pptx)
        theme_name: Name of built-in theme (default, corporate, dark)
        
    Returns:
        Theme object
        
    Raises:
        FileNotFoundError: If theme_path is provided but file doesn't exist
        ValueError: If theme_name is provided but not recognized
    """
    if theme_path:
        path = Path(theme_path)
        if not path.exists():
            raise FileNotFoundError(f"Theme file not found: {theme_path}")
        
        # Load theme from PowerPoint template
        # For now, return default theme
        # Full implementation would extract colors and fonts from template
        return Theme.default()
    
    if theme_name:
        theme_map: Dict[str, Theme] = {
            "default": Theme.default(),
            "corporate": Theme.corporate(),
            "dark": Theme.dark(),
        }
        
        if theme_name not in theme_map:
            raise ValueError(f"Unknown theme name: {theme_name}. Available: {list(theme_map.keys())}")
        
        return theme_map[theme_name]
    
    # Default to default theme
    return Theme.default()

