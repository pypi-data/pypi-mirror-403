"""
Components module for ChromaForge.

Provides UI components like boxes, tables, progress bars, spinners, and more.
"""

import sys
import time
import threading
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from .core import Forge, RGB, ESC, RESET_CODE
from .styles import Style


# Box drawing characters
BOX_STYLES = {
    "single": {
        "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
        "h": "─", "v": "│", "lm": "├", "rm": "┤",
        "tm": "┬", "bm": "┴", "cross": "┼"
    },
    "double": {
        "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
        "h": "═", "v": "║", "lm": "╠", "rm": "╣",
        "tm": "╦", "bm": "╩", "cross": "╬"
    },
    "rounded": {
        "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
        "h": "─", "v": "│", "lm": "├", "rm": "┤",
        "tm": "┬", "bm": "┴", "cross": "┼"
    },
    "bold": {
        "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛",
        "h": "━", "v": "┃", "lm": "┣", "rm": "┫",
        "tm": "┳", "bm": "┻", "cross": "╋"
    },
    "ascii": {
        "tl": "+", "tr": "+", "bl": "+", "br": "+",
        "h": "-", "v": "|", "lm": "+", "rm": "+",
        "tm": "+", "bm": "+", "cross": "+"
    },
}


class Box:
    """
    Create a box around text.

    Example:
        box = Box("Hello World", style="rounded", color="cyan")
        print(box)

        # Multi-line
        box = Box(["Line 1", "Line 2", "Line 3"], title="My Box")
        print(box)
    """

    def __init__(
        self,
        content: Union[str, List[str]],
        title: Optional[str] = None,
        style: str = "single",
        color: Optional[str] = None,
        padding: int = 1,
        width: Optional[int] = None,
        align: str = "left"
    ):
        self.content = [content] if isinstance(content, str) else content
        self.title = title
        self.style = BOX_STYLES.get(style, BOX_STYLES["single"])
        self.color = color
        self.padding = padding
        self.align = align

        # Calculate width
        content_width = max(len(line) for line in self.content) if self.content else 0
        title_width = len(title) + 2 if title else 0
        self.width = width or max(content_width + padding * 2, title_width + 2)

    def __str__(self) -> str:
        return self.render()

    def render(self) -> str:
        s = self.style
        w = self.width
        pad = " " * self.padding

        color_start = ""
        color_end = ""
        if self.color:
            colors = {
                "black": 30, "red": 31, "green": 32, "yellow": 33,
                "blue": 34, "magenta": 35, "cyan": 36, "white": 37,
            }
            if self.color in colors:
                color_start = f"{ESC}{colors[self.color]}m"
                color_end = RESET_CODE

        lines = []

        # Top border
        if self.title:
            title_str = f" {self.title} "
            remaining = w - len(title_str)
            left_bar = s["h"] * (remaining // 2)
            right_bar = s["h"] * (remaining - remaining // 2)
            lines.append(f"{color_start}{s['tl']}{left_bar}{title_str}{right_bar}{s['tr']}{color_end}")
        else:
            lines.append(f"{color_start}{s['tl']}{s['h'] * w}{s['tr']}{color_end}")

        # Content lines
        for line in self.content:
            content_width = w - self.padding * 2
            if self.align == "center":
                formatted = line.center(content_width)
            elif self.align == "right":
                formatted = line.rjust(content_width)
            else:
                formatted = line.ljust(content_width)
            lines.append(f"{color_start}{s['v']}{color_end}{pad}{formatted}{pad}{color_start}{s['v']}{color_end}")

        # Bottom border
        lines.append(f"{color_start}{s['bl']}{s['h'] * w}{s['br']}{color_end}")

        return "\n".join(lines)


class Table:
    """
    Create a formatted table.

    Example:
        table = Table(
            headers=["Name", "Age", "City"],
            rows=[
                ["Alice", "30", "New York"],
                ["Bob", "25", "Los Angeles"],
            ],
            style="rounded"
        )
        print(table)
    """

    def __init__(
        self,
        headers: List[str],
        rows: List[List[str]],
        style: str = "single",
        color: Optional[str] = None,
        header_color: Optional[str] = None,
        padding: int = 1
    ):
        self.headers = headers
        self.rows = rows
        self.style = BOX_STYLES.get(style, BOX_STYLES["single"])
        self.color = color
        self.header_color = header_color or "white"
        self.padding = padding

        # Calculate column widths
        self.col_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            self.col_widths.append(max_width + padding * 2)

    def __str__(self) -> str:
        return self.render()

    def render(self) -> str:
        s = self.style
        pad = " " * self.padding

        color_start = ""
        color_end = ""
        if self.color:
            colors = {
                "black": 30, "red": 31, "green": 32, "yellow": 33,
                "blue": 34, "magenta": 35, "cyan": 36, "white": 37,
            }
            if self.color in colors:
                color_start = f"{ESC}{colors[self.color]}m"
                color_end = RESET_CODE

        header_style = ""
        if self.header_color:
            colors = {
                "black": 30, "red": 31, "green": 32, "yellow": 33,
                "blue": 34, "magenta": 35, "cyan": 36, "white": 37,
            }
            if self.header_color in colors:
                header_style = f"{ESC}{colors[self.header_color]};1m"

        lines = []

        # Top border
        top_parts = [s["h"] * w for w in self.col_widths]
        lines.append(f"{color_start}{s['tl']}{s['tm'].join(top_parts)}{s['tr']}{color_end}")

        # Header row
        header_cells = []
        for i, header in enumerate(self.headers):
            width = self.col_widths[i] - self.padding * 2
            header_cells.append(f"{pad}{header_style}{header.center(width)}{color_end}{RESET_CODE}{pad}")
        lines.append(f"{color_start}{s['v']}{color_end}{f'{color_start}{s["v"]}{color_end}'.join(header_cells)}{color_start}{s['v']}{color_end}")

        # Header separator
        sep_parts = [s["h"] * w for w in self.col_widths]
        lines.append(f"{color_start}{s['lm']}{s['cross'].join(sep_parts)}{s['rm']}{color_end}")

        # Data rows
        for row in self.rows:
            cells = []
            for i, cell in enumerate(row):
                if i < len(self.col_widths):
                    width = self.col_widths[i] - self.padding * 2
                    cells.append(f"{pad}{str(cell).ljust(width)}{pad}")
            lines.append(f"{color_start}{s['v']}{color_end}{f'{color_start}{s["v"]}{color_end}'.join(cells)}{color_start}{s['v']}{color_end}")

        # Bottom border
        bottom_parts = [s["h"] * w for w in self.col_widths]
        lines.append(f"{color_start}{s['bl']}{s['bm'].join(bottom_parts)}{s['br']}{color_end}")

        return "\n".join(lines)


class Progress:
    """
    Create a progress bar.

    Example:
        progress = Progress(total=100, width=40)
        for i in range(101):
            progress.update(i)
            time.sleep(0.05)
        progress.finish()
    """

    def __init__(
        self,
        total: int = 100,
        width: int = 40,
        fill_char: str = "█",
        empty_char: str = "░",
        color: Optional[RGB] = None,
        show_percent: bool = True,
        show_count: bool = False,
        prefix: str = "",
        suffix: str = ""
    ):
        self.total = total
        self.width = width
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.color = color or RGB(0, 255, 100)
        self.show_percent = show_percent
        self.show_count = show_count
        self.prefix = prefix
        self.suffix = suffix
        self.current = 0
        self._start_time = time.time()

    def update(self, value: int) -> None:
        """Update the progress bar."""
        self.current = min(value, self.total)
        self._render()

    def increment(self, amount: int = 1) -> None:
        """Increment the progress bar."""
        self.update(self.current + amount)

    def _render(self) -> None:
        """Render the progress bar."""
        percent = self.current / self.total if self.total > 0 else 0
        filled = int(self.width * percent)
        empty = self.width - filled

        # Color gradient from red to green based on progress
        r = int(255 * (1 - percent))
        g = int(255 * percent)
        b = 0

        bar = f"{ESC}38;2;{r};{g};{b}m{self.fill_char * filled}{ESC}38;5;240m{self.empty_char * empty}{RESET_CODE}"

        parts = [self.prefix, bar]

        if self.show_percent:
            parts.append(f" {percent * 100:5.1f}%")

        if self.show_count:
            parts.append(f" [{self.current}/{self.total}]")

        parts.append(self.suffix)

        sys.stdout.write(f"\r{''.join(parts)}")
        sys.stdout.flush()

    def finish(self, message: str = "") -> None:
        """Complete the progress bar."""
        self.update(self.total)
        elapsed = time.time() - self._start_time
        if message:
            sys.stdout.write(f" {message}")
        sys.stdout.write(f" ({elapsed:.1f}s)\n")
        sys.stdout.flush()


class Spinner:
    """
    Create an animated spinner.

    Example:
        spinner = Spinner("Loading")
        spinner.start()
        time.sleep(3)
        spinner.stop("Done!")
    """

    SPINNERS = {
        "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        "line": ["-", "\\", "|", "/"],
        "circle": ["◐", "◓", "◑", "◒"],
        "square": ["◰", "◳", "◲", "◱"],
        "arrow": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
        "bounce": ["⠁", "⠂", "⠄", "⠂"],
        "pulse": ["█", "▓", "▒", "░", "▒", "▓"],
        "dots2": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
        "moon": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
        "clock": ["🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"],
    }

    def __init__(
        self,
        message: str = "Loading",
        style: str = "dots",
        color: Optional[str] = None,
        speed: float = 0.1
    ):
        self.message = message
        self.frames = self.SPINNERS.get(style, self.SPINNERS["dots"])
        self.color = color
        self.speed = speed
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._frame_idx = 0

    def _animate(self) -> None:
        """Animation loop."""
        color_start = ""
        color_end = ""
        if self.color:
            colors = {
                "black": 30, "red": 31, "green": 32, "yellow": 33,
                "blue": 34, "magenta": 35, "cyan": 36, "white": 37,
            }
            if self.color in colors:
                color_start = f"{ESC}{colors[self.color]}m"
                color_end = RESET_CODE

        while self._running:
            frame = self.frames[self._frame_idx % len(self.frames)]
            sys.stdout.write(f"\r{color_start}{frame}{color_end} {self.message}")
            sys.stdout.flush()
            self._frame_idx += 1
            time.sleep(self.speed)

    def start(self) -> "Spinner":
        """Start the spinner."""
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self

    def stop(self, final_message: Optional[str] = None) -> None:
        """Stop the spinner."""
        self._running = False
        if self._thread:
            self._thread.join()
        sys.stdout.write(f"\r{' ' * (len(self.message) + 4)}\r")
        if final_message:
            sys.stdout.write(f"✓ {final_message}\n")
        sys.stdout.flush()

    def __enter__(self) -> "Spinner":
        return self.start()

    def __exit__(self, *args) -> None:
        self.stop()


class Panel:
    """
    Create a panel with a title and content.

    Example:
        panel = Panel(
            "This is some important information.",
            title="Notice",
            border_color="yellow"
        )
        print(panel)
    """

    def __init__(
        self,
        content: str,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        border_color: Optional[str] = None,
        title_color: Optional[str] = None,
        width: Optional[int] = None,
        padding: int = 1,
        style: str = "rounded"
    ):
        self.content = content
        self.title = title
        self.subtitle = subtitle
        self.border_color = border_color
        self.title_color = title_color or border_color
        self.padding = padding
        self.box_style = BOX_STYLES.get(style, BOX_STYLES["rounded"])

        # Wrap content
        self.lines = content.split("\n")
        content_width = max(len(line) for line in self.lines)
        self.width = width or content_width + padding * 2 + 2

    def __str__(self) -> str:
        return self.render()

    def render(self) -> str:
        s = self.box_style
        w = self.width - 2

        border_start = ""
        border_end = ""
        if self.border_color:
            colors = {"black": 30, "red": 31, "green": 32, "yellow": 33,
                      "blue": 34, "magenta": 35, "cyan": 36, "white": 37}
            if self.border_color in colors:
                border_start = f"{ESC}{colors[self.border_color]}m"
                border_end = RESET_CODE

        title_start = ""
        if self.title_color:
            colors = {"black": 30, "red": 31, "green": 32, "yellow": 33,
                      "blue": 34, "magenta": 35, "cyan": 36, "white": 37}
            if self.title_color in colors:
                title_start = f"{ESC}{colors[self.title_color]};1m"

        lines = []

        # Top border with title
        if self.title:
            title_str = f" {title_start}{self.title}{border_end}{border_start} "
            title_len = len(self.title) + 2
            remaining = w - title_len
            lines.append(f"{border_start}{s['tl']}{s['h']}{title_str}{s['h'] * (remaining - 1)}{s['tr']}{border_end}")
        else:
            lines.append(f"{border_start}{s['tl']}{s['h'] * w}{s['tr']}{border_end}")

        # Content
        pad = " " * self.padding
        for line in self.lines:
            content_width = w - self.padding * 2
            formatted = line.ljust(content_width)
            lines.append(f"{border_start}{s['v']}{border_end}{pad}{formatted}{pad}{border_start}{s['v']}{border_end}")

        # Bottom border with subtitle
        if self.subtitle:
            sub_str = f" {self.subtitle} "
            remaining = w - len(sub_str)
            lines.append(f"{border_start}{s['bl']}{s['h'] * (remaining - 1)}{sub_str}{s['h']}{s['br']}{border_end}")
        else:
            lines.append(f"{border_start}{s['bl']}{s['h'] * w}{s['br']}{border_end}")

        return "\n".join(lines)


class Rule:
    """
    Create a horizontal rule/divider.

    Example:
        print(Rule("Section Title"))
        print(Rule(style="double", color="cyan"))
    """

    def __init__(
        self,
        title: Optional[str] = None,
        width: Optional[int] = None,
        style: str = "single",
        color: Optional[str] = None,
        align: str = "center"
    ):
        self.title = title
        self.width = width or 80
        self.char = BOX_STYLES.get(style, BOX_STYLES["single"])["h"]
        self.color = color
        self.align = align

    def __str__(self) -> str:
        return self.render()

    def render(self) -> str:
        color_start = ""
        color_end = ""
        if self.color:
            colors = {"black": 30, "red": 31, "green": 32, "yellow": 33,
                      "blue": 34, "magenta": 35, "cyan": 36, "white": 37}
            if self.color in colors:
                color_start = f"{ESC}{colors[self.color]}m"
                color_end = RESET_CODE

        if not self.title:
            return f"{color_start}{self.char * self.width}{color_end}"

        title_str = f" {self.title} "
        remaining = self.width - len(title_str)

        if self.align == "left":
            left = 2
            right = remaining - 2
        elif self.align == "right":
            left = remaining - 2
            right = 2
        else:  # center
            left = remaining // 2
            right = remaining - left

        return f"{color_start}{self.char * left}{color_end}{title_str}{color_start}{self.char * right}{color_end}"


class Columns:
    """
    Display content in columns.

    Example:
        cols = Columns(["Item 1", "Item 2", "Item 3", "Item 4"], num_columns=2)
        print(cols)
    """

    def __init__(
        self,
        items: List[str],
        num_columns: int = 2,
        column_width: Optional[int] = None,
        padding: int = 2
    ):
        self.items = items
        self.num_columns = num_columns
        self.padding = padding
        self.column_width = column_width or (max(len(item) for item in items) + padding)

    def __str__(self) -> str:
        return self.render()

    def render(self) -> str:
        lines = []
        for i in range(0, len(self.items), self.num_columns):
            row_items = self.items[i:i + self.num_columns]
            row = ""
            for item in row_items:
                row += item.ljust(self.column_width)
            lines.append(row)
        return "\n".join(lines)
