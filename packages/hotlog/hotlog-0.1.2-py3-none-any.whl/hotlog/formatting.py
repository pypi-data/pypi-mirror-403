"""Message and context formatting utilities."""

import yaml
from structlog.typing import EventDict


def format_context_yaml(event_dict: EventDict, indent: int = 2) -> str:
    r"""Format the context dictionary as YAML.

    Args:
        event_dict: The context dictionary to format.
        indent: The number of spaces to use for indentation.

    Returns:
        The formatted YAML string, or empty string if event_dict is empty.

    Example:
        >>> format_context_yaml({"count": 42, "name": "test"})
        '  count: 42\n  name: test'
    """
    if not event_dict:
        return ''
    context_yaml = yaml.safe_dump(
        event_dict,
        sort_keys=True,
        default_flow_style=False,
    )
    pad = ' ' * indent
    return '\n'.join(f'{pad}{line}' for line in context_yaml.splitlines())


def pre_process_log(event_msg: str, event_dict: EventDict) -> str:
    """Remove internal structlog keys from event dictionary.

    Removes keys that are added by structlog internals and shouldn't
    be displayed to the user.

    Args:
        event_msg: The main event message.
        event_dict: The event dictionary containing additional context.
            This dictionary is modified in-place.

    Returns:
        The event message (unchanged).
    """
    # Remove internal structlog keys
    for key in ('timestamp', 'level', 'log_level', 'event'):
        event_dict.pop(key, None)
    return event_msg


def format_log_message(level: str, event_msg: str) -> str:
    """Format a log message with appropriate styling based on level.

    Args:
        level: Log level (INFO, WARNING, ERROR, DEBUG, EXCEPTION, etc.)
        event_msg: The message text

    Returns:
        Formatted message with Rich markup

    Example:
        >>> format_log_message("INFO", "Processing data")
        '[blue]Processing data[/blue]'
        >>> format_log_message("ERROR", "Failed to connect")
        '[bold red]ERROR:[/bold red] [red]Failed to connect[/red]'
        >>> format_log_message("EXCEPTION", "Operation failed")
        '[bold red]EXCEPTION:[/bold red] [red]Operation failed[/red]'
    """
    # Map log levels to colors/styles
    level_styles = {
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'DEBUG': 'magenta',
        'CRITICAL': 'white on red',
        'SUCCESS': 'green',
        'EXCEPTION': 'red',  # Same style as ERROR
    }

    # Pick style, fallback to bold cyan for unknown
    style = level_styles.get(level, 'bold cyan')

    # Clean output without level prefix (uv style)
    if level == 'DEBUG':
        # Show DEBUG prefix only in debug mode
        return f'[{style}]DEBUG[/{style}] [{style}]{event_msg}[/{style}]'
    if level in ('WARNING', 'ERROR', 'CRITICAL', 'EXCEPTION'):
        # Show level for warnings, errors, exceptions (important)
        return f'[bold {style}]{level}:[/bold {style}] [{style}]{event_msg}[/{style}]'
    # INFO and SUCCESS: no prefix, just the message
    return f'[{style}]{event_msg}[/{style}]'
