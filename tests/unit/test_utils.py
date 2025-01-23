"""Unit tests for utility modules."""
import logging
from pathlib import Path

import pytest
from rich.console import Console

from url2md.utils.logger import ColorizedFormatter, setup_logger
from url2md.utils.sanitizer import (FilenameNormalizer, PathSanitizer,
                                  UrlSanitizer)

# URL Sanitizer Tests
def test_valid_url_detection():
    """Test URL validation."""
    assert UrlSanitizer.is_valid_url("https://example.com")
    assert UrlSanitizer.is_valid_url("http://test.com/path?q=1")
    assert not UrlSanitizer.is_valid_url("not-a-url")
    assert not UrlSanitizer.is_valid_url("file:///etc/passwd")

def test_url_sanitization():
    """Test URL sanitization."""
    # Add scheme
    assert UrlSanitizer.sanitize_url("example.com") == "https://example.com"
    
    # Normalize domain
    assert UrlSanitizer.sanitize_url("EXAMPLE.com") == "https://example.com"
    
    # Remove fragments
    assert UrlSanitizer.sanitize_url("https://example.com#fragment") == "https://example.com"
    
    # Invalid URLs
    assert UrlSanitizer.sanitize_url("javascript:alert(1)") is None
    assert UrlSanitizer.sanitize_url("data:text/plain;base64,SGVsbG8=") is None

# Path Sanitizer Tests
def test_safe_path_validation(tmp_path):
    """Test path safety validation."""
    test_file = tmp_path / "test.txt"
    test_file.touch()
    
    assert PathSanitizer.is_safe_path(test_file)
    assert PathSanitizer.is_safe_path(tmp_path / "new_file.txt")
    assert not PathSanitizer.is_safe_path(Path("/invalid/path"))

def test_path_sanitization(tmp_path):
    """Test path sanitization."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    # Valid paths
    assert PathSanitizer.sanitize_path(str(test_dir)) == test_dir.resolve()
    assert PathSanitizer.sanitize_path(str(test_dir / "new_file.txt"))
    
    # Invalid paths
    assert PathSanitizer.sanitize_path("/nonexistent/path") is None
    assert PathSanitizer.sanitize_path("../../../etc/passwd") is None

# Filename Normalizer Tests
def test_filename_normalization():
    """Test filename normalization."""
    assert FilenameNormalizer.normalize_filename("Test File.txt") == "test-file-txt"
    assert FilenameNormalizer.normalize_filename("!@#$%^&*.doc") == "doc"
    assert FilenameNormalizer.normalize_filename("") == "unnamed"
    assert FilenameNormalizer.normalize_filename("  spaces  ") == "spaces"

def test_safe_filename_generation(tmp_path):
    """Test safe filename generation with conflict resolution."""
    # Create existing file
    existing = tmp_path / "test.md"
    existing.touch()
    
    # Get safe filenames
    filename1 = FilenameNormalizer.get_safe_filename("test", "md", tmp_path)
    filename2 = FilenameNormalizer.get_safe_filename("test", "md", tmp_path)
    
    assert filename1 != filename2
    assert filename1.name == "test-1.md"
    assert filename2.name == "test-2.md"

# Logger Tests
def test_logger_setup():
    """Test logger configuration."""
    logger = setup_logger(verbose=True)
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "url2md"
    assert logger.level == logging.DEBUG
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

def test_logger_with_file(tmp_path):
    """Test logger with file output."""
    log_file = tmp_path / "test.log"
    logger = setup_logger(verbose=True, log_file=str(log_file))
    
    logger.info("Test message")
    assert log_file.exists()
    assert "Test message" in log_file.read_text()

def test_colorized_formatter():
    """Test log message colorization."""
    formatter = ColorizedFormatter("[%(levelname)s] %(message)s")
    
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="Test error",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    assert "[red]ERROR[/]" in formatted

@pytest.mark.asyncio
async def test_integration_path_handling(tmp_path):
    """Test integration of path and filename handling."""
    # Create test directory structure
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()
    
    # Test path sanitization
    safe_path = PathSanitizer.sanitize_path(str(test_dir))
    assert safe_path is not None
    
    # Generate unique filename
    filename = FilenameNormalizer.get_safe_filename(
        "Test Document!",
        "md",
        safe_path
    )
    
    assert filename.name == "test-document.md"
    assert filename.parent == test_dir

@pytest.mark.parametrize("input_url,expected", [
    ("https://example.com", "https://example.com"),
    ("http://test.com/path?q=1", "http://test.com/path?q=1"),
    ("example.com", "https://example.com"),
    ("https://EXAMPLE.COM", "https://example.com"),
    ("javascript:alert(1)", None),
    ("", None),
])
def test_url_sanitization_cases(input_url, expected):
    """Test URL sanitization with various inputs."""
    assert UrlSanitizer.sanitize_url(input_url) == expected

@pytest.mark.parametrize("filename,expected", [
    ("Normal File.txt", "normal-file-txt"),
    ("!@#$%^&*.doc", "doc"),
    ("   spaces   ", "spaces"),
    ("", "unnamed"),
    ("With-Hyphens", "with-hyphens"),
    ("multiple...dots", "multipledots"),
])
def test_filename_normalization_cases(filename, expected):
    """Test filename normalization with various inputs."""
    assert FilenameNormalizer.normalize_filename(filename) == expected