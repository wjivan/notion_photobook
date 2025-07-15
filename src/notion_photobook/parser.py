"""
Parser for Notion HTML exports.

Extracts diary entries, images, and text from Notion HTML export files.
"""

import json
import os
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from rich.console import Console

# Rich console for consistent output
console = Console()


class NotionParser:
    """Parser for Notion HTML exports."""
    
    def __init__(self, input_folder: Path):
        """Initialize parser with input folder path."""
        self.input_folder = Path(input_folder)
        self.entries: List[Dict[str, Any]] = []
    
    def strip_emojis(self, text: str) -> str:
        """Remove emoji characters from text."""
        out = []
        for ch in text:
            cat = unicodedata.category(ch)
            if cat.startswith('So') or cat == 'Mn':
                continue
            out.append(ch)
        return ''.join(out)
    
    def find_main_html_file(self) -> Optional[Path]:
        """Find the main HTML file in the export folder."""
        html_files = list(self.input_folder.glob("*.html"))
        if not html_files:
            return None
        
        # Prefer files that look like main exports (containing table structures)
        for html_file in html_files:
            try:
                with open(html_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "table" in content and "cell-title" in content:
                        return html_file
            except Exception:
                continue
        
        # Fallback to first HTML file
        return html_files[0]
    
    def parse_table_entries(self, html_file: Path) -> List[Dict[str, Any]]:
        """Parse table entries from main HTML file."""
        with open(html_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        
        entries = []
        table = soup.find("table")
        if not table:
            console.print(f"⚠️  No table found in {html_file}")
            return entries
        
        # Try different possible CSS class patterns for Notion exports
        title_cell_classes = ["cell-title", "cell-title-text", "title-cell"]
        date_cell_classes = ["cell-DUXv", "cell-date", "date-cell", "cell-day"]
        
        for row in table.find_all("tr"):
            # Try to find title cell with different class patterns
            title_cell = None
            for class_name in title_cell_classes:
                title_cell = row.find("td", class_=class_name)
                if title_cell:
                    break
            
            # Try to find date cell with different class patterns
            date_cell = None
            for class_name in date_cell_classes:
                date_cell = row.find("td", class_=class_name)
                if date_cell:
                    break
            
            if title_cell and date_cell:
                link = title_cell.find("a")
                if link and link.get("href"):
                    href = link.get("href")
                    title = link.get_text(strip=True)
                    date = date_cell.get_text(strip=True).replace("@", "")
                    
                    # Decode URL-encoded href and build full path
                    relpath = unquote(href)
                    full_path = self.input_folder / relpath
                    
                    entries.append({
                        "title": title,
                        "date": date,
                        "filepath": full_path
                    })
        
        if not entries:
            console.print(f"⚠️  No entries found in table. This might not be a valid Notion export.")
            console.print(f"   Expected CSS classes: {title_cell_classes} for titles, {date_cell_classes} for dates")
        
        return entries
    
    def parse_entry_page(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse individual entry page and extract content."""
        try:
            with open(entry["filepath"], "r", encoding="utf-8") as f:
                page = BeautifulSoup(f, "html.parser")
            
            # Extract properties (photos, food, etc.)
            photos = []
            food = []
            props = page.find("table", class_="properties")
            
            if props:
                for row in props.find_all("tr"):
                    th = row.find("th")
                    td = row.find("td")
                    if not th or not td:
                        continue
                    
                    key = th.get_text(strip=True)
                    if key == "Photos":
                        for a in td.find_all("a", href=True):
                            photos.append(os.path.basename(unquote(a["href"])))
                    elif key == "Food":
                        for span in td.find_all("span", class_="selected-value"):
                            food.append(span.get_text(strip=True))
            
            # Extract body text
            body = page.find("div", class_="page-body")
            if body:
                paras = [p.get_text(strip=True) for p in body.find_all("p")]
                paras = [p for p in paras if p]
                text = "\n\n".join(paras)
            else:
                text = page.get_text(separator="\n", strip=True)
            
            return {
                "Title": self.strip_emojis(entry["title"]),
                "Day": entry["date"],
                "Photos": ",".join(photos),
                "Food": ",".join(food),
                "Text": self.strip_emojis(text)
            }
            
        except Exception as e:
            console.print(f"Failed to read {entry['filepath']}: {e}")
            return None
    
    def _parse_day(self, day_str: str) -> datetime:
        """Parse date string to datetime object."""
        try:
            return datetime.strptime(day_str, "%B %d, %Y")
        except Exception:
            return datetime.max
    
    def parse(self, max_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Parse the entire Notion export and return structured data."""
        # Find main HTML file
        main_html = self.find_main_html_file()
        if not main_html:
            raise FileNotFoundError(f"No main HTML file found in {self.input_folder}")
        
        # Parse table entries
        table_entries = self.parse_table_entries(main_html)
        
        # Parse each entry page
        records = []
        for entry in table_entries:
            record = self.parse_entry_page(entry)
            if record:
                records.append(record)
        
        # Sort by date
        records.sort(key=lambda r: self._parse_day(r.get("Day", "")))
        
        # Filter by max date if specified
        if max_date:
            records = [r for r in records if self._parse_day(r.get("Day", "")) <= max_date]
        
        return records
    
    def save_json(self, records: List[Dict[str, Any]], output_path: Path) -> None:
        """Save parsed records to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    
    def create_test_data(self, records: List[Dict[str, Any]], output_path: Path, 
                        num_samples: int = 10) -> None:
        """Create a smaller test dataset for development."""
        if len(records) <= num_samples * 2:
            test_records = records
        else:
            test_records = records[:num_samples] + records[-num_samples:]
        
        self.save_json(test_records, output_path)


def parse_notion_export(input_folder: Path, output_json: Optional[Path] = None,
                       test_json: Optional[Path] = None,
                       max_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to parse a Notion export.
    
    Args:
        input_folder: Path to Notion HTML export folder
        output_json: Optional path to save full JSON output
        test_json: Optional path to save test JSON output
        max_date: Optional maximum date to include
    
    Returns:
        List of parsed diary entries
    """
    parser = NotionParser(input_folder)
    records = parser.parse(max_date=max_date)
    
    if output_json:
        parser.save_json(records, output_json)
        console.print(f"Saved {len(records)} entries to {output_json}")
    
    if test_json:
        parser.create_test_data(records, test_json)
        console.print(f"Saved test data to {test_json}")
    
    return records 