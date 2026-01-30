"""
Terminal utilities for ChromaForge.

Provides terminal detection, cursor control, and screen manipulation.
"""

import os
import sys
import re
from typing import Tuple, Optional, List


ESC = "\033["

# ANSI escape sequence pattern
_ANSI_PATTERN = re.compile(r"(\033\[[0-9;]*[a-zA-Z]|\033\].*?\007)")


class Terminal:
    """
    Terminal utility class for advanced terminal operations.

    Example:
        term = Terminal()
        term.clear()
        term.move_to(10, 5)
        print("Hello at position (10, 5)")
    """

    def __init__(self):
        self._saved_cursor = None

    @staticmethod
    def size() -> Tuple[int, int]:
        """Get terminal size (columns, rows)."""
        try:
            size = os.get_terminal_size()
            return size.columns, size.lines
        except OSError:
            return 80, 24

    @property
    def width(self) -> int:
        """Get terminal width."""
        return self.size()[0]

    @property
    def height(self) -> int:
        """Get terminal height."""
        return self.size()[1]

    @staticmethod
    def clear() -> None:
        """Clear the entire screen."""
        sys.stdout.write(f"{ESC}2J{ESC}H")
        sys.stdout.flush()

    @staticmethod
    def clear_line() -> None:
        """Clear the current line."""
        sys.stdout.write(f"{ESC}2K\r")
        sys.stdout.flush()

    @staticmethod
    def clear_to_end() -> None:
        """Clear from cursor to end of screen."""
        sys.stdout.write(f"{ESC}J")
        sys.stdout.flush()

    @staticmethod
    def clear_to_start() -> None:
        """Clear from cursor to start of screen."""
        sys.stdout.write(f"{ESC}1J")
        sys.stdout.flush()

    @staticmethod
    def move_to(x: int, y: int) -> None:
        """Move cursor to position (x, y). 1-indexed."""
        sys.stdout.write(f"{ESC}{y};{x}H")
        sys.stdout.flush()

    @staticmethod
    def move_up(n: int = 1) -> None:
        """Move cursor up n lines."""
        sys.stdout.write(f"{ESC}{n}A")
        sys.stdout.flush()

    @staticmethod
    def move_down(n: int = 1) -> None:
        """Move cursor down n lines."""
        sys.stdout.write(f"{ESC}{n}B")
        sys.stdout.flush()

    @staticmethod
    def move_right(n: int = 1) -> None:
        """Move cursor right n columns."""
        sys.stdout.write(f"{ESC}{n}C")
        sys.stdout.flush()

    @staticmethod
    def move_left(n: int = 1) -> None:
        """Move cursor left n columns."""
        sys.stdout.write(f"{ESC}{n}D")
        sys.stdout.flush()

    @staticmethod
    def move_to_column(n: int) -> None:
        """Move cursor to column n."""
        sys.stdout.write(f"{ESC}{n}G")
        sys.stdout.flush()

    @staticmethod
    def save_cursor() -> None:
        """Save current cursor position."""
        sys.stdout.write(f"{ESC}s")
        sys.stdout.flush()

    @staticmethod
    def restore_cursor() -> None:
        """Restore saved cursor position."""
        sys.stdout.write(f"{ESC}u")
        sys.stdout.flush()

    @staticmethod
    def hide_cursor() -> None:
        """Hide the cursor."""
        sys.stdout.write(f"{ESC}?25l")
        sys.stdout.flush()

    @staticmethod
    def show_cursor() -> None:
        """Show the cursor."""
        sys.stdout.write(f"{ESC}?25h")
        sys.stdout.flush()

    @staticmethod
    def set_title(title: str) -> None:
        """Set the terminal window title."""
        sys.stdout.write(f"{ESC}]0;{title}\007")
        sys.stdout.flush()

    @staticmethod
    def bell() -> None:
        """Ring the terminal bell."""
        sys.stdout.write("\007")
        sys.stdout.flush()

    @staticmethod
    def scroll_up(n: int = 1) -> None:
        """Scroll the screen up n lines."""
        sys.stdout.write(f"{ESC}{n}S")
        sys.stdout.flush()

    @staticmethod
    def scroll_down(n: int = 1) -> None:
        """Scroll the screen down n lines."""
        sys.stdout.write(f"{ESC}{n}T")
        sys.stdout.flush()

    @staticmethod
    def enable_alt_buffer() -> None:
        """Switch to alternate screen buffer."""
        sys.stdout.write(f"{ESC}?1049h")
        sys.stdout.flush()

    @staticmethod
    def disable_alt_buffer() -> None:
        """Switch back to main screen buffer."""
        sys.stdout.write(f"{ESC}?1049l")
        sys.stdout.flush()

    def fullscreen(self) -> "FullscreenContext":
        """Context manager for fullscreen mode."""
        return FullscreenContext(self)


