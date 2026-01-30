"""Log matchers for custom message formatting."""

from dataclasses import dataclass

from structlog.typing import EventDict


@dataclass
class LogMatcher:
    """Base class for log message matchers.

    Matchers allow custom formatting of log messages based on patterns.
    Subclass this to create custom matchers for specific log types.
    """

    def matches(self, level: str, event: str, event_dict: EventDict) -> bool:
        """Check if this matcher applies to the log message.

        Args:
            level: Log level (INFO, WARNING, etc.)
            event: Event message
            event_dict: Event context dictionary

        Returns:
            True if this matcher should handle the message
        """
        raise NotImplementedError

    def format(
        self,
        level: str,
        event: str,
        event_dict: EventDict,
    ) -> str | None:
        """Format the log message.

        Args:
            level: Log level
            event: Event message
            event_dict: Event context dictionary (will be modified)

        Returns:
            Formatted message string, or None to use default formatting
        """
        raise NotImplementedError


@dataclass
class ToolMatch(LogMatcher):
    """Matcher for tool execution logs (toolbelt style).

    Matches logs with specific event name and required keys,
    then formats them as: prefix[tool] => command

    Args:
        event: Event name to match (default: "executing")
        prefix: Prefix to show (default: "tb")
        level: Log level to match (default: "INFO")
        command_key: Key containing the command (default: "command")
        tool_key: Key containing the tool name (default: "tool")

    Example:
        >>> matcher = ToolMatch(event="executing", prefix="tb")
        >>> # Matches: logger.info("executing", command="ruff format", tool="ruff-format")
        >>> # Formats as: tb[ruff-format] => ruff format
    """

    event: str = 'executing'
    prefix: str = 'tb'
    level: str = 'INFO'
    command_key: str = 'command'
    tool_key: str = 'tool'

    def matches(self, level: str, event: str, event_dict: EventDict) -> bool:
        """Check if this is a tool execution log.

        Returns True if level, event, and command_key all match.
        """
        return level == self.level and event == self.event and self.command_key in event_dict

    def format(
        self,
        level: str,
        event: str,
        event_dict: EventDict,
    ) -> str | None:
        """Format as: prefix[tool] => command.

        Extracts command and tool from event_dict and formats with Rich markup.
        If no tool name is present, just shows the command.
        """
        del level, event
        command = event_dict.pop(self.command_key)
        tool_name = event_dict.pop(self.tool_key, '')

        if tool_name:
            return f'[bold #888888]{self.prefix}\\[{tool_name}] =>[/bold #888888] [blue]{command}[/blue]'
        return f'[blue]{command}[/blue]'
