"""Markdown formatting utilities using mdformat."""
import mdformat
from pathlib import Path
from typing import Optional, Dict

class MarkdownFormatter:
    """Format Markdown files using mdformat with custom options."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize formatter with configuration.
        
        Args:
            config: Formatting configuration options
        """
        self.config = config or {}
        
    def format_file(self, file_path: Path) -> None:
        """Format a single Markdown file.
        
        Args:
            file_path: Path to Markdown file
        """
        if not file_path.exists():
            return
            
        content = file_path.read_text()
        formatted = mdformat.text(
            content,
            options={
                'wrap': self.config.get('wrap', 80),
                'end_of_line': self.config.get('end_of_line', 'lf'),
                'code_style': self.config.get('code_style', 'consistent')
            }
        )
        file_path.write_text(formatted)
        
    def format_directory(self, directory: Path) -> None:
        """Format all Markdown files in a directory.
        
        Args:
            directory: Path to directory containing Markdown files
        """
        for md_file in directory.glob("**/*.md"):
            self.format_file(md_file)