class FullscreenContext:
    """Context manager for fullscreen terminal mode."""

    def __init__(self, terminal: Terminal):
        self.terminal = terminal

    def __enter__(self):
        self.terminal.enable_alt_buffer()
        self.terminal.hide_cursor()
        self.terminal.clear()
        return self.terminal

    def __exit__(self, *args):
        self.terminal.show_cursor()
        self.terminal.disable_alt_buffer()


def supports_color() -> bool:
    """Check if the terminal supports color."""
    if os.environ.get("NO_COLOR"):
        return False

    if os.environ.get("FORCE_COLOR"):
        return True

    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False

    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False

    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return os.environ.get("ANSICON") is not None

    return True


def supports_truecolor() -> bool:
    """Check if the terminal supports true color (24-bit)."""
    if not supports_color():
        return False

    colorterm = os.environ.get("COLORTERM", "")
    if colorterm in ("truecolor", "24bit"):
        return True

    term = os.environ.get("TERM", "")
    truecolor_terms = [
        "xterm-256color", "xterm-direct", "tmux-256color",
        "screen-256color", "vte-256color", "gnome-256color",
        "konsole-256color", "alacritty", "kitty", "wezterm",
    ]

    for tc_term in truecolor_terms:
        if tc_term in term:
            return True

    if sys.platform == "win32":
        return os.environ.get("WT_SESSION") is not None

    return False


def supports_unicode() -> bool:
    """Check if the terminal supports Unicode."""
    encoding = getattr(sys.stdout, "encoding", "") or ""
    if "utf" in encoding.lower():
        return True

    lang = os.environ.get("LANG", "")
    if "utf" in lang.lower():
        return True

    return False


def get_terminal_size() -> Tuple[int, int]:
    """Get terminal size (columns, rows)."""
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return 80, 24


def clear() -> None:
    """Clear the terminal screen."""
    Terminal.clear()


def clear_line() -> None:
    """Clear the current line."""
    Terminal.clear_line()


def move_cursor(x: int, y: int) -> None:
    """Move cursor to position (x, y)."""
    Terminal.move_to(x, y)


def hide_cursor() -> None:
    """Hide the cursor."""
    Terminal.hide_cursor()


def show_cursor() -> None:
    """Show the cursor."""
    Terminal.show_cursor()


def set_title(title: str) -> None:
    """Set the terminal window title."""
    Terminal.set_title(title)


