"""Unit tests for Markdown splitter functionality."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from url2md.utils.markdown_splitter import MarkdownSplitter

def test_split_markdown_basic():
    """Test basic Markdown splitting functionality."""
    content = """# First Section
Content for first section

# Second Section
Content for second section"""

    with TemporaryDirectory() as temp_dir:
        result = MarkdownSplitter.split_markdown(content, temp_dir)
        
        assert len(result) == 2
        assert "First_Section.md" in result
        assert "Second_Section.md" in result
        
        # Verify file contents
        with open(Path(temp_dir) / "First_Section.md", "r") as f:
            assert f.read().strip() == "# First Section\nContent for first section"
            
        with open(Path(temp_dir) / "Second_Section.md", "r") as f:
            assert f.read().strip() == "# Second Section\nContent for second section"

def test_split_markdown_no_h1():
    """Test splitting Markdown with no H1 headings."""
    content = "Some content without headings"
    
    with TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError, match="No H1 headings found"):
            MarkdownSplitter.split_markdown(content, temp_dir)

def test_split_markdown_special_chars():
    """Test splitting Markdown with special characters in headings."""
    content = """# Section: With/Colons
Content

# Section With "Quotes"
More content"""

    with TemporaryDirectory() as temp_dir:
        result = MarkdownSplitter.split_markdown(content, temp_dir)
        
        assert len(result) == 2
        assert "Section_With_Colons.md" in result
        assert "Section_With_Quotes.md" in result

def test_split_markdown_empty():
    """Test splitting empty Markdown content."""
    with TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError, match="Empty Markdown content"):
            MarkdownSplitter.split_markdown("", temp_dir)

def test_split_markdown_multiline_content():
    """Test splitting Markdown with multiline content between headings."""
    content = """# First Section
Line 1
Line 2

# Second Section
Line 3
Line 4"""

    with TemporaryDirectory() as temp_dir:
        result = MarkdownSplitter.split_markdown(content, temp_dir)
        
        assert len(result) == 2
        with open(Path(temp_dir) / "First_Section.md", "r") as f:
            assert f.read().strip() == "# First Section\nLine 1\nLine 2"