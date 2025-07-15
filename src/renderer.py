"""
PDF renderer for photobook generation.

Handles PDF creation using ReportLab with background images and text rendering.
"""

import gc
from functools import lru_cache
from typing import Dict, List, Optional, Any
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import A4, A3, A5, letter, legal, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from tqdm import tqdm

from .layout import LayoutEngine, ImageLayout, TextLayout


class BackgroundRenderer:
    """Handles background image rendering."""
    
    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
    
    @lru_cache(maxsize=1)
    def get_faded_background_reader(self, alpha: float = 0.3) -> Optional[ImageReader]:
        """
        Get faded background image reader.
        
        Args:
            alpha: Transparency level (0.0 to 1.0)
            
        Returns:
            ImageReader for faded background, or None if no background image
        """
        if not self.config.background_image or not self.config.background_image.exists():
            return None
        
        bg = Image.open(self.config.background_image).convert("RGB")
        white = Image.new("RGB", bg.size, "white")
        faded = Image.blend(white, bg, alpha)
        return ImageReader(faded)
    
    def draw_background(self, canvas_obj: canvas.Canvas, page_w: float, page_h: float) -> None:
        """Draw background on current page."""
        faded_bg = self.get_faded_background_reader(self.config.background_alpha)
        if faded_bg:
            canvas_obj.drawImage(faded_bg, 0, 0, width=page_w, height=page_h, mask='auto')


class CoverRenderer:
    """Handles cover page rendering."""
    
    def __init__(self, config):
        """Initialize with configuration."""
        self.config = config
    
    def draw_cover_page(self, canvas_obj: canvas.Canvas, page_w: float, page_h: float) -> None:
        """
        Draw cover page with full-bleed image.
        
        Args:
            canvas_obj: ReportLab canvas
            page_w: Page width
            page_h: Page height
        """
        if not self.config.cover_image or not self.config.cover_image.exists():
            # Create a simple text cover if no image
            canvas_obj.setFont("Helvetica-Bold", 24)
            canvas_obj.drawCentredString(page_w / 2, page_h / 2, "Photobook")
            canvas_obj.showPage()
            return
        
        hero = ImageReader(self.config.cover_image)
        canvas_obj.drawImage(hero, 0, 0, width=page_w, height=page_h, mask='auto')
        canvas_obj.showPage()


