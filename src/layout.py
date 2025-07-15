"""
Layout engine for photobook generation.

Handles rectangle packing, image positioning, and text layout.
"""

import os
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from PIL import Image
from reportlab.lib.utils import ImageReader
from rectpack import newPacker, PackingMode, MaxRectsBssf


class ImageLayout:
    """Handles image layout and positioning."""
    
    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
        self.max_long_edge_px = config.max_image_long_edge_px
    
    def downsample_images(self, img_dir: Path) -> None:
        """
        Resize images in directory to optimize memory usage.
        
        Args:
            img_dir: Directory containing images
        """
        for fname in os.listdir(img_dir):
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            
            path = img_dir / fname
            try:
                with Image.open(path) as im:
                    w, h = im.size
                    if max(w, h) <= self.max_long_edge_px:
                        continue  # already small enough
                    
                    scale = self.max_long_edge_px / max(w, h)
                    new_size = (int(w * scale), int(h * scale))
                    im = im.resize(new_size, Image.LANCZOS)
                    im.save(path, quality=90, optimize=True)
            except Exception as e:
                print(f"⚠️  Down-sample skipped for {fname}: {e}")
    
    def pack_photos(self, photo_paths: List[str], pane_w: float, pane_h: float, 
                   pad: int, img_dir: Path) -> List[Dict[str, Any]]:
        """
        Pack photos into a pane using rectangle packing algorithm.
        
        Args:
            photo_paths: List of image filenames
            pane_w: Width of the pane
            pane_h: Height of the pane
            pad: Padding between images
            img_dir: Directory containing images
            
        Returns:
            List of dictionaries with image layout info
        """
        max_long = min(pane_w, pane_h) * 0.6
        rects, readers = [], {}
        
        for photo_path in photo_paths:
            img_path = img_dir / photo_path
            if not img_path.exists():
                continue
                
            img = Image.open(img_path)
            w, h = img.size
            scale = min(max_long / max(w, h), 1.0)
            w_s, h_s = int(w * scale), int(h * scale)
            rects.append((w_s + pad, h_s + pad, photo_path))
            readers[photo_path] = ImageReader(img)
        
        if not rects:
            return []
        
        # Use rectpack for rectangle packing
        packer = newPacker(
            mode=PackingMode.Offline, 
            pack_algo=MaxRectsBssf,
            rotation=False
        )
        
        for rect in rects:
            packer.add_rect(*rect)
        
        packer.add_bin(pane_w, pane_h)
        packer.pack()
        
        out = []
        for bin_ in packer:
            for r in bin_:
                out.append({
                    "reader": readers[r.rid],
                    "x": r.x,
                    "y": r.y,
                    "w": r.width - pad,
                    "h": r.height - pad
                })
        
        return out
    
    def layout_single_photo(self, img_reader: ImageReader, pane_w: float, 
                           pane_h: float) -> Tuple[float, float, float, float]:
        """Layout a single photo to fill the pane proportionally."""
        iw, ih = img_reader.getSize()
        scale = min(pane_w / iw, pane_h / ih)
        dw, dh = iw * scale, ih * scale
        x_img = (pane_w - dw) / 2
        y_img = (pane_h - dh) / 2
        return x_img, y_img, dw, dh
    
    def layout_two_photos(self, img_readers: List[ImageReader], pane_w: float, 
                         pane_h: float, img_pad: int) -> List[Dict[str, Any]]:
        """Layout two photos in equal-width columns."""
        col_w = (pane_w - img_pad) / 2
        layouts = []
        
        for idx, reader in enumerate(img_readers):
            iw, ih = reader.getSize()
            scale = min(col_w / iw, pane_h / ih)
            dw, dh = iw * scale, ih * scale
            x_img = idx * (col_w + img_pad) + (col_w - dw) / 2
            y_img = (pane_h - dh) / 2
            
            layouts.append({
                "reader": reader,
                "x": x_img,
                "y": y_img,
                "w": dw,
                "h": dh
            })
        
        return layouts
    
    def layout_three_photos(self, img_readers: List[ImageReader], pane_w: float, 
                           pane_h: float, img_pad: int) -> List[Dict[str, Any]]:
        """Layout three photos: two columns, two rows."""
        col_w = (pane_w - img_pad) / 2
        row_h = (pane_h - img_pad) / 2
        layouts = []
        
        # Top row: two images
        for idx in range(2):
            iw, ih = img_readers[idx].getSize()
            scale = min(col_w / iw, row_h / ih)
            dw, dh = iw * scale, ih * scale
            x_img = idx * (col_w + img_pad) + (col_w - dw) / 2
            y_img = row_h + img_pad + (row_h - dh) / 2
            
            layouts.append({
                "reader": img_readers[idx],
                "x": x_img,
                "y": y_img,
                "w": dw,
                "h": dh
            })
        
        # Bottom row: single centred image
        iw, ih = img_readers[2].getSize()
        scale = min(col_w / iw, row_h / ih)
        dw, dh = iw * scale, ih * scale
        x_img = (pane_w - dw) / 2
        y_img = (row_h - dh) / 2
        
        layouts.append({
            "reader": img_readers[2],
            "x": x_img,
            "y": y_img,
            "w": dw,
            "h": dh
        })
        
        return layouts


