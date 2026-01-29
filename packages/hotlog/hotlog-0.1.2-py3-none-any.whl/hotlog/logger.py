"""Public API for logging operations."""

import structlog
from structlog.types import FilteringBoundLogger


def get_logger(name: str) -> FilteringBoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        FilteringBoundLogger: A configured logger instance

    Example:
        >>> from hotlog import configure_logging, get_logger
        >>> configure_logging()
        >>> log = get_logger(__name__)
        >>> log.info("Application started")
        >>> log.info("Processing file", filename="data.csv", _verbose_rows=1000)
    """
    return structlog.get_logger(name)


def highlight(text: str, *values: str) -> str:
    """Highlight specific values in a message using Rich markup.

    Useful for emphasizing important information in log messages.
    Wraps values in bold for emphasis in CLI output.

    Args:
        text: Format string with {} placeholders
        *values: Values to highlight (will be bolded)

    Returns:
        str: Formatted string with Rich markup for bold values

    Example:
        >>> from hotlog import get_logger, highlight
        >>> log = get_logger(__name__)
        >>> log.info(highlight("Downloaded {} in {}", "14 files", "2.5s"))
        # '14 files' and '2.5s' appear in bold
    """
    bold_values = [f'[bold]{v}[/bold]' for v in values]
    return text.format(*bold_values)