class ANSIString:
    """
    A string class that properly handles ANSI escape sequences.

    Provides accurate length calculation, slicing, and truncation
    while preserving all ANSI formatting codes.

    Example:
        s = ANSIString("\033[31mHello\033[0m World")
        print(s.visible_length())  # 11
        print(s[:5])  # "\033[31mHello\033[0m" - properly closed
        print(s.truncate(8, "..."))  # "\033[31mHello\033[0m..."
    """

    def __init__(self, text: str):
        self._raw = text
        self._segments = self._parse(text)

    def _parse(self, text: str) -> List[dict]:
        """Parse text into segments of visible text and ANSI codes."""
        segments = []
        pos = 0
        current_codes = []

        for match in _ANSI_PATTERN.finditer(text):
            # Add any text before this ANSI code
            if match.start() > pos:
                visible_text = text[pos:match.start()]
                segments.append({
                    "type": "text",
                    "content": visible_text,
                    "codes": current_codes.copy()
                })

            # Process the ANSI code
            code = match.group()
            if code == "\033[0m" or code == "\033[m":
                # Reset code - clear all active codes
                current_codes = []
            elif code.startswith("\033["):
                # SGR code - add to active codes
                current_codes.append(code)

            segments.append({
                "type": "ansi",
                "content": code,
                "codes": []
            })

            pos = match.end()

        # Add remaining text
        if pos < len(text):
            segments.append({
                "type": "text",
                "content": text[pos:],
                "codes": current_codes.copy()
            })

        return segments

    def visible_length(self) -> int:
        """Get the visible length (excluding ANSI codes)."""
        length = 0
        for segment in self._segments:
            if segment["type"] == "text":
                length += len(segment["content"])
        return length

    def __len__(self) -> int:
        """Return visible length."""
        return self.visible_length()

    def __str__(self) -> str:
        """Return the raw string."""
        return self._raw

    def __repr__(self) -> str:
        return f"ANSIString({self._raw!r})"

    def strip_ansi(self) -> str:
        """Return text with all ANSI codes removed."""
        result = []
        for segment in self._segments:
            if segment["type"] == "text":
                result.append(segment["content"])
        return "".join(result)

    def slice(self, start: int, end: Optional[int] = None) -> str:
        """
        Slice the string by visible character positions.
        Preserves and properly closes ANSI codes.
        """
        if end is None:
            end = self.visible_length()

        if start < 0:
            start = max(0, self.visible_length() + start)
        if end < 0:
            end = max(0, self.visible_length() + end)

        result = []
        current_pos = 0
        active_codes = []
        needs_reset = False

        for segment in self._segments:
            if segment["type"] == "ansi":
                code = segment["content"]
                if current_pos >= start and current_pos < end:
                    result.append(code)
                    if code == "\033[0m" or code == "\033[m":
                        active_codes = []
                        needs_reset = False
                    else:
                        active_codes.append(code)
                        needs_reset = True
                elif current_pos < start:
                    # Track codes that are active before our slice starts
                    if code == "\033[0m" or code == "\033[m":
                        active_codes = []
                    else:
                        active_codes.append(code)
            else:
                text = segment["content"]
                text_start = current_pos
                text_end = current_pos + len(text)

                # Calculate the portion of this text segment to include
                slice_start = max(0, start - text_start)
                slice_end = min(len(text), end - text_start)

                if slice_start < slice_end:
                    # We need to include part of this text
                    if current_pos < start and active_codes:
                        # Add active codes at the start of our slice
                        result.extend(active_codes)
                        needs_reset = True

                    result.append(text[slice_start:slice_end])

                current_pos = text_end

        # Close any open ANSI codes
        if needs_reset:
            result.append("\033[0m")

        return "".join(result)

    def __getitem__(self, key):
        """Support slicing with [] notation."""
        if isinstance(key, slice):
            start = key.start or 0
            stop = key.stop
            return self.slice(start, stop)
        elif isinstance(key, int):
            if key < 0:
                key = self.visible_length() + key
            return self.slice(key, key + 1)
        raise TypeError(f"indices must be integers or slices, not {type(key).__name__}")

    def truncate(self, width: int, suffix: str = "...", preserve_ansi: bool = True) -> str:
        """
        Truncate to fit within width, with optional suffix.
        Properly preserves and closes ANSI codes.

        Args:
            width: Maximum visible width
            suffix: String to append if truncated (default "...")
            preserve_ansi: Whether to preserve ANSI codes (default True)

        Returns:
            Truncated string with proper ANSI handling
        """
        visible_len = self.visible_length()

        if visible_len <= width:
            return self._raw

        suffix_len = len(suffix)
        if width <= suffix_len:
            return suffix[:width]

        target_len = width - suffix_len

        if preserve_ansi:
            truncated = self.slice(0, target_len)
            # Ensure we end with a reset before the suffix
            if not truncated.endswith("\033[0m"):
                truncated += "\033[0m"
            return truncated + suffix
        else:
            return self.strip_ansi()[:target_len] + suffix

    def center(self, width: int, fillchar: str = " ") -> str:
        """Center the string, preserving ANSI codes."""
        visible_len = self.visible_length()
        if visible_len >= width:
            return self._raw

        padding = width - visible_len
        left_pad = padding // 2
        right_pad = padding - left_pad

        return fillchar * left_pad + self._raw + fillchar * right_pad

    def ljust(self, width: int, fillchar: str = " ") -> str:
        """Left-justify the string, preserving ANSI codes."""
        visible_len = self.visible_length()
        if visible_len >= width:
            return self._raw

        return self._raw + fillchar * (width - visible_len)

    def rjust(self, width: int, fillchar: str = " ") -> str:
        """Right-justify the string, preserving ANSI codes."""
        visible_len = self.visible_length()
        if visible_len >= width:
            return self._raw

        return fillchar * (width - visible_len) + self._raw

    def wrap(self, width: int) -> List[str]:
        """
        Wrap text to specified width, preserving ANSI codes.

        Returns list of lines, each properly handling ANSI codes.
        """
        lines = []
        current_line = []
        current_width = 0
        active_codes = []

        for segment in self._segments:
            if segment["type"] == "ansi":
                code = segment["content"]
                current_line.append(code)
                if code == "\033[0m" or code == "\033[m":
                    active_codes = []
                else:
                    active_codes.append(code)
            else:
                words = segment["content"].split(" ")
                for i, word in enumerate(words):
                    word_len = len(word)
                    space_needed = 1 if current_width > 0 else 0

                    if current_width + space_needed + word_len > width and current_width > 0:
                        # Start new line
                        if active_codes:
                            current_line.append("\033[0m")
                        lines.append("".join(current_line))
                        current_line = []
                        if active_codes:
                            current_line.extend(active_codes)
                        current_width = 0
                        space_needed = 0

                    if space_needed:
                        current_line.append(" ")
                        current_width += 1

                    current_line.append(word)
                    current_width += word_len

        if current_line:
            if active_codes:
                current_line.append("\033[0m")
            lines.append("".join(current_line))

        return lines


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return _ANSI_PATTERN.sub("", text)