class TextLayout:
    """Handles text layout and wrapping."""
    
    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
    
    def wrap_text_to_width(self, text: str, font_name: str, font_size: int, 
                          max_w: float) -> List[str]:
        """
        Wrap text to fit within specified width.
        
        Args:
            text: Text to wrap
            font_name: Font name
            font_size: Font size
            max_w: Maximum width
            
        Returns:
            List of wrapped lines
        """
        from reportlab.pdfbase import pdfmetrics
        
        def wrap_para(para: str) -> List[str]:
            line, out = "", []
            for word in para.split():
                test = f"{line} {word}".strip()
                if pdfmetrics.stringWidth(test, font_name, font_size) <= max_w:
                    line = test
                else:
                    out.append(line)
                    line = word
            if line:
                out.append(line)
            return out
        
        lines = []
        for para in text.split("\n\n"):
            para = para.strip()
            if not para:
                lines.append("")
                continue
            lines.extend(wrap_para(para))
            lines.append("")
        
        if lines and lines[-1] == "":
            lines.pop()
        
        return lines
    
    def wrap_title(self, title: str, font_name: str, font_size: int, 
                   max_w: float) -> List[str]:
        """Wrap title text to fit within specified width."""
        from reportlab.pdfbase import pdfmetrics
        
        title_lines = []
        if not title:
            return title_lines
        
        words = title.split()
        curr = ''
        for word in words:
            test = f"{curr} {word}".strip()
            if pdfmetrics.stringWidth(test, font_name, font_size) <= max_w:
                curr = test
            else:
                title_lines.append(curr)
                curr = word
        
        if curr:
            title_lines.append(curr)
        
        return title_lines


class LayoutEngine:
    """Main layout engine that coordinates image and text layout."""
    
    def __init__(self, config):
        """Initialize layout engine with configuration."""
        self.config = config
        self.image_layout = ImageLayout(config)
        self.text_layout = TextLayout(config)
    
    def get_page_size(self) -> Tuple[float, float]:
        """Get page size based on configuration."""
        from reportlab.lib.pagesizes import A4, A3, A5, letter, legal, landscape
        
        size_map = {
            "A4": A4,
            "A3": A3,
            "A5": A5,
            "letter": letter,
            "legal": legal,
        }
        
        pagesize = size_map.get(self.config.paper_size.value, A4)
        
        if self.config.layout.value == "landscape":
            return landscape(pagesize)
        else:
            return pagesize
    
    def calculate_pane_dimensions(self, page_w: float, page_h: float, 
                                 margin: float) -> Tuple[float, float]:
        """Calculate pane dimensions based on layout."""
        if self.config.layout.value == "landscape":
            # Two panes side by side
            pane_w = (page_w - 3 * margin) / 2
            pane_h = page_h - 2 * margin
        else:
            # Single pane
            pane_w = page_w - 2 * margin
            pane_h = page_h - 2 * margin
        
        return pane_w, pane_h 