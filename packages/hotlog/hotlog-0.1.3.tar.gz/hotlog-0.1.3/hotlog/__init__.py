"""hotlog: Generalized logging utility for Python projects.

Provides three levels of verbosity:
- Level 0 (default): Essential info with live updates that can disappear
- Level 1 (-v): More verbose, messages stay visible
- Level 2 (-vv): All debug messages, no live updates

Usage:
    from hotlog import (
        add_verbosity_argument,
        configure_logging,
        get_logger,
        resolve_verbosity,
        ToolMatch,
    )

    # In your CLI
    parser = argparse.ArgumentParser()
    add_verbosity_argument(parser)
    args = parser.parse_args()

    configure_logging(
        verbosity=resolve_verbosity(args),
        matchers=[
            ToolMatch(event="executing", prefix="tb")
        ]
    )
    logger = get_logger()
"""

import logging
from collections.abc import Callable

import structlog

# Import from refactored modules
from hotlog.config import get_config
from hotlog.live import LiveLogger, live_logging, maybe_live_logging
from hotlog.logger import get_logger, highlight
from hotlog.matchers import LogMatcher, ToolMatch
from hotlog.rendering import cli_renderer
from hotlog.verbosity import (
    add_verbosity_argument,
    get_verbosity_from_env,
    resolve_verbosity,
)

# Type alias for backward compatibility
Logger = structlog.types.FilteringBoundLogger


def configure_logging(
    verbosity: int = 0,
    renderer: Callable | None = None,
    matchers: list[LogMatcher] | None = None,
) -> None:
    """Configure structlog for hotlog.

    Args:
        verbosity: Verbosity level (0=default, 1=verbose, 2=debug)
                  - 0: Essential info only, supports live updates
                  - 1: More context, messages stay visible
                  - 2: All debug info, no live updates
        renderer: Custom renderer function (optional)
        matchers: List of LogMatcher instances for custom log formatting.
                 Example: [ToolMatch(event="executing", prefix="tb")]
    """
    # Update global state
    config = get_config()
    config.verbosity_level = verbosity
    config.matchers = matchers or []

    chosen_renderer = renderer or cli_renderer

    # Reset structlog to clear any cached loggers
    structlog.reset_defaults()

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt='ISO', utc=False),
            structlog.stdlib.add_log_level,
            chosen_renderer,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

    # Set log level based on verbosity
    # Clear existing handlers and set up a basic console handler
    root_logger = logging.getLogger()
    root_logger.handlers = []  # Clear existing handlers
    root_logger.setLevel(logging.DEBUG if verbosity >= 2 else logging.INFO)


# Public API
__all__ = [
    'LiveLogger',
    'LogMatcher',
    'Logger',
    'ToolMatch',
    'add_verbosity_argument',
    'configure_logging',
    'get_logger',
    'get_verbosity_from_env',
    'highlight',
    'live_logging',
    'maybe_live_logging',
    'resolve_verbosity',
]
