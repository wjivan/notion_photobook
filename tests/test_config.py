"""
Tests for configuration module.
"""

import pytest
from pathlib import Path

from notion_photobook.config import PhotobookConfig, Layout, PaperSize


class TestLayout:
    """Test Layout enum."""
    
    def test_layout_values(self):
        """Test layout enum values."""
        assert Layout.PORTRAIT.value == "portrait"
        assert Layout.LANDSCAPE.value == "landscape"
    
    def test_layout_from_string(self):
        """Test creating layout from string."""
        assert Layout("portrait") == Layout.PORTRAIT
        assert Layout("landscape") == Layout.LANDSCAPE
    
    def test_invalid_layout(self):
        """Test invalid layout raises error."""
        with pytest.raises(ValueError):
            Layout("invalid")


class TestPaperSize:
    """Test PaperSize enum."""
    
    def test_paper_size_values(self):
        """Test paper size enum values."""
        assert PaperSize.A4.value == "A4"
        assert PaperSize.A3.value == "A3"
        assert PaperSize.A5.value == "A5"
        assert PaperSize.LETTER.value == "letter"
        assert PaperSize.LEGAL.value == "legal"
    
    def test_paper_size_from_string(self):
        """Test creating paper size from string."""
        assert PaperSize("A4") == PaperSize.A4
        assert PaperSize("letter") == PaperSize.LETTER
    
    def test_invalid_paper_size(self):
        """Test invalid paper size raises error."""
        with pytest.raises(ValueError):
            PaperSize("invalid")


class TestPhotobookConfig:
    """Test PhotobookConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PhotobookConfig()
        
        assert config.layout == Layout.LANDSCAPE
        assert config.paper_size == PaperSize.A4
        assert config.title_column == "Title"
        assert config.date_column == "Day"
        assert config.image_column == "Photos"
        assert config.text_column == "Text"
        assert config.title_font_size == 16
        assert config.text_font_size == 10
        assert config.margin_mm == 5
        assert config.image_padding == 5
        assert config.max_image_long_edge_px == 2400
        assert config.background_alpha == 0.3
        assert config.title_font == "Helvetica-Bold"
        assert config.text_font == "Helvetica"
        assert config.background_image is None
        assert config.cover_image is None
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = PhotobookConfig(
            layout=Layout.PORTRAIT,
            paper_size=PaperSize.A3,
            title_font_size=20,
            text_font_size=12,
            margin_mm=10,
            image_padding=8,
            max_image_long_edge_px=3000,
            background_alpha=0.5,
            title_font="Arial-Bold",
            text_font="Arial",
        )
        
        assert config.layout == Layout.PORTRAIT
        assert config.paper_size == PaperSize.A3
        assert config.title_font_size == 20
        assert config.text_font_size == 12
        assert config.margin_mm == 10
        assert config.image_padding == 8
        assert config.max_image_long_edge_px == 3000
        assert config.background_alpha == 0.5
        assert config.title_font == "Arial-Bold"
        assert config.text_font == "Arial"
    
    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "layout": "portrait",
            "paper_size": "A3",
            "title_font_size": 18,
            "text_font_size": 11,
            "background_image": "/path/to/bg.png",
            "cover_image": "/path/to/cover.jpg",
        }
        
        config = PhotobookConfig.from_dict(data)
        
        assert config.layout == Layout.PORTRAIT
        assert config.paper_size == PaperSize.A3
        assert config.title_font_size == 18
        assert config.text_font_size == 11
        assert config.background_image == Path("/path/to/bg.png")
        assert config.cover_image == Path("/path/to/cover.jpg")
    
    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = PhotobookConfig(
            layout=Layout.PORTRAIT,
            paper_size=PaperSize.A3,
            title_font_size=18,
        )
        
        data = config.to_dict()
        
        assert data["layout"] == "portrait"
        assert data["paper_size"] == "A3"
        assert data["title_font_size"] == 18
        assert data["text_font_size"] == 10  # default
        assert "background_image" not in data  # None values excluded
        assert "cover_image" not in data  # None values excluded
    
    def test_to_dict_with_paths(self):
        """Test converting config with paths to dictionary."""
        config = PhotobookConfig(
            background_image=Path("/path/to/bg.png"),
            cover_image=Path("/path/to/cover.jpg"),
        )
        
        data = config.to_dict()
        
        assert data["background_image"] == "/path/to/bg.png"
        assert data["cover_image"] == "/path/to/cover.jpg" 