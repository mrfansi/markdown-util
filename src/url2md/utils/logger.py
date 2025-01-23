"""Logging configuration for url2md."""
import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Custom theme for rich
CUSTOM_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "debug": "grey50",
})

class ColorizedFormatter(logging.Formatter):
    """Custom formatter with color support."""

    COLORS = {
        'DEBUG': 'grey50',
        'INFO': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red bold',
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors.

        Args:
            record: Log record to format

        Returns:
            str: Formatted log message
        """
        # Add color to level name
        if record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            record.levelname = f"[{color}]{record.levelname}[/]"

        return super().format(record)

def setup_logger(
    verbose: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Configure and return logger instance.

    Args:
        verbose: Enable debug logging
        log_file: Optional file path for logging

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("url2md")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Remove existing handlers
    logger.handlers.clear()

    # Console output with rich handler
    console = Console(theme=CUSTOM_THEME)
    rich_handler = RichHandler(
        console=console,
        show_path=verbose,
        enable_link_path=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=verbose,
        show_time=False,
        show_level=True,
    )
    
    rich_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    rich_handler.setFormatter(ColorizedFormatter(
        "%(message)s"
    ))
    logger.addHandler(rich_handler)

    # Add stream handler for non-rich output
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    stream_handler.setFormatter(ColorizedFormatter(
        "[%(levelname)s] %(message)s"
    ))
    logger.addHandler(stream_handler)

    # File output if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(file_handler)

    # Capture warnings
    logging.captureWarnings(True)
    
    return logger

def get_logger() -> logging.Logger:
    """Get the url2md logger instance.

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger("url2md")

# Configure exception handling
def handle_exception(exc_type, exc_value, exc_traceback):
    """Custom exception handler for unhandled exceptions.

    Args:
        exc_type: Exception type
        exc_value: Exception value
        exc_traceback: Exception traceback
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = get_logger()
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# Set custom exception handler
sys.excepthook = handle_exception