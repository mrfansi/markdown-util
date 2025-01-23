"""Integration tests for url2md."""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from typer.testing import CliRunner

from url2md import Url2Md
from url2md.cli import app
from url2md.handlers.html_handler import HtmlHandler

@pytest_asyncio.fixture
async def converter(tmp_path, mock_session):
    """Create configured Url2Md instance."""
    with patch('url2md.handlers.html_handler.AsyncHTMLSession') as mock:
        mock.return_value = mock_session
        converter = Url2Md(output_dir=tmp_path)
        converter.register_handler("html", HtmlHandler)
        yield converter

@pytest.mark.asyncio
async def test_full_conversion_workflow(converter, mock_html_response):
    """Test complete conversion workflow."""
    # Convert test URL
    files = await converter.convert("https://example.com")
    
    assert len(files) > 0
    
    # Verify file contents
    content_map = {f.stem: f.read_text() for f in files}
    
    # Check Introduction section
    assert "test-title" in content_map
    intro = content_map["test-title"]
    assert "# Test Title" in intro
    assert "Test content" in intro
    
    # Check Second Section
    assert "second-section" in content_map
    section = content_map["second-section"]
    assert "# Second Section" in section
    assert "More content" in section
    
    # Check TOC
    assert any("README.md" in str(f) for f in files)
    toc = next(f for f in files if "README.md" in str(f))
    toc_content = toc.read_text()
    assert "Table of Contents" in toc_content
    assert "Test Title" in toc_content
    assert "Second Section" in toc_content

def test_cli_integration(mock_converter, tmp_path):
    """Test CLI integration with converter."""
    runner = CliRunner()
    mock_converter.run.return_value = [
        tmp_path / "test-title.md",
        tmp_path / "second-section.md"
    ]
    
    result = runner.invoke(app, [
        "https://example.com",
        "--output-dir", str(tmp_path),
        "--verbose"
    ])
    
    assert result.exit_code == 0
    assert "Successfully generated" in result.stdout
    assert mock_converter.run.called

@pytest.mark.asyncio
async def test_error_handling_integration(converter):
    """Test error handling in integration scenario."""
    with patch.object(converter._handlers["html"], 'fetch_content', 
                     side_effect=Exception("Network error")):
        with pytest.raises(Exception) as exc_info:
            await converter.convert("https://example.com")
        
        assert "Network error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_custom_config_integration(converter, tmp_path):
    """Test integration with custom configuration."""
    config_file = tmp_path / "test_config.yml"
    config_file.write_text("""
html:
  js_render:
    enabled: true
    timeout: 30
  content:
    remove_selectors:
      - .advertisement
    """)
    
    # Create new converter with config
    converter = Url2Md(output_dir=tmp_path, config_file=config_file)
    converter.register_handler("html", HtmlHandler)
    
    files = await converter.convert("https://example.com")
    assert len(files) > 0

@pytest.mark.asyncio
async def test_multiple_url_integration(converter):
    """Test converting multiple URLs in integration."""
    urls = [
        "https://example1.com",
        "https://example2.com"
    ]
    
    all_files = []
    for url in urls:
        files = await converter.convert(url)
        all_files.extend(files)
    
    # Each URL should generate at least 2 files (content + TOC)
    assert len(all_files) >= len(urls) * 2

@pytest.mark.asyncio
async def test_checksum_verification_integration(converter, tmp_path):
    """Test checksum verification in integration scenario."""
    # Initial conversion
    files = await converter.convert("https://example.com")
    
    for file in files:
        # Verify checksum file exists
        checksum_file = file.parent / f".{file.name}.sha256"
        assert checksum_file.exists()
        
        # Modify file and verify checksum fails
        original_content = file.read_text()
        file.write_text(original_content + "\nModified")
        
        handler = HtmlHandler("https://example.com", tmp_path)
        assert not await handler.verify_checksum(file)

@pytest.mark.asyncio
async def test_directory_structure_integration(converter, tmp_path):
    """Test directory structure creation."""
    files = await converter.convert("https://example.com")
    
    # Check date-based directory
    date_dirs = list(tmp_path.glob("????-??-??"))
    assert len(date_dirs) == 1
    assert all(f.parent == date_dirs[0] for f in files)

@pytest.mark.asyncio
async def test_toc_generation_integration(converter):
    """Test table of contents generation with multiple files."""
    files = await converter.convert("https://example.com")
    toc_file = next((f for f in files if f.name == "README.md"), None)
    
    assert toc_file is not None
    content = toc_file.read_text()
    assert "Table of Contents" in content
    
    # Check all content files are linked
    content_files = [f for f in files if f.name != "README.md"]
    for file in content_files:
        assert file.stem in content