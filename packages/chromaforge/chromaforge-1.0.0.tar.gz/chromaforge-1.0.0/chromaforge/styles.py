"""
Styles module for ChromaForge.

Provides style constants and the StyleBuilder class for creating reusable styles.
"""

from typing import Optional, List, Callable
from dataclasses import dataclass, field


ESC = "\033["

# Style constants
RESET = f"{ESC}0m"
BOLD = f"{ESC}1m"
DIM = f"{ESC}2m"
ITALIC = f"{ESC}3m"
UNDERLINE = f"{ESC}4m"
BLINK = f"{ESC}5m"
RAPID_BLINK = f"{ESC}6m"
REVERSE = f"{ESC}7m"
HIDDEN = f"{ESC}8m"
STRIKETHROUGH = f"{ESC}9m"
DOUBLE_UNDERLINE = f"{ESC}21m"

# Reset specific styles
RESET_BOLD = f"{ESC}22m"
RESET_DIM = f"{ESC}22m"
RESET_ITALIC = f"{ESC}23m"
RESET_UNDERLINE = f"{ESC}24m"
RESET_BLINK = f"{ESC}25m"
RESET_REVERSE = f"{ESC}27m"
RESET_HIDDEN = f"{ESC}28m"
RESET_STRIKETHROUGH = f"{ESC}29m"


@dataclass
class Style:
    """
    A reusable style definition.

    Example:
        error_style = Style(fg="red", bold=True)
        warning_style = Style(fg="yellow", italic=True)

        print(error_style("Error: Something went wrong!"))
        print(warning_style("Warning: Check your input"))
    """

    fg: Optional[str] = None
    bg: Optional[str] = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False
    blink: bool = False
    reverse: bool = False
    hidden: bool = False
    strikethrough: bool = False
    double_underline: bool = False

    _fg_rgb: Optional[tuple] = field(default=None, repr=False)
    _bg_rgb: Optional[tuple] = field(default=None, repr=False)

    def __post_init__(self):
        # Parse color strings
        if self.fg and self.fg.startswith("#"):
            hex_str = self.fg.lstrip("#")
            if len(hex_str) == 3:
                hex_str = "".join(c * 2 for c in hex_str)
            self._fg_rgb = (
                int(hex_str[0:2], 16),
                int(hex_str[2:4], 16),
                int(hex_str[4:6], 16)
            )
        if self.bg and self.bg.startswith("#"):
            hex_str = self.bg.lstrip("#")
            if len(hex_str) == 3:
                hex_str = "".join(c * 2 for c in hex_str)
            self._bg_rgb = (
                int(hex_str[0:2], 16),
                int(hex_str[2:4], 16),
                int(hex_str[4:6], 16)
            )

    def __call__(self, text: str) -> str:
        """Apply this style to text."""
        return self.apply(text)

    def apply(self, text: str) -> str:
        """Apply this style to text."""
        codes = []

        # Foreground color
        if self._fg_rgb:
            r, g, b = self._fg_rgb
            codes.append(f"38;2;{r};{g};{b}")
        elif self.fg:
            color_codes = {
                "black": 30, "red": 31, "green": 32, "yellow": 33,
                "blue": 34, "magenta": 35, "cyan": 36, "white": 37,
                "bright_black": 90, "bright_red": 91, "bright_green": 92,
                "bright_yellow": 93, "bright_blue": 94, "bright_magenta": 95,
                "bright_cyan": 96, "bright_white": 97,
            }
            if self.fg in color_codes:
                codes.append(str(color_codes[self.fg]))

        # Background color
        if self._bg_rgb:
            r, g, b = self._bg_rgb
            codes.append(f"48;2;{r};{g};{b}")
        elif self.bg:
            bg_codes = {
                "black": 40, "red": 41, "green": 42, "yellow": 43,
                "blue": 44, "magenta": 45, "cyan": 46, "white": 47,
                "bright_black": 100, "bright_red": 101, "bright_green": 102,
                "bright_yellow": 103, "bright_blue": 104, "bright_magenta": 105,
                "bright_cyan": 106, "bright_white": 107,
            }
            if self.bg in bg_codes:
                codes.append(str(bg_codes[self.bg]))

        # Styles
        if self.bold: codes.append("1")
        if self.dim: codes.append("2")
        if self.italic: codes.append("3")
        if self.underline: codes.append("4")
        if self.blink: codes.append("5")
        if self.reverse: codes.append("7")
        if self.hidden: codes.append("8")
        if self.strikethrough: codes.append("9")
        if self.double_underline: codes.append("21")

        if not codes:
            return text

        return f"{ESC}{';'.join(codes)}m{text}{RESET}"

    def combine(self, other: "Style") -> "Style":
        """Combine this style with another, with other taking precedence."""
        return Style(
            fg=other.fg or self.fg,
            bg=other.bg or self.bg,
            bold=other.bold or self.bold,
            dim=other.dim or self.dim,
            italic=other.italic or self.italic,
            underline=other.underline or self.underline,
            blink=other.blink or self.blink,
            reverse=other.reverse or self.reverse,
            hidden=other.hidden or self.hidden,
            strikethrough=other.strikethrough or self.strikethrough,
            double_underline=other.double_underline or self.double_underline,
        )


