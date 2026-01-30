"""Rich console singleton for kubepath.

Environment variables:
    KUBEPATH_PLAIN=1 - Disable ANSI colors and Rich formatting
    KUBEPATH_NO_CLEAR=1 - Prevent screen clearing (content accumulates)

Both are useful for automated testing with pexpect.
"""

import os

from rich.console import Console
from rich.theme import Theme

# Custom theme for kubepath
KUBEPATH_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "hint": "dim italic",
    "chapter": "bold magenta",
    "points": "bold yellow",
    "progress.complete": "cyan",
    "progress.remaining": "dim",
    # Gamification styles
    "level": "bold yellow",
    "streak": "cyan",
    "celebration": "bold magenta",
})

# Singleton console instance
_console: Console | None = None


def get_console() -> Console:
    """Get the singleton Rich console instance.

    Set KUBEPATH_PLAIN=1 environment variable for plain text output
    (useful for automated testing with pexpect).
    """
    global _console
    if _console is None:
        plain_mode = os.environ.get("KUBEPATH_PLAIN", "0") == "1"
        _console = Console(
            theme=KUBEPATH_THEME,
            force_terminal=not plain_mode,
            no_color=plain_mode,
        )
    return _console


def clear_screen() -> None:
    """Clear the screen, respecting KUBEPATH_NO_CLEAR mode.

    Set KUBEPATH_NO_CLEAR=1 to prevent screen clearing (useful for
    automated testing where you want to capture all content in the
    terminal buffer).

    In no-clear mode, prints a separator line instead of clearing.
    """
    console = get_console()
    no_clear = os.environ.get("KUBEPATH_NO_CLEAR", "0") == "1"

    if no_clear:
        # Print separator instead of clearing - allows content to accumulate
        console.print("\n" + "=" * 60 + "\n")
    else:
        console.clear()


def print_banner():
    """Print the kubepath welcome banner."""
    console = get_console()
    console.print(
        "[chapter]"
        r"""
    __          __                     __  __
   / /____  __ / /_   ___   ____  ____ _/ /_/ /_
  / //_/ / / // __ \ / _ \ / __ \/ __ `/ __/ __ \
 / ,<  / /_/ // /_/ //  __// /_/ / /_/ / /_/ / / /
/_/|_| \__,_//_.___/ \___// .___/\__,_/\__/_/ /_/
                        /_/
"""
        "[/chapter]"
    )
    console.print("[info]Learn Kubernetes interactively![/info]\n")
