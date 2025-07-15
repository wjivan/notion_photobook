"""
Command-line interface for Notion Photobook Generator.

Provides a user-friendly CLI for generating photobooks from Notion exports.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from .core import NotionPhotobookGenerator
from .config import PhotobookConfig, Layout, PaperSize

# Create Typer app
app = typer.Typer(
    name="photobookgen",
    help="Convert Notion HTML exports into beautiful print-ready photobooks",
    add_completion=False,
)

# Rich console for pretty output
console = Console()


def check_path_setup():
    """Check if the script is properly accessible and provide helpful guidance."""
    script_name = "photobookgen"
    
    # Check if we can find the script in PATH
    import shutil
    if shutil.which(script_name) is None:
        # Try to find where pip installed it
        import site
        user_site = site.getusersitepackages()
        if user_site:
            script_dir = Path(user_site).parent / "bin"
            if (script_dir / script_name).exists():
                console.print(f"\n⚠️  [yellow]Note:[/yellow] The '{script_name}' command is installed but not in your PATH.")
                console.print(f"   Script location: {script_dir}")
                console.print(f"   To add to PATH, run: [bold]export PATH=\"{script_dir}:$PATH\"[/bold]")
                console.print(f"   Or add to your shell config file (~/.zshrc, ~/.bashrc, etc.)")
                console.print(f"   Then restart your terminal or run: [bold]source ~/.zshrc[/bold]\n")


def validate_input_folder(input_folder: Path) -> None:
    """Validate that input folder exists and contains HTML files."""
    if not input_folder.exists():
        raise typer.BadParameter(f"Input folder does not exist: {input_folder}")
    
    if not input_folder.is_dir():
        raise typer.BadParameter(f"Input path is not a directory: {input_folder}")
    
    html_files = list(input_folder.glob("*.html"))
    if not html_files:
        raise typer.BadParameter(f"No HTML files found in: {input_folder}")


def validate_img_dir(img_dir: Optional[Path]) -> Optional[Path]:
    """Validate image directory if provided."""
    if img_dir is None:
        return None
    
    if not img_dir.exists():
        raise typer.BadParameter(f"Image directory does not exist: {img_dir}")
    
    if not img_dir.is_dir():
        raise typer.BadParameter(f"Image path is not a directory: {img_dir}")
    
    return img_dir


def parse_date(date_str: str) -> datetime:
    """Parse date string in format YYYY-MM-DD."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise typer.BadParameter(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


