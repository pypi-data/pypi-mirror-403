"""
Core module for ChromaForge.

Provides the main Forge class and color handling utilities.
"""

from typing import Union, Optional, Tuple, List
from dataclasses import dataclass
import re


# ANSI escape codes
ESC = "\033["
RESET_CODE = f"{ESC}0m"


@dataclass
class RGB:
    """RGB color representation."""
    r: int
    g: int
    b: int

    def __post_init__(self):
        self.r = max(0, min(255, self.r))
        self.g = max(0, min(255, self.g))
        self.b = max(0, min(255, self.b))

    def to_ansi_fg(self) -> str:
        """Convert to ANSI foreground color code."""
        return f"{ESC}38;2;{self.r};{self.g};{self.b}m"

    def to_ansi_bg(self) -> str:
        """Convert to ANSI background color code."""
        return f"{ESC}48;2;{self.r};{self.g};{self.b}m"

    def to_hex(self) -> str:
        """Convert to hex color string."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_hsl(self) -> "HSL":
        """Convert to HSL color."""
        r, g, b = self.r / 255, self.g / 255, self.b / 255
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2

        if max_c == min_c:
            h = s = 0
        else:
            d = max_c - min_c
            s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
            if max_c == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_c == g:
                h = (b - r) / d + 2
            else:
                h = (r - g) / d + 4
            h /= 6

        return HSL(int(h * 360), int(s * 100), int(l * 100))

    def blend(self, other: "RGB", factor: float = 0.5) -> "RGB":
        """Blend with another color."""
        factor = max(0, min(1, factor))
        return RGB(
            int(self.r + (other.r - self.r) * factor),
            int(self.g + (other.g - self.g) * factor),
            int(self.b + (other.b - self.b) * factor)
        )

    def lighten(self, amount: float = 0.2) -> "RGB":
        """Lighten the color."""
        return self.blend(RGB(255, 255, 255), amount)

    def darken(self, amount: float = 0.2) -> "RGB":
        """Darken the color."""
        return self.blend(RGB(0, 0, 0), amount)

    def __iter__(self):
        return iter((self.r, self.g, self.b))


@dataclass
class HSL:
    """HSL color representation."""
    h: int  # 0-360
    s: int  # 0-100
    l: int  # 0-100

    def __post_init__(self):
        self.h = self.h % 360
        self.s = max(0, min(100, self.s))
        self.l = max(0, min(100, self.l))

    def to_rgb(self) -> RGB:
        """Convert to RGB color."""
        h, s, l = self.h / 360, self.s / 100, self.l / 100

        if s == 0:
            r = g = b = l
        else:
            def hue_to_rgb(p, q, t):
                if t < 0: t += 1
                if t > 1: t -= 1
                if t < 1/6: return p + (q - p) * 6 * t
                if t < 1/2: return q
                if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                return p

            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)

        return RGB(int(r * 255), int(g * 255), int(b * 255))

    def to_ansi_fg(self) -> str:
        """Convert to ANSI foreground color code."""
        return self.to_rgb().to_ansi_fg()

    def to_ansi_bg(self) -> str:
        """Convert to ANSI background color code."""
        return self.to_rgb().to_ansi_bg()


class HEX:
    """Hex color representation."""

    def __init__(self, hex_string: str):
        self.hex_string = hex_string.lstrip("#")
        if len(self.hex_string) == 3:
            self.hex_string = "".join(c * 2 for c in self.hex_string)

    def to_rgb(self) -> RGB:
        """Convert to RGB color."""
        h = self.hex_string
        return RGB(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def to_ansi_fg(self) -> str:
        """Convert to ANSI foreground color code."""
        return self.to_rgb().to_ansi_fg()

    def to_ansi_bg(self) -> str:
        """Convert to ANSI background color code."""
        return self.to_rgb().to_ansi_bg()


# Type alias for any color type
Color = Union[RGB, HSL, HEX, str, Tuple[int, int, int]]


def parse_color(color: Color) -> RGB:
    """Parse any color format to RGB."""
    if isinstance(color, RGB):
        return color
    elif isinstance(color, HSL):
        return color.to_rgb()
    elif isinstance(color, HEX):
        return color.to_rgb()
    elif isinstance(color, tuple) and len(color) == 3:
        return RGB(*color)
    elif isinstance(color, str):
        if color.startswith("#"):
            return HEX(color).to_rgb()
        # Named colors
        named_colors = {
            "black": RGB(0, 0, 0),
            "red": RGB(255, 0, 0),
            "green": RGB(0, 255, 0),
            "yellow": RGB(255, 255, 0),
            "blue": RGB(0, 0, 255),
            "magenta": RGB(255, 0, 255),
            "cyan": RGB(0, 255, 255),
            "white": RGB(255, 255, 255),
            "orange": RGB(255, 165, 0),
            "pink": RGB(255, 192, 203),
            "purple": RGB(128, 0, 128),
            "gray": RGB(128, 128, 128),
            "grey": RGB(128, 128, 128),
            "lime": RGB(0, 255, 0),
            "navy": RGB(0, 0, 128),
            "teal": RGB(0, 128, 128),
            "maroon": RGB(128, 0, 0),
            "olive": RGB(128, 128, 0),
            "silver": RGB(192, 192, 192),
            "aqua": RGB(0, 255, 255),
            "fuchsia": RGB(255, 0, 255),
            "coral": RGB(255, 127, 80),
            "salmon": RGB(250, 128, 114),
            "gold": RGB(255, 215, 0),
            "indigo": RGB(75, 0, 130),
            "violet": RGB(238, 130, 238),
            "turquoise": RGB(64, 224, 208),
            "crimson": RGB(220, 20, 60),
            "chocolate": RGB(210, 105, 30),
        }
        return named_colors.get(color.lower(), RGB(255, 255, 255))
    else:
        raise ValueError(f"Invalid color format: {color}")


class Forge:
    """
    Main class for creating styled terminal text.

    Supports method chaining for easy composition of styles.

    Example:
        text = Forge("Hello").red().bold().underline()
        print(text)
    """

    # Basic ANSI color codes
    COLORS = {
        "black": 30, "red": 31, "green": 32, "yellow": 33,
        "blue": 34, "magenta": 35, "cyan": 36, "white": 37,
    }

    BRIGHT_COLORS = {
        "bright_black": 90, "bright_red": 91, "bright_green": 92,
        "bright_yellow": 93, "bright_blue": 94, "bright_magenta": 95,
        "bright_cyan": 96, "bright_white": 97,
    }

    BG_COLORS = {
        "on_black": 40, "on_red": 41, "on_green": 42, "on_yellow": 43,
        "on_blue": 44, "on_magenta": 45, "on_cyan": 46, "on_white": 47,
    }

    BRIGHT_BG_COLORS = {
        "on_bright_black": 100, "on_bright_red": 101, "on_bright_green": 102,
        "on_bright_yellow": 103, "on_bright_blue": 104, "on_bright_magenta": 105,
        "on_bright_cyan": 106, "on_bright_white": 107,
    }

    STYLES = {
        "bold": 1, "dim": 2, "italic": 3, "underline": 4,
        "blink": 5, "rapid_blink": 6, "reverse": 7, "hidden": 8,
        "strikethrough": 9, "double_underline": 21,
    }

    def __init__(self, text: str = ""):
        self._text = str(text)
        self._codes: List[str] = []
        self._prefix = ""
        self._suffix = ""

    def __str__(self) -> str:
        if not self._codes:
            return f"{self._prefix}{self._text}{self._suffix}"
        codes = ";".join(self._codes)
        return f"{self._prefix}{ESC}{codes}m{self._text}{RESET_CODE}{self._suffix}"

    def __repr__(self) -> str:
        return f"Forge({self._text!r})"

    def __add__(self, other: Union["Forge", str]) -> "Forge":
        if isinstance(other, Forge):
            new_forge = Forge(str(self) + str(other))
        else:
            new_forge = Forge(str(self) + str(other))
        return new_forge

    def __radd__(self, other: str) -> str:
        return str(other) + str(self)

    def _add_code(self, code: Union[int, str]) -> "Forge":
        """Add an ANSI code and return self for chaining."""
        new = Forge(self._text)
        new._codes = self._codes.copy()
        new._codes.append(str(code))
        new._prefix = self._prefix
        new._suffix = self._suffix
        return new

    def _add_raw(self, raw: str) -> "Forge":
        """Add raw ANSI sequence."""
        new = Forge(self._text)
        new._codes = self._codes.copy()
        new._prefix = self._prefix + raw
        new._suffix = self._suffix
        return new

    # Basic colors
    def black(self) -> "Forge": return self._add_code(self.COLORS["black"])
    def red(self) -> "Forge": return self._add_code(self.COLORS["red"])
    def green(self) -> "Forge": return self._add_code(self.COLORS["green"])
    def yellow(self) -> "Forge": return self._add_code(self.COLORS["yellow"])
    def blue(self) -> "Forge": return self._add_code(self.COLORS["blue"])
    def magenta(self) -> "Forge": return self._add_code(self.COLORS["magenta"])
    def cyan(self) -> "Forge": return self._add_code(self.COLORS["cyan"])
    def white(self) -> "Forge": return self._add_code(self.COLORS["white"])

    # Bright colors
    def bright_black(self) -> "Forge": return self._add_code(self.BRIGHT_COLORS["bright_black"])
    def bright_red(self) -> "Forge": return self._add_code(self.BRIGHT_COLORS["bright_red"])
    def bright_green(self) -> "Forge": return self._add_code(self.BRIGHT_COLORS["bright_green"])
    def bright_yellow(self) -> "Forge": return self._add_code(self.BRIGHT_COLORS["bright_yellow"])
    def bright_blue(self) -> "Forge": return self._add_code(self.BRIGHT_COLORS["bright_blue"])
    def bright_magenta(self) -> "Forge": return self._add_code(self.BRIGHT_COLORS["bright_magenta"])
    def bright_cyan(self) -> "Forge": return self._add_code(self.BRIGHT_COLORS["bright_cyan"])
    def bright_white(self) -> "Forge": return self._add_code(self.BRIGHT_COLORS["bright_white"])

    # Background colors
    def on_black(self) -> "Forge": return self._add_code(self.BG_COLORS["on_black"])
    def on_red(self) -> "Forge": return self._add_code(self.BG_COLORS["on_red"])
    def on_green(self) -> "Forge": return self._add_code(self.BG_COLORS["on_green"])
    def on_yellow(self) -> "Forge": return self._add_code(self.BG_COLORS["on_yellow"])
    def on_blue(self) -> "Forge": return self._add_code(self.BG_COLORS["on_blue"])
    def on_magenta(self) -> "Forge": return self._add_code(self.BG_COLORS["on_magenta"])
    def on_cyan(self) -> "Forge": return self._add_code(self.BG_COLORS["on_cyan"])
    def on_white(self) -> "Forge": return self._add_code(self.BG_COLORS["on_white"])

    # Bright background colors
    def on_bright_black(self) -> "Forge": return self._add_code(self.BRIGHT_BG_COLORS["on_bright_black"])
    def on_bright_red(self) -> "Forge": return self._add_code(self.BRIGHT_BG_COLORS["on_bright_red"])
    def on_bright_green(self) -> "Forge": return self._add_code(self.BRIGHT_BG_COLORS["on_bright_green"])
    def on_bright_yellow(self) -> "Forge": return self._add_code(self.BRIGHT_BG_COLORS["on_bright_yellow"])
    def on_bright_blue(self) -> "Forge": return self._add_code(self.BRIGHT_BG_COLORS["on_bright_blue"])
    def on_bright_magenta(self) -> "Forge": return self._add_code(self.BRIGHT_BG_COLORS["on_bright_magenta"])
    def on_bright_cyan(self) -> "Forge": return self._add_code(self.BRIGHT_BG_COLORS["on_bright_cyan"])
    def on_bright_white(self) -> "Forge": return self._add_code(self.BRIGHT_BG_COLORS["on_bright_white"])

    # Styles
    def bold(self) -> "Forge": return self._add_code(self.STYLES["bold"])
    def dim(self) -> "Forge": return self._add_code(self.STYLES["dim"])
    def italic(self) -> "Forge": return self._add_code(self.STYLES["italic"])
    def underline(self) -> "Forge": return self._add_code(self.STYLES["underline"])
    def blink(self) -> "Forge": return self._add_code(self.STYLES["blink"])
    def rapid_blink(self) -> "Forge": return self._add_code(self.STYLES["rapid_blink"])
    def reverse(self) -> "Forge": return self._add_code(self.STYLES["reverse"])
    def hidden(self) -> "Forge": return self._add_code(self.STYLES["hidden"])
    def strikethrough(self) -> "Forge": return self._add_code(self.STYLES["strikethrough"])
    def double_underline(self) -> "Forge": return self._add_code(self.STYLES["double_underline"])

    # RGB colors (true color)
    def rgb(self, r: int, g: int, b: int) -> "Forge":
        """Set foreground color using RGB values (0-255)."""
        return self._add_raw(f"{ESC}38;2;{r};{g};{b}m")

    def on_rgb(self, r: int, g: int, b: int) -> "Forge":
        """Set background color using RGB values (0-255)."""
        return self._add_raw(f"{ESC}48;2;{r};{g};{b}m")

    def color(self, color: Color) -> "Forge":
        """Set foreground color using any color format."""
        rgb = parse_color(color)
        return self.rgb(rgb.r, rgb.g, rgb.b)

    def on_color(self, color: Color) -> "Forge":
        """Set background color using any color format."""
        rgb = parse_color(color)
        return self.on_rgb(rgb.r, rgb.g, rgb.b)

    def hex(self, hex_color: str) -> "Forge":
        """Set foreground color using hex string."""
        rgb = HEX(hex_color).to_rgb()
        return self.rgb(rgb.r, rgb.g, rgb.b)

    def on_hex(self, hex_color: str) -> "Forge":
        """Set background color using hex string."""
        rgb = HEX(hex_color).to_rgb()
        return self.on_rgb(rgb.r, rgb.g, rgb.b)

    def hsl(self, h: int, s: int, l: int) -> "Forge":
        """Set foreground color using HSL values."""
        rgb = HSL(h, s, l).to_rgb()
        return self.rgb(rgb.r, rgb.g, rgb.b)

    def on_hsl(self, h: int, s: int, l: int) -> "Forge":
        """Set background color using HSL values."""
        rgb = HSL(h, s, l).to_rgb()
        return self.on_rgb(rgb.r, rgb.g, rgb.b)

    # 256 color mode
    def color256(self, code: int) -> "Forge":
        """Set foreground color using 256-color code."""
        return self._add_raw(f"{ESC}38;5;{code}m")

    def on_color256(self, code: int) -> "Forge":
        """Set background color using 256-color code."""
        return self._add_raw(f"{ESC}48;5;{code}m")

    # Gradient
    def gradient(self, start: Color, end: Color) -> "Forge":
        """Apply a gradient from start to end color across the text."""
        from .gradient import Gradient
        return Gradient(start, end).apply(self._text)

    def rainbow(self) -> "Forge":
        """Apply rainbow gradient to text."""
        from .gradient import rainbow as rainbow_gradient
        return rainbow_gradient(self._text)

    # Utility methods
    def strip(self) -> str:
        """Return the text without any ANSI codes."""
        return self._text

    def len(self) -> int:
        """Return the length of the text without ANSI codes."""
        return len(self._text)

    def center(self, width: int, fillchar: str = " ") -> "Forge":
        """Center the text within the given width."""
        new = Forge(self._text.center(width, fillchar))
        new._codes = self._codes.copy()
        new._prefix = self._prefix
        new._suffix = self._suffix
        return new

    def ljust(self, width: int, fillchar: str = " ") -> "Forge":
        """Left-justify the text within the given width."""
        new = Forge(self._text.ljust(width, fillchar))
        new._codes = self._codes.copy()
        new._prefix = self._prefix
        new._suffix = self._suffix
        return new

    def rjust(self, width: int, fillchar: str = " ") -> "Forge":
        """Right-justify the text within the given width."""
        new = Forge(self._text.rjust(width, fillchar))
        new._codes = self._codes.copy()
        new._prefix = self._prefix
        new._suffix = self._suffix
        return new


def forge(text: str = "") -> Forge:
    """
    Create a new Forge instance for styling text.

    This is the main entry point for ChromaForge.

    Args:
        text: The text to style

    Returns:
        A Forge instance for method chaining

    Example:
        print(forge("Hello").red().bold())
        print(forge("World").rgb(100, 200, 50).underline())
    """
    return Forge(text)
