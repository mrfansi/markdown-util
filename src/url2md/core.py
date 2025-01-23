"""Core functionality for URL to Markdown conversion."""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Type, Union
from url2md.utils.formatter import MarkdownFormatter

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from url2md.handlers.base_handler import BaseHandler
from url2md.utils.logger import setup_logger
from url2md.utils.markdown_splitter import MarkdownSplitter
from url2md.utils.html_splitter import HtmlSplitter

class Url2Md:
    """Main class for URL to Markdown conversion."""

    def __init__(
        self,
        output_dir: Union[str, Path] = "./docs",
        config_file: Optional[Union[str, Path]] = None,
        verbose: bool = False,
        timeout: int = 30,
        wait: int = 0,
    ):
        """Initialize URL to Markdown converter.

        Args:
            output_dir: Directory to store output files
            config_file: Path to configuration file
            verbose: Enable verbose logging
            timeout: Timeout in seconds for page rendering
            wait: Time in seconds to wait after page load
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger(verbose)
        self.console = Console()
        self._handlers: Dict[str, Type[BaseHandler]] = {}
        self.config = self._load_config(config_file) if config_file else {}
        self.timeout = timeout
        self.wait = wait

    def _load_config(self, config_file: Union[str, Path]) -> dict:
        """Load configuration from file.

        Args:
            config_file: Path to configuration file

        Returns:
            dict: Configuration dictionary
        """
        config_path = Path(config_file)
        if not config_path.exists():
            self.logger.warning(f"Config file not found: {config_file}")
            return {}

        with config_path.open() as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                self.logger.error(f"Error parsing config file: {e}")
                return {}

    def register_handler(self, handler_type: str, handler_class: Type[BaseHandler]) -> None:
        """Register a new content handler.

        Args:
            handler_type: Type identifier for the handler
            handler_class: Handler class to register
        """
        if not issubclass(handler_class, BaseHandler):
            raise ValueError(f"Handler must inherit from BaseHandler: {handler_class}")
        self._handlers[handler_type] = handler_class

    async def convert(self, url: str, handler_type: str = "html", timeout: int = 30, wait: int = 0) -> List[Path]:
        """Convert URL content to Markdown files.

        Args:
            url: URL to convert
            handler_type: Type of handler to use
            timeout: Timeout in seconds for page rendering
            wait: Time in seconds to wait after page load

        Returns:
            List[Path]: List of generated markdown files

        Raises:
            ValueError: If handler type is not registered
        """
        if handler_type not in self._handlers:
            raise ValueError(f"No handler registered for type: {handler_type}")

        # Create output directory based on configuration
        if self.config.get('output', {}).get('structure', {}).get('domain_folders', False):
            from url2md.utils.domain import build_domain_path
            domain_path = build_domain_path(
                url,
                include_subdomains=self.config['output']['structure']['domain_options']['include_subdomains'],
                fallback=self.config['output']['structure']['domain_options']['fallback_folder']
            )
            output_path = self.output_dir / domain_path
        else:
            # Fallback to date-based structure
            date_dir = datetime.now().strftime("%Y-%m-%d")
            output_path = self.output_dir / date_dir
            
        output_path.mkdir(parents=True, exist_ok=True)

        # Initialize handler
        handler = self._handlers[handler_type](
            url=url,
            output_dir=output_path,
            config=self.config.get(handler_type, {}),
            timeout=timeout,
            wait=wait
        )

        # Show progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task(f"Converting {url}...", total=None)
            
            try:
                # Fetch and process content
                await handler.fetch_content()
                files = await handler.convert()
                
                # Split both Markdown and HTML files
                split_files = []
                html_splitter = HtmlSplitter(output_path)
                
                for file in files:
                    try:
                        # Split Markdown
                        md_split_result = self.split_markdown_file(file)
                        split_files.extend(md_split_result)
                        
                        # Split HTML
                        with open(file, 'r') as f:
                            html_content = f.read()
                        html_splitter.split_and_save(html_content)
                        
                    except ValueError:
                        # File doesn't contain multiple H1s, keep original
                        split_files.append(file)
                
                # Generate table of contents if multiple files
                if len(split_files) > 1:
                    toc_file = await handler.generate_toc(split_files)
                    split_files.append(toc_file)
                
                files = split_files
                
                # Format generated Markdown files
                if self.config.get('format_markdown', True):
                    formatter = MarkdownFormatter(self.config.get('formatting', {}))
                    formatter.format_directory(self.output_dir)
                
                progress.update(task, completed=True)
                return files
                
            except Exception as e:
                self.logger.error(f"Conversion failed: {str(e)}", exc_info=True)
                progress.update(task, description=f"[red]Error: {str(e)}")
                raise

    def split_markdown_file(self, markdown_file: Union[str, Path]) -> List[Path]:
        """Split a Markdown file into multiple files based on H1 headings.
        
        Args:
            markdown_file: Path to the Markdown file to split
            
        Returns:
            List[Path]: List of generated Markdown files
            
        Raises:
            ValueError: If file doesn't exist or has no H1 headings
            IOError: If file cannot be read
        """
        file_path = Path(markdown_file)
        if not file_path.exists():
            raise ValueError(f"Markdown file not found: {markdown_file}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Create output directory with same name as input file
            output_dir = file_path.parent / file_path.stem
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Split and save files
            MarkdownSplitter.split_markdown(content, str(output_dir))
            
            # Return list of generated files
            return sorted(output_dir.glob("*.md"))
            
        except Exception as e:
            self.logger.error(f"Failed to split Markdown file: {str(e)}", exc_info=True)
            raise

    def run(self, url: str, handler_type: str = "html") -> List[Path]:
        """Synchronous wrapper for convert method.

        Args:
            url: URL to convert
            handler_type: Type of handler to use

        Returns:
            List[Path]: List of generated markdown files
        """
        return asyncio.run(self.convert(url, handler_type, self.timeout, self.wait))
