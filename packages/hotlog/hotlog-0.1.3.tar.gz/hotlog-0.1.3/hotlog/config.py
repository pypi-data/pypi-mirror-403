"""Configuration and state management for hotlog."""

import os
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.console import Console
from rich.live import Live

from hotlog.verbosity import is_env_var_true

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
    using the current sys.stdout, not a cached version. We force terminal
    mode for CI color output, but disable it during tests to ensure
    live logging works properly in captured output.

    The behavior can be overridden with HOTLOG_FORCE_TERMINAL env var:
    - HOTLOG_FORCE_TERMINAL=1 or true: Always force terminal mode
    - HOTLOG_FORCE_TERMINAL=0 or false: Never force terminal mode
    - Not set: Auto-detect (disable in tests, enable otherwise)
    """
    # Check for explicit user override first
    if 'HOTLOG_FORCE_TERMINAL' in os.environ:
        force_terminal = is_env_var_true('HOTLOG_FORCE_TERMINAL')
    else:
        # Auto-detect: disable during tests, enable otherwise
        force_terminal = True
        if 'pytest' in sys.modules or any(key.startswith('PYTEST_') for key in os.environ):
            force_terminal = False

    return Console(
        file=sys.stdout,
        force_jupyter=False,
        force_terminal=force_terminal,
    )
