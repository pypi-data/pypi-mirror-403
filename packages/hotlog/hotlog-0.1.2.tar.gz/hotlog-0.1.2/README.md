# hotlog

Generalized logging utility for Python projects

## Overview

`hotlog` provides a simple, flexible, and structured logging interface for
Python applications and libraries. It wraps `structlog` and `rich` to offer:

- **Three-level verbosity system** for controlling output detail
- **Rich colored output** with YAML-formatted context
- **Live logging support** for dynamic status updates (at default level)
- **Context-aware logging** with prefix-based filtering (`_verbose_`, `_debug_`)
- **Unified API**: `from hotlog import get_logger, configure_logging`
- Works seamlessly in CLI tools, scripts, and libraries

## Features

### Three Verbosity Levels

- **Level 0 (default)**: Essential info only, supports live updates that
  disappear
- **Level 1 (-v)**: More context visible, includes `_verbose_` prefixed keys
- **Level 2 (-vv)**: All debug info, includes `_debug_` prefixed keys, no live
  updates

### Prefix Filtering

Control which context appears at different verbosity levels by using key
prefixes:

- Regular keys (no prefix): Always shown at all levels
- `_verbose_key`: Only shown at level 1 (`-v`) or 2 (`-vv`)
- `_debug_key`: Only shown at level 2 (`-vv`)

**The prefixes are automatically removed** when displayed, so `_verbose_source`
becomes `source`.

```python
logger.info(
    "Processing dataset",
    records=1000,                    # Always shown
    _verbose_source="data.csv",      # Only at -v or -vv
    _debug_file_size="2.5MB"         # Only at -vv
)
```

**No special configuration needed** - just prefix your keys and hotlog handles
the rest!

### Visibility Gating with `_display_level`

Sometimes you want to hide entire events unless the user explicitly opts into
higher verbosity. Add `_display_level` to the event context to specify the
minimum verbosity (0, 1, or 2) required to display it:

```python
logger.info("download_entry_start", entry=item.name, _display_level=1)
```

- Messages log as normal when the active verbosity (set via `configure_logging`
  or environment detection) is **at least** `_display_level`.
- When the required level is higher than the active verbosity, the event is
  skipped entirely. The key is removed before rendering, so it never appears in
  the formatted output.
- `_display_level` complements `_verbose_*`/`_debug_*` prefixes—use it to gate
  whole events, while prefixes still gate individual context values.

### Custom Log Matchers

Configure custom formatting rules for specific log patterns using matchers.
Matchers check if a log entry matches certain conditions and apply custom
formatting.

#### Built-in Matchers

**ToolMatch**: Format tool execution logs (toolbelt style)

```python
from hotlog import configure_logging, get_logger, ToolMatch

# Configure with ToolMatch
configure_logging(
    verbosity=0,
    matchers=[
        ToolMatch(event="executing", prefix="tb")
    ]
)
logger = get_logger(__name__)

# Automatically formats as: tb[ruff-format] => ruff format .
logger.info(
    "executing",
    command="ruff format .",
    tool="ruff-format",
    _verbose_files_changed=14
)
```

The ToolMatch matcher checks for:

- Event name: `"executing"` (configurable)
- Log level: `"INFO"` (configurable)
- Required key: `command`
- Optional key: `tool` (shows in brackets)

Customize the matcher:

```python
ToolMatch(
    event="executing",      # Event name to match
    prefix="pkg",          # Prefix shown before tool name
    level="INFO",          # Log level to match
    command_key="command", # Key containing command
    tool_key="tool"        # Key containing tool name
)
```

#### Creating Custom Matchers

Extend `LogMatcher` to create your own formatting rules:

```python
from hotlog import LogMatcher, configure_logging, get_logger
from structlog.typing import EventDict
from typing import Optional

class InstallMatch(LogMatcher):
    """Custom matcher for package installation logs."""
    
    def matches(self, level: str, event: str, event_dict: EventDict) -> bool:
        """Check if this log entry matches our pattern."""
        return (
            level == "INFO" and
            event == "installed" and
            "package" in event_dict
        )
    
    def format(self, level: str, event: str, event_dict: EventDict) -> Optional[str]:
        """Format matching log entries.
        
        Note: Extract and remove keys you use from event_dict.
        Return None to fall back to default formatting.
        """
        package = event_dict.pop("package")
        version = event_dict.pop("version", "unknown")
        
        return f'[green]✓[/green] Installed [bold]{package}[/bold] [dim](version {version})[/dim]'

# Use your custom matcher
configure_logging(
    verbosity=0,
    matchers=[
        InstallMatch(),
        ToolMatch(event="executing", prefix="pkg"),
    ]
)
logger = get_logger(__name__)

# This will use InstallMatch formatting
logger.info("installed", package="requests", version="2.31.0")

# This will use ToolMatch formatting
logger.info("executing", command="uv pip install requests", tool="uv")

# This will use default formatting
logger.info("Build completed")
```

