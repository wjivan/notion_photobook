"""
Tests for core module.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from notion_photobook.core import NotionPhotobookGenerator, create_photobook
from notion_photobook.config import PhotobookConfig, Layout, PaperSize


class TestNotionPhotobookGenerator:
    """Test NotionPhotobookGenerator class."""
    
    def test_init_default_config(self):
        """Test initialization with default config."""
        generator = NotionPhotobookGenerator()
        assert generator.config is not None
        assert isinstance(generator.config, PhotobookConfig)
    
    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = PhotobookConfig(layout=Layout.PORTRAIT)
        generator = NotionPhotobookGenerator(config)
        assert generator.config == config
    
    def test_create_demo_data(self, tmp_path):
        """Test creating demo data."""
        generator = NotionPhotobookGenerator()
        demo_path = tmp_path / "demo.json"
        
        generator.create_demo_data(demo_path)
        
        assert demo_path.exists()
        
        with open(demo_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 3
        assert data[0]["Title"] == "First Day"
        assert data[0]["Day"] == "January 1, 2024"
        assert "demo1.jpg" in data[0]["Photos"]
    
    def test_generate_from_json(self, tmp_path):
        """Test generating photobook from JSON."""
        # Create test JSON
        test_entries = [
            {
                "Title": "Test Entry",
                "Day": "January 1, 2024",
                "Photos": "test1.jpg",
                "Text": "Test content"
            }
        ]
        
        json_path = tmp_path / "test.json"
        with open(json_path, 'w') as f:
            json.dump(test_entries, f)
        
        # Create image directory
        img_dir = tmp_path / "images"
        img_dir.mkdir()
        
        # Create a dummy image file
        (img_dir / "test1.jpg").touch()
        
        # Mock the renderer to avoid actual PDF generation
        generator = NotionPhotobookGenerator()
        generator.renderer.create_photobook = Mock()
        
        output_path = tmp_path / "output.pdf"
        generator.generate_from_json(json_path, output_path, img_dir)
        
        # Check that renderer was called
        generator.renderer.create_photobook.assert_called_once()
        args = generator.renderer.create_photobook.call_args
        assert args[0][0] == test_entries  # entries
        assert args[0][1] == output_path   # output_path
        assert args[0][2] == img_dir       # img_dir
    
    def test_generate_from_json_empty(self, tmp_path):
        """Test generating photobook from empty JSON."""
        json_path = tmp_path / "empty.json"
        with open(json_path, 'w') as f:
            json.dump([], f)
        
        generator = NotionPhotobookGenerator()
        output_path = tmp_path / "output.pdf"
        img_dir = tmp_path / "images"
        img_dir.mkdir()
        
        with pytest.raises(ValueError, match="No entries found"):
            generator.generate_from_json(json_path, output_path, img_dir)
    
    def test_generate_from_json_file_not_found(self, tmp_path):
        """Test generating photobook from non-existent JSON."""
        generator = NotionPhotobookGenerator()
        json_path = tmp_path / "nonexistent.json"
        output_path = tmp_path / "output.pdf"
        img_dir = tmp_path / "images"
        img_dir.mkdir()
        
        with pytest.raises(FileNotFoundError):
            generator.generate_from_json(json_path, output_path, img_dir)


class TestCreatePhotobook:
    """Test create_photobook convenience function."""
    
    @patch('notion_photobook.core.NotionPhotobookGenerator')
    def test_create_photobook(self, mock_generator_class, tmp_path):
        """Test create_photobook function."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        input_folder = tmp_path / "input"
        input_folder.mkdir()
        output_path = tmp_path / "output.pdf"
        
        create_photobook(
            input_folder=input_folder,
            output_path=output_path,
            layout="portrait",
            paper_size="A4"
        )
        
        # Check that generator was created with correct config
        mock_generator_class.assert_called_once()
        config = mock_generator_class.call_args[0][0]
        assert config.layout == Layout.PORTRAIT
        assert config.paper_size == PaperSize.A4
        
        # Check that generate_from_notion_export was called
        mock_generator.generate_from_notion_export.assert_called_once()
        args = mock_generator.generate_from_notion_export.call_args
        assert args[1]["input_folder"] == input_folder
        assert args[1]["output_path"] == output_path
        assert args[1]["downsample_images"] is True 