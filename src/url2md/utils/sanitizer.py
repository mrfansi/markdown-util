"""Sanitization utilities for url2md."""
import re
from pathlib import Path
from typing import Optional
from urllib.parse import ParseResult, urlparse

class UrlSanitizer:
    """URL validation and sanitization."""

    DANGEROUS_SCHEMES = {
        'javascript', 'data', 'vbscript', 'file',
        'about', 'chrome', 'resource'
    }

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid.

        Args:
            url: URL to validate

        Returns:
            bool: True if URL is valid
        """
        try:
            result = urlparse(url)
            return all([
                result.scheme in ('http', 'https'),
                result.netloc and '.' in result.netloc
            ])
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def sanitize_url(url: str) -> Optional[str]:
        """Sanitize and normalize URL.

        Args:
            url: URL to sanitize

        Returns:
            Optional[str]: Sanitized URL or None if invalid
        """
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        try:
            parsed: ParseResult = urlparse(url)
            
            # Validate URL scheme
            if parsed.scheme.lower() in UrlSanitizer.DANGEROUS_SCHEMES:
                return None

            # Validate URL components
            if not all([
                parsed.scheme in ('http', 'https'),
                parsed.netloc and '.' in parsed.netloc
            ]):
                return None

            # Remove fragments unless needed
            parsed = parsed._replace(fragment='')

            # Normalize domain
            netloc = parsed.netloc.lower().strip('.')
            parsed = parsed._replace(netloc=netloc)

            return parsed.geturl()
        except (ValueError, AttributeError):
            return None

class PathSanitizer:
    """Path validation and sanitization."""

    @staticmethod
    def is_safe_path(path: Path) -> bool:
        """Check if path is safe to use.

        Args:
            path: Path to validate

        Returns:
            bool: True if path is safe
        """
        try:
            # Resolve to absolute path
            resolved = path.resolve()
            
            # Check if path exists and is accessible
            if resolved.exists():
                resolved.stat()
                return True
                
            # For new paths, check if parent is accessible
            parent = resolved.parent
            if parent.exists():
                parent.stat()
                return True
                
            return False
        except (OSError, RuntimeError):
            return False

    @staticmethod
    def sanitize_path(path: str) -> Optional[Path]:
        """Sanitize and normalize file path.

        Args:
            path: Path to sanitize

        Returns:
            Optional[Path]: Sanitized Path or None if invalid
        """
        try:
            # Convert to Path object
            path_obj = Path(path)
            
            # Resolve to absolute path
            resolved = path_obj.resolve()
            
            # Basic security checks
            if PathSanitizer.is_safe_path(resolved):
                return resolved
                
            return None
        except (OSError, RuntimeError):
            return None

class FilenameNormalizer:
    """Filename normalization utilities."""

    INVALID_CHARS = re.compile(r'[^\w\s.-]')
    MULTIPLE_DOTS = re.compile(r'\.{2,}')
    SPACES_HYPHENS = re.compile(r'[-\s]+')

    @staticmethod
    def normalize_filename(filename: str) -> str:
        """Normalize filename for filesystem compatibility.

        Args:
            filename: Original filename

        Returns:
            str: Normalized filename
        """
        # Convert to lowercase
        filename = filename.lower()

        # Split extension if present (use rsplit to handle multiple dots)
        name_parts = filename.split('.')
        base = name_parts[0]
        ext = name_parts[-1] if len(name_parts) > 1 else ''

        # Clean up base name
        # 1. Replace invalid chars with empty string
        base = FilenameNormalizer.INVALID_CHARS.sub('', base)
        # 2. Replace spaces and multiple hyphens with single hyphen
        base = FilenameNormalizer.SPACES_HYPHENS.sub('-', base)
        # 3. Strip leading/trailing hyphens
        base = base.strip('-')

        # Ensure base is not empty
        if not base:
            base = 'unnamed'

        # Remove extension if it's just invalid characters
        if ext and not FilenameNormalizer.INVALID_CHARS.sub('', ext):
            ext = ''

        # Return base or base-ext
        return f"{base}-{ext}" if ext else base

    @staticmethod
    def get_safe_filename(base: str, extension: str, directory: Path) -> Path:
        """Get unique filename, avoiding conflicts.

        Args:
            base: Base filename
            extension: File extension
            directory: Target directory

        Returns:
            Path: Unique file path
        """
        directory.mkdir(parents=True, exist_ok=True)
        normalized_base = FilenameNormalizer.normalize_filename(base)

        # Try with counter
        counter = 1
        while True:
            if counter == 1:
                filename = f"{normalized_base}.{extension}"
            else:
                filename = f"{normalized_base}-{counter}.{extension}"

            path = directory / filename
            if not path.exists():
                return path
            counter += 1