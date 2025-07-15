"""
Notion Photobook Generator

Convert Notion HTML exports into beautiful print-ready photobooks.
"""

__version__ = "0.1.0"
__author__ = "Notion Photobook Team"
__email__ = "contact@notion-photobook.dev"

from .core import NotionPhotobookGenerator
from .config import PhotobookConfig, Layout, PaperSize

__all__ = [
    "NotionPhotobookGenerator",
    "PhotobookConfig", 
    "Layout",
    "PaperSize",
    "__version__",
] 