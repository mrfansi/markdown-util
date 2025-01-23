"""URL to Markdown converter package."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from url2md.core import Url2Md
from url2md.handlers.base_handler import BaseHandler
from url2md.handlers.html_handler import HtmlHandler

__all__ = ["Url2Md", "BaseHandler", "HtmlHandler"]