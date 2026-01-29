"""Terminal image display with fallback chain."""

import base64
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path


def detect_terminal() -> str:
    """Detect terminal type for image display capabilities.

    Returns:
        Terminal identifier: "iterm2", "kitty", "wezterm", "mintty", or "unknown"
    """
    term_program = os.environ.get("TERM_PROGRAM", "").lower()

    if "iterm" in term_program:
        return "iterm2"
    if os.environ.get("KITTY_WINDOW_ID"):
        return "kitty"
    if "wezterm" in term_program:
        return "wezterm"
    if "mintty" in term_program:
        return "mintty"

    return "unknown"


def display_iterm2_image(image_path: Path, width: str = "auto") -> None:
    """Display image using iTerm2 inline image protocol.

    Also works for WezTerm and Mintty which support the same protocol.
    """
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    # iTerm2 escape sequence for inline images
    osc = f"\033]1337;File=inline=1;width={width}:{image_data}\a"
    sys.stdout.write(osc)
    sys.stdout.flush()
    print()  # Newline after image


def display_kitty_image(image_path: Path) -> None:
    """Display image using Kitty graphics protocol."""
    subprocess.run(
        ["kitty", "+kitten", "icat", str(image_path)],
        check=True,
    )


def display_with_timg(image_path: Path) -> None:
    """Display image using timg tool."""
    subprocess.run(
        ["timg", "-g", "80x40", str(image_path)],
        check=True,
    )


def display_with_chafa(image_path: Path) -> None:
    """Display image using chafa tool (Unicode/ANSI art)."""
    subprocess.run(
        ["chafa", "--size=80x40", str(image_path)],
        check=True,
    )


def open_in_browser(image_path: Path) -> None:
    """Open image in default browser/viewer."""
    webbrowser.open(f"file://{image_path.absolute()}")


def display_image(image_path: Path, force_browser: bool = False) -> bool:
    """Display image in terminal with fallback strategy.

    Tries in order:
    1. Native terminal protocols (iTerm2, Kitty, WezTerm)
    2. External tools (timg, chafa)
    3. Browser (last resort)

    Always prints the file path for full-quality viewing.

    Args:
        image_path: Path to the image file
        force_browser: Skip terminal display and open in browser

    Returns:
        True if displayed in terminal, False if opened in browser
    """
    displayed_in_terminal = False

    if not force_browser:
        terminal = detect_terminal()

        # Try native terminal protocols
        if terminal in ("iterm2", "wezterm", "mintty"):
            try:
                display_iterm2_image(image_path)
                displayed_in_terminal = True
            except Exception:
                pass

        if not displayed_in_terminal and terminal == "kitty":
            try:
                display_kitty_image(image_path)
                displayed_in_terminal = True
            except Exception:
                pass

        # Try external tools
        if not displayed_in_terminal and shutil.which("timg"):
            try:
                display_with_timg(image_path)
                displayed_in_terminal = True
            except Exception:
                pass

        if not displayed_in_terminal and shutil.which("chafa"):
            try:
                display_with_chafa(image_path)
                displayed_in_terminal = True
            except Exception:
                pass

    # Always show the path for full quality preview
    print(f"\n  Full preview: file://{image_path.absolute()}")

    # Open in browser if requested or no terminal display worked
    if force_browser or not displayed_in_terminal:
        open_in_browser(image_path)

    return displayed_in_terminal
