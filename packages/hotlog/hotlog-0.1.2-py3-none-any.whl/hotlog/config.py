"""Configuration and state management for hotlog."""

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.console import Console
from rich.live import Live

if TYPE_CHECKING:
    from hotlog.matchers import LogMatcher


# Default prefixes for context filtering
DEFAULT_PREFIXES = ['_verbose_', '_debug_', '_perf_', '_security_']


@dataclass
class HotlogConfig:
    """Configuration and state for hotlog.

    This holds all runtime state including verbosity level, matchers,
    and live context information.
    """

    verbosity_level: int = 0
    """Verbosity level (0=default, 1=verbose, 2=debug)"""

    matchers: list['LogMatcher'] = field(default_factory=list)
    """List of LogMatcher instances for custom formatting"""

    live_context: Live | None = None
    """Active Live context for level 0 ephemeral messages"""

    live_messages: list[tuple[str, str]] = field(default_factory=list)
    """Buffer of (message, context_yaml) tuples during live context"""

    def clear_live_messages(self) -> None:
        """Clear the live message buffer."""
        self.live_messages.clear()

    def append_live_message(self, message: str, context_yaml: str) -> None:
        """Append a message to the live buffer.

        Args:
            message: Formatted log message
            context_yaml: Formatted context YAML
        """
        self.live_messages.append((message, context_yaml))


# Global configuration instance
_config = HotlogConfig()


def get_config() -> HotlogConfig:
    """Get the global configuration instance.

    Returns:
        Global HotlogConfig instance
    """
    return _config


def get_console() -> Console:
    """Get a Console instance that writes to the current sys.stdout.

    This ensures compatibility with pytest's output capturing by always
    using the current sys.stdout, not a cached version. We don't force
    terminal mode but ensure output is not suppressed.
    """
    return Console(file=sys.stdout, force_jupyter=False)
