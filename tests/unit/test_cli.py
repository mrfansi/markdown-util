"""Unit tests for command-line interface."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from url2md.cli import app
from url2md import __version__

runner = CliRunner()

def test_version():
    """Test version display."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"url2md version: {__version__}" in result.stdout

def test_missing_url():
    """Test error on missing URL."""
    result = runner.invoke(app)
    assert result.exit_code == 2
    assert "Missing argument 'URLS...'" in result.stdout

@pytest.fixture
def mock_converter():
    """Create mock Url2Md instance."""
    with patch("url2md.cli.Url2Md") as mock_cls:
        converter = MagicMock()
        mock_cls.return_value = converter
        yield converter

def test_basic_conversion(mock_converter, tmp_path):
    """Test basic URL conversion."""
    mock_converter.run.return_value = [Path("test.md")]
    
    result = runner.invoke(app, [
        "https://example.com",
        "--output-dir", str(tmp_path)
    ])
    
    assert result.exit_code == 0
    mock_converter.register_handler.assert_called_once()
    mock_converter.run.assert_called_once_with("https://example.com")
    assert "Successfully generated" in result.stdout

def test_multiple_urls(mock_converter, tmp_path):
    """Test converting multiple URLs."""
    mock_converter.run.return_value = [Path("test.md")]
    urls = ["https://example1.com", "https://example2.com"]
    
    result = runner.invoke(app, [
        *urls,
        "--output-dir", str(tmp_path)
    ])
    
    assert result.exit_code == 0
    assert mock_converter.run.call_count == len(urls)

def test_verbose_output(mock_converter, tmp_path):
    """Test verbose output mode."""
    mock_converter.run.return_value = [Path("test.md")]
    
    result = runner.invoke(app, [
        "https://example.com",
        "--output-dir", str(tmp_path),
        "--verbose"
    ])
    
    assert result.exit_code == 0
    mock_converter.run.assert_called_once()
    assert "Configuration" in result.stdout

@patch("url2md.cli.Console")
def test_error_handling(mock_console, mock_converter, tmp_path):
    """Test error handling in CLI."""
    mock_converter.run.side_effect = Exception("Test error")
    mock_status = MagicMock()
    mock_console.return_value.status.return_value.__enter__.return_value = mock_status

    result = runner.invoke(app, [
        "https://example.com",
        "--output-dir", str(tmp_path)
    ])
    
    assert result.exit_code == 1
    assert "Error:" in result.stdout
    mock_status.update.assert_called()

def test_custom_config(mock_converter, tmp_path):
    """Test using custom configuration file."""
    mock_converter.run.return_value = [Path("test.md")]
    config_file = tmp_path / "test_config.yml"
    config_file.touch()
    
    result = runner.invoke(app, [
        "https://example.com",
        "--config", str(config_file)
    ])
    
    assert result.exit_code == 0
    assert mock_converter.register_handler.called
    assert mock_converter.run.called

@pytest.mark.parametrize("flag", ["-v", "--verbose"])
def test_verbose_flags(flag, mock_converter, tmp_path):
    """Test different verbose flag formats."""
    mock_converter.run.return_value = [Path("test.md")]
    
    result = runner.invoke(app, [
        "https://example.com",
        flag
    ])
    
    assert result.exit_code == 0
    assert mock_converter.register_handler.called
    assert mock_converter.run.called
    # Check if verbose was set correctly in constructor
    constructor_calls = [
        call for call in mock_converter.mock_calls 
        if isinstance(call, type) and call.kwargs.get('verbose')
    ]
    assert any(constructor_calls)

def test_help_output():
    """Test help message display."""
    result = runner.invoke(app, ["--help"])
    
    assert result.exit_code == 0
    assert "Convert webpage content" in result.stdout
    assert "--output-dir" in result.stdout
    assert "--verbose" in result.stdout

@patch("url2md.cli.Console")
def test_progress_display(mock_console, mock_converter, tmp_path):
    """Test progress display during conversion."""
    mock_converter.run.return_value = [Path("test.md")]
    mock_status = MagicMock()
    mock_console.return_value.status.return_value.__enter__.return_value = mock_status

    result = runner.invoke(app, [
        "https://example.com",
        "--output-dir", str(tmp_path)
    ])
    
    assert result.exit_code == 0
    mock_status.update.assert_called_with("Processing https://example.com")

def test_output_directory_creation(tmp_path):
    """Test output directory is created if not exists."""
    output_dir = tmp_path / "nonexistent"
    
    with patch("url2md.cli.Url2Md") as mock:
        mock.return_value.run.return_value = [Path("test.md")]
        
        result = runner.invoke(app, [
            "https://example.com",
            "--output-dir", str(output_dir)
        ])
        
        assert result.exit_code == 0
        assert output_dir.exists()

def test_no_files_generated(mock_converter, tmp_path):
    """Test handling when no files are generated."""
    mock_converter.run.return_value = []
    
    result = runner.invoke(app, [
        "https://example.com",
        "--output-dir", str(tmp_path)
    ])
    
    assert result.exit_code == 1
    assert "No files were generated" in result.stdout

@patch("url2md.cli.Console")
def test_exception_in_progress(mock_console, mock_converter, tmp_path):
    """Test handling exceptions during progress display."""
    mock_status = MagicMock()
    mock_console.return_value.status.return_value.__enter__.return_value = mock_status
    mock_converter.run.side_effect = Exception("Network error")

    result = runner.invoke(app, [
        "https://example.com",
        "--output-dir", str(tmp_path)
    ])
    
    assert result.exit_code == 1
    assert "Error:" in result.stdout
    mock_status.update.assert_called()