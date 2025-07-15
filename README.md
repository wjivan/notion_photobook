# Notion Photobook Generator 📚

Convert Notion HTML exports into beautiful print-ready photobooks with automatic image layout and text formatting.

## ✨ Features

- **Smart Image Layout**: Uses rectangle packing algorithms to efficiently arrange multiple images
- **Flexible Layouts**: Support for portrait and landscape orientations
- **Multiple Paper Sizes**: A4, A3, A5, Letter, and Legal sizes
- **Automatic Text Wrapping**: Intelligent text layout that adapts to available space
- **Background Support**: Optional background images with transparency control
- **Cover Pages**: Full-bleed cover page support
- **Image Optimization**: Automatic image downsampling for memory efficiency
- **Customizable Columns**: Flexible column mapping for different Notion structures

## 🚀 Quick Start

### Installation

```bash
# Or install from source
git clone https://github.com/yourusername/notion-photobook.git
cd notion-photobook
pip install -e .
```

**Note:** If you install with `pip install --user`, the `photobookgen` command may not be in your PATH. 

After installation, you can:
1. Run `python scripts/post_install.py` to automatically configure your PATH
2. Or run `photobookgen setup` for manual instructions
3. Or add the script directory to your PATH manually

### Basic Usage

1. **Export from Notion**: Export your Notion workspace as HTML
2. **Generate Photobook**: Run the tool on your export folder

```bash
# Basic usage
photobookgen ./my_notion_export ./book.pdf

# With custom layout
photobookgen ./my_notion_export ./book.pdf --layout portrait --size A4

# With custom image directory
photobookgen ./my_notion_export ./book.pdf --img-dir ./photos
```

## 📖 How to Export from Notion

1. **In Notion**: Go to your workspace settings
2. **Export**: Select "Export all workspace content"
3. **Format**: Choose "HTML" format
4. **Download**: Save the ZIP file and extract it
5. **Use**: Point the tool to the extracted folder

## 🎯 Command Line Interface

### Main Command

```bash
photobookgen <input_folder> <output_pdf> [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--layout, -l` | Page layout (`portrait` or `landscape`) | `landscape` |
| `--size, -s` | Paper size (`A4`, `A3`, `A5`, `letter`, `legal`) | `A4` |
| `--img-dir, -i` | Directory containing images | Input folder |
| `--max-date, -d` | Maximum date to include (YYYY-MM-DD) | None |
| `--title-column` | Column name for entry titles | `Title` |
| `--image-column` | Column name for image filenames | `Photos` |
| `--text-column` | Column name for entry text | `Text` |
| `--date-column` | Column name for entry dates | `Day` |
| `--no-downsample` | Skip image downsampling | False |
| `--verbose, -v` | Enable verbose output | False |

### Examples

```bash
# Generate a portrait A4 photobook
photobookgen ./notion_export ./my_book.pdf --layout portrait --size A4

# Use custom column names
photobookgen ./notion_export ./my_book.pdf \
  --title-column "Entry Title" \
  --image-column "Images" \
  --text-column "Content"

# Include only entries up to a certain date
photobookgen ./notion_export ./my_book.pdf --max-date 2024-06-30

# Skip image optimization for faster processing
photobookgen ./notion_export ./my_book.pdf --no-downsample
```

### Additional Commands

#### Demo Mode

Generate a sample photobook to test the tool:

```bash
photobookgen demo ./demo_book.pdf --layout landscape
```

#### Parse Only

Extract data from Notion export without generating PDF:

```bash
photobookgen parse ./notion_export ./entries.json
photobookgen parse ./notion_export ./entries.json --test-json ./test_entries.json
```

#### Version Info

```bash
photobookgen version
```

#### Setup Help

Get help with PATH configuration:

```bash
photobookgen setup
```

## 📁 Expected Notion Structure

The tool expects your Notion export to have a table structure with these columns:

| Column | Purpose | Example |
|--------|---------|---------|
| `Title` | Entry title | "My First Day" |
| `Day` | Date | "January 1, 2024" |
| `Photos` | Image filenames (comma-separated) | "photo1.jpg,photo2.png" |
| `Text` | Entry content | "Today was amazing..." |

### Custom Column Names

You can customize column names using the `--title-column`, `--image-column`, etc. options.

## 🎨 Layout Features

### Image Layout

- **Single Image**: Fills available space proportionally
- **Two Images**: Equal-width columns
- **Three Images**: 2+1 grid layout
- **4+ Images**: Rectangle packing algorithm for optimal space usage

### Text Layout

- Automatic text wrapping to fit page width
- Paragraph preservation
- Intelligent spacing and margins
- Font size adaptation

### Page Layout

- **Landscape**: Two entries per page (side by side)
- **Portrait**: Single entry per page
- Automatic page breaks for long content
- Consistent margins and spacing

## 🔧 Advanced Usage

### Python API

```python
from notion_photobook import NotionPhotobookGenerator, PhotobookConfig, Layout, PaperSize
from pathlib import Path

# Create configuration
config = PhotobookConfig(
    layout=Layout.PORTRAIT,
    paper_size=PaperSize.A4,
    title_font_size=18,
    text_font_size=11,
)

# Generate photobook
generator = NotionPhotobookGenerator(config)
generator.generate_from_notion_export(
    input_folder=Path("./notion_export"),
    output_path=Path("./book.pdf"),
    img_dir=Path("./images"),
    max_date=datetime(2024, 6, 30)
)
```

### Custom Configuration

```python
from notion_photobook import PhotobookConfig, Layout, PaperSize

config = PhotobookConfig(
    layout=Layout.LANDSCAPE,
    paper_size=PaperSize.A3,
    title_font_size=20,
    text_font_size=12,
    margin_mm=10,
    image_padding=8,
    max_image_long_edge_px=3000,
    background_image=Path("./background.png"),
    cover_image=Path("./cover.jpg"),
    background_alpha=0.2,
)
```

## 🧪 Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=notion_photobook
```

## 📋 Requirements

- Python 3.8+
- ReportLab (PDF generation)
- Pillow (image processing)
- rectpack (rectangle packing)
- BeautifulSoup4 (HTML parsing)
- Typer (CLI framework)
- Rich (pretty output)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ReportLab](https://www.reportlab.com/) for PDF generation
- [rectpack](https://github.com/secnot/rectpack) for rectangle packing algorithms
- [Typer](https://typer.tiangolo.com/) for the CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/notion-photobook/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/notion-photobook/discussions)
- **Email**: your.email@example.com

---

**Made with ❤️ for the Notion community** 