class PhotobookRenderer:
    """Main renderer for photobook generation."""
    
    def __init__(self, config):
        """Initialize renderer with configuration."""
        self.config = config
        self.layout_engine = LayoutEngine(config)
        self.background_renderer = BackgroundRenderer(config)
        self.cover_renderer = CoverRenderer(config)
        self.image_layout = ImageLayout(config)
        self.text_layout = TextLayout(config)
    
    def create_photobook(self, entries: List[Dict[str, Any]], output_path: Path, 
                        img_dir: Path) -> None:
        """
        Create photobook PDF from entries.
        
        Args:
            entries: List of diary entries
            output_path: Output PDF path
            img_dir: Directory containing images
        """
        # Get page dimensions
        page_w, page_h = self.layout_engine.get_page_size()
        margin = self.config.margin_mm * mm
        pane_w, pane_h = self.layout_engine.calculate_pane_dimensions(page_w, page_h, margin)
        
        # Create canvas
        c = canvas.Canvas(str(output_path), pagesize=(page_w, page_h))
        
        # Draw cover page
        self.cover_renderer.draw_cover_page(c, page_w, page_h)
        
        # Start first content page
        self.background_renderer.draw_background(c, page_w, page_h)
        
        # Layout parameters
        title_sz = self.config.title_font_size
        text_sz = self.config.text_font_size
        pad = self.config.image_padding
        img_pad = self.config.image_padding
        
        pane_idx = 0
        
        for idx, entry in enumerate(tqdm(entries, desc="Generating pages")):
            # Calculate pane position
            col = pane_idx % 2 if self.config.layout.value == "landscape" else 0
            
            if pane_idx and col == 0:
                c.showPage()
                self.background_renderer.draw_background(c, page_w, page_h)
            
            x0 = margin + col * (pane_w + margin) if self.config.layout.value == "landscape" else margin
            y0 = page_h - margin
            
            # Draw title
            day = entry.get(self.config.date_column, '').strip()
            title_text = entry.get(self.config.title_column, '').strip()
            full_title = f"{day} - {title_text}" if day and title_text else (day or title_text)
            
            c.setFont(self.config.title_font, title_sz)
            title_lines = self.text_layout.wrap_title(full_title, self.config.title_font, title_sz, pane_w)
            
            title_leading = title_sz * 1.2
            y_title = y0 - title_leading
            
            for line in title_lines:
                c.drawString(x0, y_title, line)
                y_title -= title_leading
            
            y_curr = y_title - title_leading * 0.5
            
            # Handle images
            photos = [p.strip() for p in entry.get(self.config.image_column, '').split(',') if p.strip()]
            if photos:
                txt = entry.get(self.config.text_column, '').strip()
                ph = (pane_h - title_sz - pad) if not txt else pane_h * 0.40
                
                # Load image readers
                img_readers = []
                for photo in photos:
                    img_path = img_dir / photo
                    if img_path.exists():
                        img_readers.append(ImageReader(img_path))
                
                if img_readers:
                    y_base = y_curr - ph
                    
                    # Ensure bottom margin is respected
                    if y_base < margin:
                        shift_up = margin - y_base
                        y_base += shift_up
                        y_curr += shift_up
                    
                    # Layout images based on count
                    n = len(img_readers)
                    if n == 1:
                        x_img, y_img, dw, dh = self.image_layout.layout_single_photo(
                            img_readers[0], pane_w, ph
                        )
                        c.drawImage(img_readers[0], x0 + x_img, y_base + y_img, 
                                   width=dw, height=dh, mask='auto')
                    
                    elif n == 2:
                        layouts = self.image_layout.layout_two_photos(
                            img_readers, pane_w, ph, img_pad
                        )
                        for layout in layouts:
                            c.drawImage(layout["reader"], x0 + layout["x"], 
                                       y_base + layout["y"], width=layout["w"], 
                                       height=layout["h"], mask='auto')
                    
                    elif n == 3:
                        layouts = self.image_layout.layout_three_photos(
                            img_readers, pane_w, ph, img_pad
                        )
                        for layout in layouts:
                            c.drawImage(layout["reader"], x0 + layout["x"], 
                                       y_base + layout["y"], width=layout["w"], 
                                       height=layout["h"], mask='auto')
                    
                    else:
                        # Use rectangle packing for 4+ images
                        slots = self.image_layout.pack_photos(photos, pane_w, ph, img_pad, img_dir)
                        
                        if slots:
                            cluster_h = max(s["y"] + s["h"] for s in slots)
                            y_offset = ph - cluster_h
                            
                            for slot in slots:
                                c.drawImage(slot["reader"], x0 + slot["x"], 
                                           y_base + y_offset + slot["y"], 
                                           width=slot["w"], height=slot["h"], 
                                           mask='auto')
                    
                    y_curr -= ph + pad
            
            # Handle text
            txt = entry.get(self.config.text_column, '').strip()
            if txt:
                c.setFont(self.config.text_font, text_sz)
                wrapped = self.text_layout.wrap_text_to_width(
                    txt, self.config.text_font, text_sz, pane_w - pad * 2
                )
                leading = text_sz * 1.2
                
                t = c.beginText(x0, y_curr)
                t.setFont(self.config.text_font, text_sz)
                t.setLeading(leading)
                t.textLine("")  # Blank line after photos
                
                i = 0
                while i < len(wrapped):
                    if t.getY() - margin < text_sz:
                        c.drawText(t)
                        pane_idx += 1
                        col = pane_idx % 2 if self.config.layout.value == "landscape" else 0
                        
                        if col == 0:
                            c.showPage()
                            self.background_renderer.draw_background(c, page_w, page_h)
                        
                        x_p = margin + col * (pane_w + margin) if self.config.layout.value == "landscape" else margin
                        y_p = page_h - margin - title_sz - pad
                        
                        t = c.beginText(x_p, y_p)
                        t.setFont(self.config.text_font, text_sz)
                        t.setLeading(leading)
                    
                    t.textLine(wrapped[i])
                    i += 1
                
                c.drawText(t)
                pane_idx += 1
            else:
                pane_idx += 1
        
        c.save()
        print(f"✅ Photobook saved to: {output_path}")
        print(f"📄 Total pages: ≈ {pane_idx // 2 + pane_idx % 2 if self.config.layout.value == 'landscape' else pane_idx}")
    
    def downsample_images(self, img_dir: Path) -> None:
        """Downsample images in directory to optimize memory usage."""
        self.image_layout.downsample_images(img_dir) 