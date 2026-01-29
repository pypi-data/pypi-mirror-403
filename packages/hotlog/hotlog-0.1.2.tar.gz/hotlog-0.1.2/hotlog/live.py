"""Live logging support for ephemeral messages in CLI applications."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import structlog
from rich.live import Live
from structlog.types import FilteringBoundLogger

from hotlog.config import get_config, get_console


class LiveLogger:
    """A logger wrapper that marks all messages as live (ephemeral).

    When using live_logging() context manager at level 0, messages logged
    through LiveLogger are buffered and displayed in the live area.
    They disappear when the live context ends.

    Example:
        >>> with live_logging() as live_log:
        ...     live_log.info("Processing...", file="data.csv")
        ...     # Message appears only during the context
    """

    def __init__(self, base_logger: FilteringBoundLogger) -> None:
        """Initialize with a base logger.

        Args:
            base_logger: The structlog logger to wrap
        """
        self._base_logger = base_logger

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message marked as live."""
        self._base_logger.info(message, _live_=True, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message marked as live."""
        self._base_logger.warning(message, _live_=True, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message (always visible, never buffered)."""
        # Errors should always be visible, don't mark as live
        self._base_logger.error(message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message marked as live."""
        self._base_logger.debug(message, _live_=True, **kwargs)


@contextmanager
def live_logging(
    message: str = 'Processing...',
) -> Generator[LiveLogger, None, None]:
    """Context manager for live logging of ephemeral messages.

    At level 0, messages logged through the LiveLogger are buffered
    and displayed in a live area. They disappear when the context exits.

    At level 1+, messages are printed normally (not ephemeral).

    Args:
        message: The live status message to display

    Yields:
        LiveLogger: A logger wrapper that marks messages as live

    Example:
        >>> with live_logging("Downloading files...") as live:
        ...     for i in range(3):
        ...         live.info("Processing", item=i)
        ...         time.sleep(0.5)
        >>> # Live messages disappear here at level 0
    """
    config = get_config()
    base_logger = structlog.get_logger('live')

    if config.verbosity_level == 0:
        # Level 0: Use Rich Live display for ephemeral messages
        console = get_console()
        config.clear_live_messages()  # Clear message buffer
        with Live(
            f'[bold blue]{message}[/bold blue]',
            console=console,
            refresh_per_second=10,
            transient=True,  # Makes the live display disappear when done!
        ) as live:
            config.live_context = live
            try:
                yield LiveLogger(base_logger)
            finally:
                # Clean up: clear the live context and buffered messages
                config.live_context = None
                config.clear_live_messages()
    else:
        # Level 1+: Just print header and messages normally (not ephemeral)
        console = get_console()
        console.print(f'[bold blue]{message}[/bold blue]')
        yield LiveLogger(base_logger)


@contextmanager
def maybe_live_logging(
    message: str,
) -> Generator[LiveLogger | None, None, None]:
    """Provide a live logging context only when verbosity is 0.

    Args:
        message: Status message to display if live logging is active.

    Yields:
        LiveLogger when verbosity is 0, otherwise None for a no-op context.
    """
    config = get_config()
    if config.verbosity_level == 0:
        with live_logging(message) as live:
            yield live
    else:
        yield None
