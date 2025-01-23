"""Shared test configuration and fixtures."""
import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from _pytest.fixtures import SubRequest
from rich.console import Console

@pytest.fixture
def mock_converter(monkeypatch):
    """Create mock Url2Md instance."""
    import url2md.cli
    
    converter = MagicMock()
    converter.run.return_value = [Path("test.md")]
    converter.register_handler = MagicMock()
    
    mock = MagicMock()
    mock.return_value = converter
    
    monkeypatch.setattr(url2md.cli, "Url2Md", mock)
    return converter

@pytest.fixture
def mock_console(monkeypatch):
    """Create mock Console instance."""
    console = MagicMock(spec=Console)
    status_context = MagicMock()
    status_mock = MagicMock()
    status_context.__enter__.return_value = status_mock
    console.status.return_value = status_context
    
    monkeypatch.setattr(url2md.cli, "Console", MagicMock(return_value=console))
    return console

@pytest_asyncio.fixture
async def event_loop(request: SubRequest) -> AsyncGenerator[asyncio.AbstractEventLoop, None]:
    """Create and provide an event loop for each test case.
    
    This fixture ensures each test has its own event loop and
    properly handles both async and sync tests.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def mock_html_response() -> str:
    """Provide mock HTML content for testing."""
    return """
    <html>
        <body>
            <h1>Test Title</h1>
            <p>Test content</p>
            <h1>Second Section</h1>
            <p>More content</p>
        </body>
    </html>
    """

class HtmlMock(MagicMock):
    """Mock HTML object with arender method."""
    
    def __init__(self, html_content: str, *args, **kwargs):
        """Initialize with HTML content."""
        super().__init__(*args, **kwargs)
        self.html = html_content
        self.arender = AsyncMock()

class MockResponse:
    """Mock response object for testing."""
    
    def __init__(self, html_content: str):
        """Initialize with HTML content."""
        self.html = HtmlMock(html_content)

class MockAsyncSession:
    """Mock async session for testing."""
    
    def __init__(self, html_response: str):
        """Initialize with HTML response."""
        self.html_response = html_response
        self.get = AsyncMock()
        self.get.return_value = MockResponse(html_response)
        self.close = AsyncMock()

@pytest_asyncio.fixture
async def mock_session(mock_html_response: str) -> AsyncGenerator[MockAsyncSession, None]:
    """Create and provide a mock async session.
    
    Args:
        mock_html_response: Mock HTML content to return

    Yields:
        MockAsyncSession: Configured mock session
    """
    session = MockAsyncSession(mock_html_response)
    yield session
    await session.close()

@pytest.fixture(autouse=True)
def _setup_testing_directory(monkeypatch) -> None:
    """Configure testing directory for consistent test execution."""
    # Use a consistent test directory
    test_dir = os.path.abspath(os.path.dirname(__file__))
    monkeypatch.chdir(test_dir)