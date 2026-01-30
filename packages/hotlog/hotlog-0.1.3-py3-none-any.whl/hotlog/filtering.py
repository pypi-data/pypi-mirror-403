"""Context filtering based on verbosity level and key prefixes."""

from typing import cast

from structlog.typing import EventDict

from hotlog.config import DEFAULT_PREFIXES, get_config


def _should_filter_key(key: str, verbosity_level: int) -> bool:
    """Check if a key should be filtered based on verbosity level.

    Note: This is only called for verbosity levels 0 and 1.
    Level 2+ returns early without filtering.

    Args:
        key: The dictionary key to check
        verbosity_level: Current verbosity level (0 or 1)

    Returns:
        True if the key should be filtered out, False to keep it
    """
    if verbosity_level == 0:
        # Default mode: filter out _verbose_ and _debug_
        return key.startswith(('_verbose_', '_debug_'))
    # Verbose mode (level 1): only filter out _debug_
    return key.startswith('_debug_')


def filter_context_by_prefix(event_dict: EventDict) -> EventDict:
    """Filter context dictionary based on key prefixes and verbosity level.

    - Level 0: Only keys without _verbose_ or _debug_ prefixes
    - Level 1: Keys without _debug_ prefix (includes _verbose_)
    - Level 2: All keys

    Prefixes are NOT stripped by this function - that's done by strip_prefixes_from_keys().

    Args:
        event_dict: Dictionary of context key-value pairs

    Returns:
        Filtered dictionary based on current verbosity level
    """
    config = get_config()

    if config.verbosity_level >= 2:
        # Debug mode: show everything
        return event_dict

    return {key: value for key, value in event_dict.items() if not _should_filter_key(key, config.verbosity_level)}


def _strip_prefix_from_key(raw_key: str, prefixes: tuple[str, ...]) -> str:
    for prefix in prefixes:
        if raw_key.startswith(prefix):
            stripped = raw_key.removeprefix(prefix)
            return stripped or raw_key
    return raw_key


def _strip_prefixes(value: object, prefixes: tuple[str, ...]) -> object:
    if isinstance(value, dict):
        return {
            _strip_prefix_from_key(key, prefixes): _strip_prefixes(
                val,
                prefixes,
            )
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_strip_prefixes(item, prefixes) for item in value]
    if isinstance(value, tuple):
        return tuple(_strip_prefixes(item, prefixes) for item in value)
    return value


def strip_prefixes_from_keys(event_dict: EventDict) -> EventDict:
    """Strip display prefixes from keys for cleaner output.

    Removes prefixes like _verbose_, _debug_, _perf_, _security_ from keys
    so they display cleanly in the output.

    Applies recursively for nested dictionaries and sequences, ensuring
    that deeply nested context also has prefixes removed.

    Args:
        event_dict: Dictionary with potentially prefixed keys

    Returns:
        Dictionary with clean keys (prefixes removed)

    Example:
        >>> strip_prefixes_from_keys({"_verbose_source": "file.py", "count": 42})
        {"source": "file.py", "count": 42}
    """
    prefixes = tuple(DEFAULT_PREFIXES)
    return cast('EventDict', _strip_prefixes(event_dict, prefixes))