class StyleBuilder:
    """
    Fluent builder for creating Style objects.

    Example:
        style = (StyleBuilder()
            .foreground("red")
            .background("white")
            .bold()
            .underline()
            .build())
    """

    def __init__(self):
        self._fg: Optional[str] = None
        self._bg: Optional[str] = None
        self._bold: bool = False
        self._dim: bool = False
        self._italic: bool = False
        self._underline: bool = False
        self._blink: bool = False
        self._reverse: bool = False
        self._hidden: bool = False
        self._strikethrough: bool = False
        self._double_underline: bool = False

    def foreground(self, color: str) -> "StyleBuilder":
        """Set the foreground color."""
        self._fg = color
        return self

    def fg(self, color: str) -> "StyleBuilder":
        """Alias for foreground()."""
        return self.foreground(color)

    def background(self, color: str) -> "StyleBuilder":
        """Set the background color."""
        self._bg = color
        return self

    def bg(self, color: str) -> "StyleBuilder":
        """Alias for background()."""
        return self.background(color)

    def rgb(self, r: int, g: int, b: int) -> "StyleBuilder":
        """Set foreground color using RGB."""
        self._fg = f"#{r:02x}{g:02x}{b:02x}"
        return self

    def on_rgb(self, r: int, g: int, b: int) -> "StyleBuilder":
        """Set background color using RGB."""
        self._bg = f"#{r:02x}{g:02x}{b:02x}"
        return self

    def hex(self, color: str) -> "StyleBuilder":
        """Set foreground color using hex."""
        self._fg = color if color.startswith("#") else f"#{color}"
        return self

    def on_hex(self, color: str) -> "StyleBuilder":
        """Set background color using hex."""
        self._bg = color if color.startswith("#") else f"#{color}"
        return self

    def bold(self, enabled: bool = True) -> "StyleBuilder":
        """Enable bold style."""
        self._bold = enabled
        return self

    def dim(self, enabled: bool = True) -> "StyleBuilder":
        """Enable dim style."""
        self._dim = enabled
        return self

    def italic(self, enabled: bool = True) -> "StyleBuilder":
        """Enable italic style."""
        self._italic = enabled
        return self

    def underline(self, enabled: bool = True) -> "StyleBuilder":
        """Enable underline style."""
        self._underline = enabled
        return self

    def blink(self, enabled: bool = True) -> "StyleBuilder":
        """Enable blink style."""
        self._blink = enabled
        return self

    def reverse(self, enabled: bool = True) -> "StyleBuilder":
        """Enable reverse style."""
        self._reverse = enabled
        return self

    def hidden(self, enabled: bool = True) -> "StyleBuilder":
        """Enable hidden style."""
        self._hidden = enabled
        return self

    def strikethrough(self, enabled: bool = True) -> "StyleBuilder":
        """Enable strikethrough style."""
        self._strikethrough = enabled
        return self

    def double_underline(self, enabled: bool = True) -> "StyleBuilder":
        """Enable double underline style."""
        self._double_underline = enabled
        return self

    def build(self) -> Style:
        """Build and return the Style object."""
        return Style(
            fg=self._fg,
            bg=self._bg,
            bold=self._bold,
            dim=self._dim,
            italic=self._italic,
            underline=self._underline,
            blink=self._blink,
            reverse=self._reverse,
            hidden=self._hidden,
            strikethrough=self._strikethrough,
            double_underline=self._double_underline,
        )


# Pre-defined styles
STYLES = {
    "error": Style(fg="red", bold=True),
    "warning": Style(fg="yellow", bold=True),
    "success": Style(fg="green", bold=True),
    "info": Style(fg="cyan"),
    "debug": Style(fg="bright_black"),
    "highlight": Style(fg="black", bg="yellow"),
    "link": Style(fg="blue", underline=True),
    "code": Style(fg="bright_green", bg="bright_black"),
    "header": Style(fg="white", bold=True, underline=True),
    "muted": Style(fg="bright_black", dim=True),
}


def get_style(name: str) -> Style:
    """Get a pre-defined style by name."""
    return STYLES.get(name, Style())


def register_style(name: str, style: Style) -> None:
    """Register a custom style."""
    STYLES[name] = style