**Key points about custom matchers:**

- Matchers are checked in order - first match wins
- Use `event_dict.pop()` to remove keys you've formatted
- Return `None` to fall back to default formatting
- Remaining context keys are shown as YAML below the message
- Rich markup is supported in formatted strings

### Rich Output

- Colored log levels (INFO=blue, WARNING=yellow, ERROR=red, DEBUG=magenta)
- YAML-formatted context for easy reading
- Syntax highlighting for structured data
- Clean output without log level prefixes (like `uv`) - set `show_levels=True`
  for traditional `[INFO]` style

### Highlighting Important Information

Emphasize specific values in your messages using Rich markup or the
`highlight()` helper:

```python
from hotlog import get_logger, highlight

logger = get_logger(__name__)

# Option 1: Direct Rich markup
logger.info("Installed [bold]5 packages[/bold] in [bold]3ms[/bold]")

# Option 2: Using highlight() helper
logger.info(highlight("Downloaded {} in {}", "14 files", "2.5s"))
# Renders as: "Downloaded [bold]14 files[/bold] in [bold]2.5s[/bold]"
```

This is perfect for level 0 summaries where you want to emphasize key metrics
while keeping the output clean.

### Live Logging

Use the `live_logging` context manager for operations with progress updates
(level 0 only):

```python
with live_logging("Downloading..."):
    # Your operation here
    logger.info("Connected", host="example.com")
```

### Conditional Live Logging Helper

When you only want live updates at verbosity 0, use
`maybe_live_logging(message)`:

```python
from hotlog import maybe_live_logging

with maybe_live_logging("Downloading repos...") as live:
        if live:
                live.info("Downloading", name=repo)
```

- At verbosity 0, it delegates to `live_logging()` and yields a `LiveLogger`.
- At verbosity 1 or 2, it yields `None` without printing anything, so you can
  skip live output and avoid extra branching in your code.

## Usage

### Basic Example

```python
from hotlog import configure_logging, get_logger

# Configure logging (verbosity: 0, 1, or 2)
configure_logging(verbosity=0)
logger = get_logger(__name__)

# Log messages
logger.info("Starting process", task_id=123)
logger.info("Processing data", records=100, _verbose_source="db.sqlite")
logger.warning("Rate limit approaching", current=95, limit=100)
```

### With Different Verbosity Levels

```python
# Level 0: Only essential info
configure_logging(verbosity=0)
logger.info("Processing", items=10, _verbose_detail="xyz", _debug_internals="abc")
# Output: items=10 only

# Level 1: Include verbose context
configure_logging(verbosity=1)
logger.info("Processing", items=10, _verbose_detail="xyz", _debug_internals="abc")
# Output: items=10, detail="xyz"

# Level 2: Include all debug context
configure_logging(verbosity=2)
logger.info("Processing", items=10, _verbose_detail="xyz", _debug_internals="abc")
# Output: items=10, detail="xyz", internals="abc"
```

### Live Logging Example

```python
from hotlog import configure_logging, get_logger, live_logging
import time

configure_logging(verbosity=0)
logger = get_logger(__name__)

with live_logging("Downloading repository..."):
    time.sleep(1)
    logger.info("Connected to server")
    time.sleep(1)
    logger.info("Fetching metadata")
    
logger.info("Download completed")
```

### CLI Integration

```python
import argparse
from hotlog import configure_logging, get_logger

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action='count', default=0)
args = parser.parse_args()

# Map -v/-vv to verbosity levels
configure_logging(verbosity=min(args.verbose, 2))
logger = get_logger(__name__)
```

## Installation

```bash
# Install dependencies (adjust based on your package manager)
pip install structlog rich pyyaml
```

## Why hotlog?

Hotlog standardizes logging across multiple projects and CLIs, making it easy
to:

- Provide consistent verbosity control
- Display beautiful, readable logs
- Handle live updates for better UX
- Filter context based on user's needs
- Customize log formatting with matchers

No more reinventing logging configuration for every project!

## Examples

See the `example_*.py` files for more usage patterns:

- `example_quickstart.py` - Comprehensive quick start guide
- `example_cli.py` - Full CLI simulation
- `example_toolbelt.py` - Tool execution logging with ToolMatch
- `example_custom_matcher.py` - Creating custom matchers
- `example_highlight.py` - Using highlight() and Rich markup
- `example_prefixes.py` - Prefix filtering demonstration

Run examples with different verbosity levels:

```bash
python example_toolbelt.py      # Level 0 (default)
python example_toolbelt.py -v   # Level 1 (verbose)
python example_toolbelt.py -vv  # Level 2 (debug)
```
