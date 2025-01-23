"""Core functionality for URL to Markdown conversion."""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from url2md.handlers.base_handler import BaseHandler
from url2md.utils.logger import setup_logger

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

        # Create output directory with date-based structure
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
                
                # Generate table of contents if multiple files
                if len(files) > 1:
                    toc_file = await handler.generate_toc(files)
                    files.append(toc_file)
                
                # Verify checksums
                for file in files:
                    await handler.verify_checksum(file)
                
                progress.update(task, completed=True)
                return files
                
            except Exception as e:
                self.logger.error(f"Conversion failed: {str(e)}", exc_info=True)
                progress.update(task, description=f"[red]Error: {str(e)}")
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
