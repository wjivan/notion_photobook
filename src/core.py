"""
Core photobook generator module.

Main class that orchestrates the entire photobook generation process.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .config import PhotobookConfig, Layout, PaperSize
from .parser import NotionParser, parse_notion_export
from .renderer import PhotobookRenderer


class NotionPhotobookGenerator:
    """
    Main class for generating photobooks from Notion exports.
    
    This class orchestrates the entire process:
    1. Parsing Notion HTML exports
    2. Processing images and text
    3. Generating PDF photobooks
    """
    
    def __init__(self, config: Optional[PhotobookConfig] = None):
        """
        Initialize the photobook generator.
        
        Args:
            config: Configuration object, uses default if None
        """
        self.config = config or PhotobookConfig()
        self.renderer = PhotobookRenderer(self.config)
    
    def generate_from_notion_export(self, 
                                  input_folder: Path,
                                  output_path: Path,
                                  img_dir: Optional[Path] = None,
                                  max_date: Optional[datetime] = None,
                                  downsample_images: bool = True) -> None:
        """
        Generate photobook directly from Notion HTML export.
        
        Args:
            input_folder: Path to Notion HTML export folder
            output_path: Output PDF path
            img_dir: Directory containing images (defaults to input_folder)
            max_date: Optional maximum date to include
            downsample_images: Whether to downsample images for optimization
        """
        print(f"📖 Parsing Notion export from: {input_folder}")
        
        # Parse Notion export
        parser = NotionParser(input_folder)
        entries = parser.parse(max_date=max_date)
        
        if not entries:
            raise ValueError("No entries found in Notion export")
        
        print(f"📝 Found {len(entries)} entries")
        
        # Use input folder as image directory if not specified
        if img_dir is None:
            img_dir = input_folder
        
        # Generate photobook
        self.generate_from_entries(entries, output_path, img_dir, downsample_images)
    
    def generate_from_json(self, 
                          json_path: Path,
                          output_path: Path,
                          img_dir: Path,
                          downsample_images: bool = True) -> None:
        """
        Generate photobook from JSON file.
        
        Args:
            json_path: Path to JSON file with entries
            output_path: Output PDF path
            img_dir: Directory containing images
            downsample_images: Whether to downsample images for optimization
        """
        print(f"📖 Loading entries from: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        if not entries:
            raise ValueError("No entries found in JSON file")
        
        print(f"📝 Loaded {len(entries)} entries")
        
        self.generate_from_entries(entries, output_path, img_dir, downsample_images)
    
    def generate_from_entries(self, 
                             entries: List[Dict[str, Any]],
                             output_path: Path,
                             img_dir: Path,
                             downsample_images: bool = True) -> None:
        """
        Generate photobook from list of entries.
        
        Args:
            entries: List of diary entries
            output_path: Output PDF path
            img_dir: Directory containing images
            downsample_images: Whether to downsample images for optimization
        """
        print(f"🎨 Generating photobook...")
        print(f"   Layout: {self.config.layout.value}")
        print(f"   Paper size: {self.config.paper_size.value}")
        print(f"   Images directory: {img_dir}")
        
        # Downsample images if requested
        if downsample_images:
            print("🖼️  Downsampling images for optimization...")
            self.renderer.downsample_images(img_dir)
        
        # Create photobook
        self.renderer.create_photobook(entries, output_path, img_dir)
    
    def parse_and_save_json(self, 
                           input_folder: Path,
                           output_json: Path,
                           test_json: Optional[Path] = None,
                           max_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Parse Notion export and save to JSON files.
        
        Args:
            input_folder: Path to Notion HTML export folder
            output_json: Path to save full JSON output
            test_json: Optional path to save test JSON output
            max_date: Optional maximum date to include
            
        Returns:
            List of parsed entries
        """
        return parse_notion_export(
            input_folder=input_folder,
            output_json=output_json,
            test_json=test_json,
            max_date=max_date
        )
    
    def create_demo_data(self, output_path: Path) -> None:
        """
        Create demo data for testing.
        
        Args:
            output_path: Path to save demo JSON
        """
        demo_entries = [
            {
                "Title": "First Day",
                "Day": "January 1, 2024",
                "Photos": "demo1.jpg,demo2.jpg",
                "Text": "This is a sample entry for testing the photobook generator. It contains some text to demonstrate how the layout works with multiple paragraphs.\n\nThis is a second paragraph to show text wrapping and spacing."
            },
            {
                "Title": "Second Day",
                "Day": "January 2, 2024", 
                "Photos": "demo3.jpg",
                "Text": "Another sample entry with just one photo and some text content."
            },
            {
                "Title": "Third Day",
                "Day": "January 3, 2024",
                "Photos": "demo4.jpg,demo5.jpg,demo6.jpg",
                "Text": "This entry has three photos to test the three-photo layout algorithm."
            }
        ]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(demo_entries, f, ensure_ascii=False, indent=2)
        
        print(f"📝 Demo data saved to: {output_path}")


def create_photobook(input_folder: Path,
                    output_path: Path,
                    img_dir: Optional[Path] = None,
                    layout: str = "landscape",
                    paper_size: str = "A4",
                    max_date: Optional[datetime] = None,
                    downsample_images: bool = True) -> None:
    """
    Convenience function to create a photobook.
    
    Args:
        input_folder: Path to Notion HTML export folder
        output_path: Output PDF path
        img_dir: Directory containing images (defaults to input_folder)
        layout: Layout type ("portrait" or "landscape")
        paper_size: Paper size ("A4", "A3", "A5", "letter", "legal")
        max_date: Optional maximum date to include
        downsample_images: Whether to downsample images for optimization
    """
    config = PhotobookConfig(
        layout=Layout(layout),
        paper_size=PaperSize(paper_size)
    )
    
    generator = NotionPhotobookGenerator(config)
    generator.generate_from_notion_export(
        input_folder=input_folder,
        output_path=output_path,
        img_dir=img_dir,
        max_date=max_date,
        downsample_images=downsample_images
    ) 