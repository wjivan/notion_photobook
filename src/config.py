"""
Configuration and settings for the Notion Photobook Generator.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from pathlib import Path


class Layout(Enum):
    """Photobook layout options."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class PaperSize(Enum):
    """Standard paper sizes."""
    A4 = "A4"
    A3 = "A3"
    A5 = "A5"
    LETTER = "letter"
    LEGAL = "legal"


@dataclass
class PhotobookConfig:
    """Configuration for photobook generation."""
    
    # Layout settings
    layout: Layout = Layout.LANDSCAPE
    paper_size: PaperSize = PaperSize.A4
    
    # Column mappings (for flexibility)
    title_column: str = "Title"
    date_column: str = "Day"
    image_column: str = "Photos"
    text_column: str = "Text"
    
    # Styling
    title_font_size: int = 16
    text_font_size: int = 10
    margin_mm: int = 5
    image_padding: int = 5
    
    # Image processing
    max_image_long_edge_px: int = 2400
    
    # Background and cover
    background_image: Optional[Path] = None
    cover_image: Optional[Path] = None
    background_alpha: float = 0.3
    
    # Fonts
    title_font: str = "Helvetica-Bold"
    text_font: str = "Helvetica"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhotobookConfig":
        """Create config from dictionary."""
        # Handle enum conversions
        if "layout" in data:
            data["layout"] = Layout(data["layout"])
        if "paper_size" in data:
            data["paper_size"] = PaperSize(data["paper_size"])
        
        # Handle path conversions
        if "background_image" in data and data["background_image"]:
            data["background_image"] = Path(data["background_image"])
        if "cover_image" in data and data["cover_image"]:
            data["cover_image"] = Path(data["cover_image"])
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        data = {
            "layout": self.layout.value,
            "paper_size": self.paper_size.value,
            "title_column": self.title_column,
            "date_column": self.date_column,
            "image_column": self.image_column,
            "text_column": self.text_column,
            "title_font_size": self.title_font_size,
            "text_font_size": self.text_font_size,
            "margin_mm": self.margin_mm,
            "image_padding": self.image_padding,
            "max_image_long_edge_px": self.max_image_long_edge_px,
            "background_alpha": self.background_alpha,
            "title_font": self.title_font,
            "text_font": self.text_font,
        }
        
        if self.background_image:
            data["background_image"] = str(self.background_image)
        if self.cover_image:
            data["cover_image"] = str(self.cover_image)
        
        return data


# Default configurations
DEFAULT_CONFIG = PhotobookConfig()

PORTRAIT_A4_CONFIG = PhotobookConfig(
    layout=Layout.PORTRAIT,
    paper_size=PaperSize.A4,
    title_font_size=18,
    text_font_size=11,
)

LANDSCAPE_A4_CONFIG = PhotobookConfig(
    layout=Layout.LANDSCAPE,
    paper_size=PaperSize.A4,
    title_font_size=16,
    text_font_size=10,
) 