def visible_length(text: str) -> int:
    """Get the visible length of text (excluding ANSI codes)."""
    return len(strip_ansi(text))


def truncate(text: str, width: int, suffix: str = "...", preserve_ansi: bool = True) -> str:
    """
    Truncate text to fit within width, properly handling ANSI codes.

    Args:
        text: The text to truncate
        width: Maximum visible width
        suffix: String to append if truncated
        preserve_ansi: Whether to preserve ANSI formatting

    Returns:
        Truncated string with proper ANSI handling
    """
    return ANSIString(text).truncate(width, suffix, preserve_ansi)


def wrap_text(text: str, width: int) -> List[str]:
    """
    Wrap text to specified width, preserving ANSI codes.

    Args:
        text: The text to wrap
        width: Maximum width per line

    Returns:
        List of wrapped lines
    """
    return ANSIString(text).wrap(width)


def center_text(text: str, width: int, fillchar: str = " ") -> str:
    """Center text, preserving ANSI codes."""
    return ANSIString(text).center(width, fillchar)


def ljust_text(text: str, width: int, fillchar: str = " ") -> str:
    """Left-justify text, preserving ANSI codes."""
    return ANSIString(text).ljust(width, fillchar)


def rjust_text(text: str, width: int, fillchar: str = " ") -> str:
    """Right-justify text, preserving ANSI codes."""
    return ANSIString(text).rjust(width, fillchar)
