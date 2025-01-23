"""Unit tests for core functionality."""
import pytest
from pathlib import Path

from url2md.core import Url2Md
from url2md.handlers.base_handler import BaseHandler

class MockHandler(BaseHandler):
    """Mock handler for testing."""
    
    async def fetch_content(self):
        """Mock fetch content."""
        self.content = "<h1>Test</h1><p>Content</p>"

    async def convert(self):
        """Mock convert content."""
        output_file = self.output_dir / "test.md"
        output_file.write_text("# Test\n\nContent")
        return [output_file]

@pytest.fixture
def converter(tmp_path):
    """Create test converter instance."""
    return Url2Md(output_dir=tmp_path)

def test_url2md_initialization(converter):
    """Test Url2Md initialization."""
    assert isinstance(converter, Url2Md)
    assert converter.output_dir.exists()

def test_register_handler(converter):
    """Test handler registration."""
    converter.register_handler("mock", MockHandler)
    assert "mock" in converter._handlers
    assert converter._handlers["mock"] == MockHandler

def test_register_invalid_handler(converter):
    """Test registering invalid handler."""
    class InvalidHandler:
        pass

    with pytest.raises(ValueError):
        converter.register_handler("invalid", InvalidHandler)

@pytest.mark.asyncio
async def test_convert_with_mock_handler(converter, tmp_path):
    """Test conversion process with mock handler."""
    # Register mock handler
    converter.register_handler("mock", MockHandler)
    
    # Convert test URL
    files = await converter.convert("https://example.com", "mock")
    
    assert len(files) == 1
    assert files[0].name == "test.md"
    assert files[0].read_text() == "# Test\n\nContent"

def test_run_sync_wrapper(converter):
    """Test synchronous run wrapper."""
    converter.register_handler("mock", MockHandler)
    files = converter.run("https://example.com", "mock")
    
    assert len(files) == 1
    assert files[0].name == "test.md"

def test_invalid_handler_type(converter):
    """Test conversion with invalid handler type."""
    with pytest.raises(ValueError):
        converter.run("https://example.com", "nonexistent")

@pytest.mark.asyncio
async def test_output_directory_creation(tmp_path):
    """Test output directory is created if not exists."""
    output_dir = tmp_path / "nonexistent"
    converter = Url2Md(output_dir=output_dir)
    
    assert output_dir.exists()
    assert output_dir.is_dir()

def test_load_config_file(tmp_path):
    """Test configuration loading."""
    config_file = tmp_path / "test_config.yml"
    config_file.write_text("""
html:
  js_render:
    enabled: true
    timeout: 30
""")
    
    converter = Url2Md(output_dir=tmp_path, config_file=config_file)
    assert converter.config.get("html", {}).get("js_render", {}).get("timeout") == 30

def test_load_nonexistent_config(converter, caplog):
    """Test loading nonexistent config file."""
    converter = Url2Md(output_dir=".", config_file="nonexistent.yml")
    assert not converter.config
    assert "Config file not found" in caplog.text