@app.command()
def main(
    input_folder: Path = typer.Argument(
        ...,
        help="Path to Notion HTML export folder",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output_path: Path = typer.Argument(
        ...,
        help="Output PDF path",
        resolve_path=True,
    ),
    layout: Layout = typer.Option(
        Layout.LANDSCAPE,
        "--layout",
        "-l",
        help="Page layout (portrait or landscape)",
        case_sensitive=False,
    ),
    paper_size: PaperSize = typer.Option(
        PaperSize.A4,
        "--size",
        "-s",
        help="Paper size (A4, A3, A5, letter, legal)",
        case_sensitive=False,
    ),
    img_dir: Optional[Path] = typer.Option(
        None,
        "--img-dir",
        "-i",
        help="Directory containing images (defaults to input folder)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    max_date: Optional[str] = typer.Option(
        None,
        "--max-date",
        "-d",
        help="Maximum date to include (YYYY-MM-DD format)",
    ),
    title_column: str = typer.Option(
        "Title",
        "--title-column",
        help="Column name for entry titles",
    ),
    image_column: str = typer.Option(
        "Photos",
        "--image-column",
        help="Column name for image filenames",
    ),
    text_column: str = typer.Option(
        "Text",
        "--text-column",
        help="Column name for entry text",
    ),
    date_column: str = typer.Option(
        "Day",
        "--date-column",
        help="Column name for entry dates",
    ),
    no_downsample: bool = typer.Option(
        False,
        "--no-downsample",
        help="Skip image downsampling (faster but uses more memory)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Generate a photobook from Notion HTML export.
    
    This tool converts a Notion HTML export into a beautiful print-ready photobook PDF.
    It uses a table structure to extract entries and creates a layout with images and text.
    
    Example:
        photobookgen ./my_notion_export ./book.pdf --layout portrait --size A4
    """
    try:
        # Check PATH setup on first run
        check_path_setup()
        
        # Validate inputs
        validate_input_folder(input_folder)
        img_dir = validate_img_dir(img_dir)
        
        # Parse max date if provided
        max_date_obj = None
        if max_date:
            max_date_obj = parse_date(max_date)
        
        # Create configuration
        config = PhotobookConfig(
            layout=layout,
            paper_size=paper_size,
            title_column=title_column,
            image_column=image_column,
            text_column=text_column,
            date_column=date_column,
        )
        
        # Show configuration
        if verbose:
            console.print(Panel(
                f"[bold]Configuration:[/bold]\n"
                f"Layout: {layout.value}\n"
                f"Paper size: {paper_size.value}\n"
                f"Title column: {title_column}\n"
                f"Image column: {image_column}\n"
                f"Text column: {text_column}\n"
                f"Date column: {date_column}\n"
                f"Downsample images: {not no_downsample}",
                title="📋 Settings"
            ))
        
        # Create generator
        generator = NotionPhotobookGenerator(config)
        
        # Generate photobook
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Generating photobook...", total=None)
            
            generator.generate_from_notion_export(
                input_folder=input_folder,
                output_path=output_path,
                img_dir=img_dir,
                max_date=max_date_obj,
                downsample_images=not no_downsample,
            )
        
        # Success message
        console.print(f"\n✅ [bold green]Photobook generated successfully![/bold green]")
        console.print(f"📄 Output: {output_path}")
        
    except Exception as e:
        console.print(f"\n❌ [bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command()
def demo(
    output_path: Path = typer.Argument(
        ...,
        help="Output PDF path for demo photobook",
        resolve_path=True,
    ),
    layout: Layout = typer.Option(
        Layout.LANDSCAPE,
        "--layout",
        "-l",
        help="Page layout (portrait or landscape)",
        case_sensitive=False,
    ),
    paper_size: PaperSize = typer.Option(
        PaperSize.A4,
        "--size",
        "-s",
        help="Paper size (A4, A3, A5, letter, legal)",
        case_sensitive=False,
    ),
) -> None:
    """
    Generate a demo photobook with sample data.
    
    This creates a photobook using sample entries to demonstrate the tool's capabilities.
    Note: You'll need to add some sample images to see the full effect.
    """
    try:
        # Check PATH setup on first run
        check_path_setup()
        
        console.print("🎭 [bold]Generating demo photobook...[/bold]")
        
        # Create configuration
        config = PhotobookConfig(
            layout=layout,
            paper_size=paper_size,
        )
        
        # Create generator
        generator = NotionPhotobookGenerator(config)
        
        # Create demo data
        demo_json = output_path.with_suffix('.demo.json')
        generator.create_demo_data(demo_json)
        
        # Create a dummy image directory
        img_dir = output_path.parent / "demo_images"
        img_dir.mkdir(exist_ok=True)
        
        # Generate photobook from demo data
        generator.generate_from_json(demo_json, output_path, img_dir)
        
        console.print(f"\n✅ [bold green]Demo photobook generated![/bold green]")
        console.print(f"📄 Output: {output_path}")
        console.print(f"📝 Demo data: {demo_json}")
        console.print(f"🖼️  Add some images to {img_dir} to see the full effect")
        
    except Exception as e:
        console.print(f"\n❌ [bold red]Error:[/bold red] {e}")
        sys.exit(1)


@app.command()
def parse(
    input_folder: Path = typer.Argument(
        ...,
        help="Path to Notion HTML export folder",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output_json: Path = typer.Argument(
        ...,
        help="Output JSON path",
        resolve_path=True,
    ),
    test_json: Optional[Path] = typer.Option(
        None,
        "--test-json",
        help="Path to save test JSON (smaller dataset)",
        resolve_path=True,
    ),
    max_date: Optional[str] = typer.Option(
        None,
        "--max-date",
        "-d",
        help="Maximum date to include (YYYY-MM-DD format)",
    ),
) -> None:
    """
    Parse Notion HTML export to JSON without generating PDF.
    
    This is useful for inspecting the parsed data or generating JSON for later use.
    """
    try:
        # Check PATH setup on first run
        check_path_setup()
        
        # Validate inputs
        validate_input_folder(input_folder)
        
        # Parse max date if provided
        max_date_obj = None
        if max_date:
            max_date_obj = parse_date(max_date)
        
        # Create generator
        generator = NotionPhotobookGenerator()
        
        # Parse and save
        entries = generator.parse_and_save_json(
            input_folder=input_folder,
            output_json=output_json,
            test_json=test_json,
            max_date=max_date_obj,
        )
        
        console.print(f"\n✅ [bold green]Parsed successfully![/bold green]")
        console.print(f"📝 Found {len(entries)} entries")
        console.print(f"📄 Output: {output_json}")
        if test_json:
            console.print(f"🧪 Test data: {test_json}")
        
    except Exception as e:
        console.print(f"\n❌ [bold red]Error:[/bold red] {e}")
        sys.exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    from . import __version__
    
    console.print(f"📚 [bold]Notion Photobook Generator[/bold] v{__version__}")
    console.print("Convert Notion HTML exports into beautiful print-ready photobooks")


@app.command()
def setup() -> None:
    """Show setup instructions for PATH configuration."""
    console.print("[bold]🔧 Setup Instructions[/bold]\n")
    
    # Try to find the script location
    import site
    user_site = site.getusersitepackages()
    if user_site:
        script_dir = Path(user_site).parent / "bin"
        if (script_dir / "photobookgen").exists():
            console.print(f"📍 Script location: [bold]{script_dir}[/bold]\n")
            
            console.print("To add to your PATH, choose one of these options:\n")
            
            console.print("1️⃣ [bold]Temporary (current session only):[/bold]")
            console.print(f"   [code]export PATH=\"{script_dir}:$PATH\"[/code]\n")
            
            console.print("2️⃣ [bold]Permanent (recommended):[/bold]")
            console.print("   Add this line to your shell config file:")
            console.print(f"   [code]export PATH=\"{script_dir}:$PATH\"[/code]")
            console.print("   Then restart your terminal or run: [code]source ~/.zshrc[/code]\n")
            
            console.print("3️⃣ [bold]Alternative:[/bold]")
            console.print("   Run the tool directly:")
            console.print(f"   [code]{script_dir}/photobookgen --help[/code]\n")
        else:
            console.print("❌ Could not find the photobookgen script.")
            console.print("   Try reinstalling the package.")
    else:
        console.print("❌ Could not determine script location.")
        console.print("   Try reinstalling the package.")


if __name__ == "__main__":
    app() 