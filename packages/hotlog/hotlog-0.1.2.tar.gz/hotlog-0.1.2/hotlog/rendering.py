"""Log message rendering with support for matchers, filtering, and live display."""

from rich.syntax import Syntax
from structlog.types import FilteringBoundLogger
from structlog.typing import EventDict

from hotlog.config import get_config, get_console
from hotlog.filtering import filter_context_by_prefix, strip_prefixes_from_keys
from hotlog.formatting import (
    format_context_yaml,
    format_log_message,
    pre_process_log,
)


def apply_matchers(
    level: str,
    event_msg: str,
    event_dict: EventDict,
) -> str | None:
    """Try to match and format message using registered matchers.

    Iterates through all registered matchers and returns the first match.

    Args:
        level: Log level (INFO, WARNING, etc.)
        event_msg: The event message
        event_dict: Context dictionary (may be modified by matcher)

    Returns:
        Formatted message string if a matcher handled it, None otherwise
    """
    config = get_config()
    for matcher in config.matchers:
        if matcher.matches(level, event_msg, event_dict):
            formatted = matcher.format(level, event_msg, event_dict)
            if formatted is not None:
                return formatted
    return None


def _format_live_display(live_messages: list[tuple[str, str]]) -> str:
    """Format live messages for display.

    Args:
        live_messages: List of (message, context) tuples

    Returns:
        Formatted string with messages and indented context
    """
    display_lines = []
    for msg, ctx in live_messages:
        display_lines.append(msg)
        if ctx:
            # Indent context for better readability
            display_lines.extend(f'  {line}' for line in ctx.split('\n'))
    return '\n'.join(display_lines)


def handle_live_buffering(
    log_msg: str,
    context_yaml: str,
    *,
    is_live_message: bool,
) -> bool:
    """Handle buffering of messages for live display.

    At level 0 with live context active, messages marked as _live_ are buffered
    and displayed in the live area. They disappear when the live context ends.

    Args:
        log_msg: Formatted log message
        context_yaml: Formatted context
        is_live_message: Whether this is a live message

    Returns:
        True if message was buffered (don't print), False if should print normally
    """
    config = get_config()

    if not (is_live_message and config.live_context is not None and config.verbosity_level == 0):
        return False  # Should print normally

    # At level 0 with live context: buffer messages
    config.append_live_message(log_msg, context_yaml)

    # Update live display to show buffered messages
    if config.live_messages:
        config.live_context.update(_format_live_display(config.live_messages))

    return True  # Message was buffered


def render_output(log_msg: str, context_yaml: str) -> None:
    """Render the formatted message and context to console.

    Args:
        log_msg: Formatted log message with Rich markup
        context_yaml: Formatted context YAML
    """
    console = get_console()
    console.print(log_msg)

    if context_yaml:
        syntax = Syntax(
            context_yaml,
            'yaml',
            theme='github-dark',
            background_color='default',
            line_numbers=False,
        )
        console.print(syntax)


def cli_renderer(
    _logger: FilteringBoundLogger,
    method_name: str,
    event_dict: EventDict,
) -> str:
    """Render log messages for CLI output using rich formatting.

    This is the main rendering pipeline that orchestrates:
    1. Pre-processing (removing internal keys)
    2. Matcher application (custom formatting)
    3. Filtering (verbosity-based)
    4. Formatting (default style)
    5. Live buffering (level 0 only)
    6. Output rendering

    Args:
        _logger: The logger instance.
        method_name: The logging method name (e.g., 'info', 'error').
        event_dict: The event dictionary containing log data.

    Returns:
        str: An empty string, as structlog expects a string return but output is printed.
    """
    config = get_config()
    level = method_name.upper()
    event_msg = event_dict.pop('event', '')

    # Optional display level gating (_display_level: 0,1,2)
    required_display_level = None
    display_raw = event_dict.pop('_display_level', None)
    if display_raw is not None:
        try:
            required_display_level = int(display_raw)
        except (TypeError, ValueError):
            required_display_level = None
        else:
            required_display_level = max(0, min(2, required_display_level))

    if required_display_level is not None and config.verbosity_level < required_display_level:
        return ''

    # Check if this is a live message (should be buffered at level 0)
    is_live_message = event_dict.pop('_live_', False)

    # Pre-process to remove internal keys
    event_msg = pre_process_log(event_msg, event_dict)

    # Try matchers first for custom formatting
    log_msg = apply_matchers(level, event_msg, event_dict)

    # If no matcher handled it, use default formatting
    if log_msg is None:
        # Filter context based on verbosity level
        event_dict = filter_context_by_prefix(event_dict)

        # Always strip prefixes for clean display
        event_dict = strip_prefixes_from_keys(event_dict)

        # Format the message with level-appropriate styling
        log_msg = format_log_message(level, event_msg)
    else:
        # Matcher provided formatting, still need to process context
        event_dict = filter_context_by_prefix(event_dict)
        event_dict = strip_prefixes_from_keys(event_dict)

    # Format context as YAML
    context_yaml = format_context_yaml(event_dict)

    # Check if we should buffer this message (live context at level 0)
    if handle_live_buffering(
        log_msg,
        context_yaml,
        is_live_message=is_live_message,
    ):
        # Message was buffered, don't print
        return ''

    # Normal mode or level 1+: print to console directly
    render_output(log_msg, context_yaml)

    return ''  # structlog expects a string return, but we already printed
