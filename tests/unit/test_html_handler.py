"""Unit tests for HTML content handler."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from bs4 import BeautifulSoup

from url2md.handlers.html_handler import CustomMarkdownConverter, HtmlHandler

@pytest_asyncio.fixture
async def html_handler(tmp_path, mock_session):
    """Create test HTML handler instance."""
    with patch('url2md.handlers.html_handler.AsyncHTMLSession') as mock:
        mock.return_value = mock_session
        handler = HtmlHandler(
            url="https://example.com",
            output_dir=tmp_path,
            config={
                "js_render": {
                    "enabled": True,
                    "timeout": 20
                }
            }
        )
        yield handler
        await handler.session.close()

@pytest.fixture
def markdown_converter():
    """Create test markdown converter instance."""
    return CustomMarkdownConverter(
        heading_style="atx",
        bullets="-",
        code_language=""
    )

@pytest.mark.asyncio
async def test_html_handler_initialization(html_handler):
    """Test HTML handler initialization."""
    assert isinstance(html_handler, HtmlHandler)
    assert html_handler.url == "https://example.com"
    assert html_handler.content is None

@pytest.mark.asyncio
async def test_convert_simple_content(html_handler, mock_html_response):
    """Test converting simple HTML content."""
    html_handler.content = mock_html_response
    
    files = await html_handler.convert()
    
    assert len(files) == 2
    assert files[0].name == "test-title.md"
    assert files[1].name == "second-section.md"
    
    # Check first file content
    content = files[0].read_text()
    assert "# Test Title" in content
    assert "Test content" in content

def test_markdown_converter_img_conversion(markdown_converter):
    """Test image conversion in markdown."""
    html = '<img src="test.jpg" alt="Test" title="Test Image">'
    soup = BeautifulSoup(html, "html.parser")
    result = markdown_converter.convert_img(soup.img, "", True)
    
    assert result == '![Test](test.jpg "Test Image")'

def test_markdown_converter_code_blocks(markdown_converter):
    """Test code block conversion."""
    html = '''
    <pre><code class="language-python">
    def test():
        print("Hello")
    </code></pre>
    '''
    soup = BeautifulSoup(html, "html.parser")
    result = markdown_converter.convert_pre(soup.pre, "def test():\n    print(\"Hello\")", False)
    
    assert "```python" in result
    assert "def test():" in result
    assert "```" in result

@pytest.mark.asyncio
async def test_split_by_h1(html_handler, mock_html_response):
    """Test content splitting by H1 headings."""
    soup = BeautifulSoup(mock_html_response, "html.parser")
    sections = html_handler._split_by_h1(soup)
    
    assert len(sections) == 2
    assert sections[0][0] == "Test Title"
    assert sections[1][0] == "Second Section"

@pytest.mark.asyncio
async def test_clean_markdown(html_handler):
    """Test markdown cleaning and formatting."""
    markdown = """

# Heading

- List item

```python
def test():
    pass
```

"""
    cleaned = html_handler._clean_markdown(markdown)
    
    assert cleaned.count("\n\n") == 3  # Check double newlines
    assert cleaned.startswith("# Heading")
    assert "```python" in cleaned

@pytest.mark.asyncio
async def test_generate_toc(html_handler, tmp_path):
    """Test table of contents generation."""
    # Create test files
    files = [
        tmp_path / "first-section.md",
        tmp_path / "second-section.md"
    ]
    
    for file in files:
        file.touch()
    
    toc = await html_handler.generate_toc(files)
    
    assert toc.exists()
    content = toc.read_text()
    assert "# Table of Contents" in content
    assert "First Section" in content
    assert "Second Section" in content

@pytest.mark.asyncio
async def test_verify_checksum(html_handler, tmp_path):
    """Test file checksum verification."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\nContent")
    
    # First verification creates checksum
    assert await html_handler.verify_checksum(test_file)
    
    # Second verification should match
    assert await html_handler.verify_checksum(test_file)
    
    # Modify file
    test_file.write_text("Modified content")
    assert not await html_handler.verify_checksum(test_file)

@pytest.mark.asyncio
async def test_handle_complex_html(html_handler):
    """Test handling complex HTML with nested structures."""
    html = """
    <article>
        <h1>Main Title</h1>
        <section>
            <h2>Section 1</h2>
            <p>Content with <strong>bold</strong> and <em>italic</em></p>
            <pre><code class="language-javascript">
            console.log('test');
            </code></pre>
        </section>
        <section>
            <h2>Section 2</h2>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </section>
    </article>
    """
    
    html_handler.content = html
    files = await html_handler.convert()
    
    assert len(files) == 1
    content = files[0].read_text()
    
    assert "# Main Title" in content
    assert "## Section" in content
    assert "**bold**" in content
    assert "_italic_" in content
    assert "```javascript" in content
    assert "- Item" in content

@pytest.mark.asyncio
async def test_fetch_content(html_handler):
    """Test content fetching and rendering."""
    await html_handler.fetch_content()
    assert html_handler.content is not None
    assert "<h1>Test Title</h1>" in html_handler.content

@pytest.mark.asyncio
async def test_fetch_content_error_handling(html_handler):
    """Test error handling during content fetching."""
    with patch.object(html_handler.session, 'get', side_effect=Exception("Network error")):
        with pytest.raises(Exception) as exc_info:
            await html_handler.fetch_content()
        assert "Network error" in str(exc_info.value)