"""Command-line interface for url2md."""
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from rich.table import Table

from url2md import __version__
from url2md.core import Url2Md
from url2md.handlers.html_handler import HtmlHandler

app = typer.Typer(
    name="url2md",
    help="Convert webpage content to well-structured Markdown files.",
    add_completion=False,
)

console = Console()

def version_callback(value: bool):
    """Show version and exit.

    Args:
        value: Flag value
    """
    if value:
        console.print(f"url2md version: {__version__}")
        raise typer.Exit()

@app.command()
def main(
    urls: List[str] = typer.Argument(
        ...,
        help="URLs to convert to Markdown",
        show_default=False,
    ),
    output_dir: Path = typer.Option(
        "./docs",
        "--output-dir", "-o",
        help="Output directory for Markdown files",
        show_default=True,
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to configuration file",
        show_default=False,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output",
        show_default=True,
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        help="Timeout in seconds for page rendering",
        show_default=True,
    ),
    wait: int = typer.Option(
        0,
        "--wait",
        help="Time in seconds to wait after page load",
        show_default=True,
    ),
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        help="Show version and exit",
        is_eager=True,
    ),
) -> None:
    """Convert webpage content to Markdown files.

    This tool fetches content from the specified URLs and converts it into
    well-structured Markdown files, automatically handling:

    - Multi-file generation based on H1 headings
    - Dynamic content rendering (JavaScript)
    - Table of contents generation
    - Checksum verification
    """
    try:
        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize converter
        converter = Url2Md(
            output_dir=output_dir,
            config_file=config,
            verbose=verbose,
        )

        # Register HTML handler
        converter.register_handler("html", HtmlHandler)

        # Show configuration in verbose mode
        if verbose:
            config_table = Table(title="Configuration")
            config_table.add_column("Setting", style="cyan")
            config_table.add_column("Value", style="green")
            
            config_table.add_row("Output Directory", str(output_dir))
            config_table.add_row("Config File", str(config) if config else "Default")
            config_table.add_row("Verbose Mode", "Enabled" if verbose else "Disabled")
            
            console.print(config_table)
            console.print()

        # Validate URLs
        if not urls:
            console.print("[red]Error:[/red] No URLs provided")
            raise typer.Exit(code=1)

        # Validate output directory
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            if not output_dir.is_dir():
                console.print(f"[red]Error:[/red] Invalid output directory: {output_dir}")
                raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to create output directory: {str(e)}")
            raise typer.Exit(code=1)

        # Process each URL
        total_files = []
        with console.status("[bold blue]Converting URLs...") as status:
            for url in urls:
                status.update(f"Processing {url}")
                console.print(f"Processing {url}")
                
                # Validate URL format
                if not url.startswith(('http://', 'https://')):
                    console.print(f"[red]✗[/red] {url}: Invalid URL format")
                    raise typer.Exit(code=1)

                try:
                    files = converter.run(url)
                    if not files:
                        console.print(f"[red]Error:[/red] No files generated from {url}")
                        raise typer.Exit(code=1)
                    
                    # Show success message
                    console.print(f"[green]Success:[/green] Generated {len(files)} files from {url}")
                    if verbose:
                        for file in files:
                            console.print(f"  ├─ [cyan]{file.name}[/cyan]")
                    total_files.extend(files)
                    status.update(f"Completed {url} - {len(files)} files generated")
                
                except Exception as e:
                    console.print(f"[red]Error processing {url}:[/red] {str(e)}")
                    if verbose:
                        console.print_exception()
                    raise typer.Exit(code=1)

        # Show summary
        if total_files:
            summary = Panel(
                f"[green]Conversion completed successfully[/green]\n"
                f"Total files generated: {len(total_files)}\n"
                f"Output directory: [cyan]{output_dir}[/cyan]",
                title="Summary",
                border_style="green",
            )
            console.print(summary)
            raise typer.Exit(code=0)
        else:
            console.print("[red]Error:[/red] No files were generated from any URLs")
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
