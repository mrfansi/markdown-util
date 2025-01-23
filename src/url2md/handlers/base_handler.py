"""Base handler for content conversion."""
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from rich.console import Console


class BaseHandler(ABC):
    """Abstract base class for content handlers."""

    def __init__(
        self,
        url: str,
        output_dir: Path,
        config: Optional[Dict] = None,
        timeout: int = 30,
        wait: int = 0,
    ) -> None:
        """Initialize base handler.

        Args:
            url: Source URL to process
            output_dir: Directory for output files
            config: Handler-specific configuration
            timeout: Timeout in seconds for page rendering
            wait: Time in seconds to wait after page load
        """
        self.url = url
        self.output_dir = Path(output_dir)
        self.config = config or {}
        self.timeout = timeout
        self.wait = wait
        self.content: Optional[str] = None
        self.console = Console()
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Context manager entry."""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._session:
            await self._session.close()

    @abstractmethod
    async def fetch_content(self) -> None:
        """Fetch content from source URL.

        This method must be implemented by concrete handlers to fetch
        content in their specific way (e.g., HTML, PDF, etc.).

        Raises:
            NotImplementedError: If not implemented by concrete handler
        """
        raise NotImplementedError

    @abstractmethod
    async def convert(self) -> List[Path]:
        """Convert fetched content to Markdown.

        Returns:
            List[Path]: Paths to generated Markdown files

        Raises:
            NotImplementedError: If not implemented by concrete handler
        """
        raise NotImplementedError

    async def generate_toc(self, files: List[Path]) -> Path:
        """Generate table of contents for multiple files.

        Args:
            files: List of markdown files to include in TOC

        Returns:
            Path: Path to generated TOC file
        """
        toc_content = ["# Table of Contents\n"]
        
        for file in sorted(files):
            relative_path = file.relative_to(self.output_dir)
            name = file.stem.replace("-", " ").title()
            toc_content.append(f"- [{name}]({relative_path})")

        toc_file = self.output_dir / "README.md"
        toc_file.write_text("\n".join(toc_content))
        return toc_file

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility.

        Args:
            filename: Original filename

        Returns:
            str: Sanitized filename
        """
        # Remove invalid characters
        valid_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        filename = "".join(c for c in filename if c in valid_chars)
        
        # Convert to lowercase and replace spaces with hyphens
        filename = filename.lower().strip().replace(" ", "-")
        
        # Ensure filename is not empty
        if not filename:
            filename = "unnamed"
        
        return filename
