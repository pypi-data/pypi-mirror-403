"""
Colors module for ChromaForge.

Provides color utility functions and pre-defined color shortcuts.
"""

from typing import Union
from .core import Forge, RGB, HSL, HEX, parse_color, Color


# Basic color functions
def black(text: str) -> Forge:
    """Apply black color to text."""
    return Forge(text).black()


def red(text: str) -> Forge:
    """Apply red color to text."""
    return Forge(text).red()


def green(text: str) -> Forge:
    """Apply green color to text."""
    return Forge(text).green()


def yellow(text: str) -> Forge:
    """Apply yellow color to text."""
    return Forge(text).yellow()


def blue(text: str) -> Forge:
    """Apply blue color to text."""
    return Forge(text).blue()


def magenta(text: str) -> Forge:
    """Apply magenta color to text."""
    return Forge(text).magenta()


def cyan(text: str) -> Forge:
    """Apply cyan color to text."""
    return Forge(text).cyan()


def white(text: str) -> Forge:
    """Apply white color to text."""
    return Forge(text).white()


# Bright color functions
def bright_black(text: str) -> Forge:
    """Apply bright black (gray) color to text."""
    return Forge(text).bright_black()


def bright_red(text: str) -> Forge:
    """Apply bright red color to text."""
    return Forge(text).bright_red()


def bright_green(text: str) -> Forge:
    """Apply bright green color to text."""
    return Forge(text).bright_green()


def bright_yellow(text: str) -> Forge:
    """Apply bright yellow color to text."""
    return Forge(text).bright_yellow()


def bright_blue(text: str) -> Forge:
    """Apply bright blue color to text."""
    return Forge(text).bright_blue()


def bright_magenta(text: str) -> Forge:
    """Apply bright magenta color to text."""
    return Forge(text).bright_magenta()


def bright_cyan(text: str) -> Forge:
    """Apply bright cyan color to text."""
    return Forge(text).bright_cyan()


def bright_white(text: str) -> Forge:
    """Apply bright white color to text."""
    return Forge(text).bright_white()


# RGB/HSL/Hex functions
def rgb(text: str, r: int, g: int, b: int) -> Forge:
    """Apply RGB color to text."""
    return Forge(text).rgb(r, g, b)


def hsl(text: str, h: int, s: int, l: int) -> Forge:
    """Apply HSL color to text."""
    return Forge(text).hsl(h, s, l)


def hex_color(text: str, hex_code: str) -> Forge:
    """Apply hex color to text."""
    return Forge(text).hex(hex_code)


# Color palette - Extended named colors
PALETTE = {
    # Reds
    "crimson": RGB(220, 20, 60),
    "darkred": RGB(139, 0, 0),
    "firebrick": RGB(178, 34, 34),
    "indianred": RGB(205, 92, 92),
    "lightcoral": RGB(240, 128, 128),
    "salmon": RGB(250, 128, 114),
    "darksalmon": RGB(233, 150, 122),
    "lightsalmon": RGB(255, 160, 122),

    # Oranges
    "coral": RGB(255, 127, 80),
    "tomato": RGB(255, 99, 71),
    "orangered": RGB(255, 69, 0),
    "darkorange": RGB(255, 140, 0),
    "orange": RGB(255, 165, 0),

    # Yellows
    "gold": RGB(255, 215, 0),
    "lightyellow": RGB(255, 255, 224),
    "lemonchiffon": RGB(255, 250, 205),
    "papayawhip": RGB(255, 239, 213),
    "moccasin": RGB(255, 228, 181),
    "peachpuff": RGB(255, 218, 185),
    "palegoldenrod": RGB(238, 232, 170),
    "khaki": RGB(240, 230, 140),
    "darkkhaki": RGB(189, 183, 107),

    # Greens
    "lawngreen": RGB(124, 252, 0),
    "chartreuse": RGB(127, 255, 0),
    "limegreen": RGB(50, 205, 50),
    "lime": RGB(0, 255, 0),
    "forestgreen": RGB(34, 139, 34),
    "darkgreen": RGB(0, 100, 0),
    "seagreen": RGB(46, 139, 87),
    "mediumseagreen": RGB(60, 179, 113),
    "springgreen": RGB(0, 255, 127),
    "mediumspringgreen": RGB(0, 250, 154),
    "mediumaquamarine": RGB(102, 205, 170),
    "aquamarine": RGB(127, 255, 212),
    "palegreen": RGB(152, 251, 152),
    "lightgreen": RGB(144, 238, 144),
    "darkseagreen": RGB(143, 188, 143),
    "olivedrab": RGB(107, 142, 35),
    "olive": RGB(128, 128, 0),
    "darkolivegreen": RGB(85, 107, 47),

    # Cyans
    "teal": RGB(0, 128, 128),
    "darkcyan": RGB(0, 139, 139),
    "aqua": RGB(0, 255, 255),
    "lightcyan": RGB(224, 255, 255),
    "darkturquoise": RGB(0, 206, 209),
    "turquoise": RGB(64, 224, 208),
    "mediumturquoise": RGB(72, 209, 204),
    "paleturquoise": RGB(175, 238, 238),
    "cadetblue": RGB(95, 158, 160),

    # Blues
    "steelblue": RGB(70, 130, 180),
    "lightsteelblue": RGB(176, 196, 222),
    "powderblue": RGB(176, 224, 230),
    "lightblue": RGB(173, 216, 230),
    "skyblue": RGB(135, 206, 235),
    "lightskyblue": RGB(135, 206, 250),
    "deepskyblue": RGB(0, 191, 255),
    "dodgerblue": RGB(30, 144, 255),
    "cornflowerblue": RGB(100, 149, 237),
    "royalblue": RGB(65, 105, 225),
    "mediumblue": RGB(0, 0, 205),
    "darkblue": RGB(0, 0, 139),
    "navy": RGB(0, 0, 128),
    "midnightblue": RGB(25, 25, 112),

    # Purples
    "lavender": RGB(230, 230, 250),
    "thistle": RGB(216, 191, 216),
    "plum": RGB(221, 160, 221),
    "violet": RGB(238, 130, 238),
    "orchid": RGB(218, 112, 214),
    "fuchsia": RGB(255, 0, 255),
    "mediumorchid": RGB(186, 85, 211),
    "mediumpurple": RGB(147, 112, 219),
    "blueviolet": RGB(138, 43, 226),
    "darkviolet": RGB(148, 0, 211),
    "darkorchid": RGB(153, 50, 204),
    "darkmagenta": RGB(139, 0, 139),
    "purple": RGB(128, 0, 128),
    "indigo": RGB(75, 0, 130),
    "slateblue": RGB(106, 90, 205),
    "darkslateblue": RGB(72, 61, 139),

    # Pinks
    "pink": RGB(255, 192, 203),
    "lightpink": RGB(255, 182, 193),
    "hotpink": RGB(255, 105, 180),
    "deeppink": RGB(255, 20, 147),
    "mediumvioletred": RGB(199, 21, 133),
    "palevioletred": RGB(219, 112, 147),

    # Browns
    "chocolate": RGB(210, 105, 30),
    "saddlebrown": RGB(139, 69, 19),
    "sienna": RGB(160, 82, 45),
    "brown": RGB(165, 42, 42),
    "maroon": RGB(128, 0, 0),
    "peru": RGB(205, 133, 63),
    "rosybrown": RGB(188, 143, 143),
    "sandybrown": RGB(244, 164, 96),
    "tan": RGB(210, 180, 140),
    "burlywood": RGB(222, 184, 135),
    "wheat": RGB(245, 222, 179),
    "navajowhite": RGB(255, 222, 173),
    "bisque": RGB(255, 228, 196),
    "blanchedalmond": RGB(255, 235, 205),
    "cornsilk": RGB(255, 248, 220),

    # Whites
    "snow": RGB(255, 250, 250),
    "honeydew": RGB(240, 255, 240),
    "mintcream": RGB(245, 255, 250),
    "azure": RGB(240, 255, 255),
    "aliceblue": RGB(240, 248, 255),
    "ghostwhite": RGB(248, 248, 255),
    "whitesmoke": RGB(245, 245, 245),
    "seashell": RGB(255, 245, 238),
    "beige": RGB(245, 245, 220),
    "oldlace": RGB(253, 245, 230),
    "floralwhite": RGB(255, 250, 240),
    "ivory": RGB(255, 255, 240),
    "antiquewhite": RGB(250, 235, 215),
    "linen": RGB(250, 240, 230),
    "lavenderblush": RGB(255, 240, 245),
    "mistyrose": RGB(255, 228, 225),

    # Grays
    "gainsboro": RGB(220, 220, 220),
    "lightgray": RGB(211, 211, 211),
    "silver": RGB(192, 192, 192),
    "darkgray": RGB(169, 169, 169),
    "gray": RGB(128, 128, 128),
    "dimgray": RGB(105, 105, 105),
    "lightslategray": RGB(119, 136, 153),
    "slategray": RGB(112, 128, 144),
    "darkslategray": RGB(47, 79, 79),
}


def get_color(name: str) -> RGB:
    """Get a named color from the palette."""
    return PALETTE.get(name.lower(), RGB(255, 255, 255))


def from_name(text: str, color_name: str) -> Forge:
    """Apply a named color from the palette to text."""
    color = get_color(color_name)
    return Forge(text).rgb(color.r, color.g, color.b)


def blend(color1: Color, color2: Color, factor: float = 0.5) -> RGB:
    """Blend two colors together."""
    rgb1 = parse_color(color1)
    rgb2 = parse_color(color2)
    return rgb1.blend(rgb2, factor)


def lighten(color: Color, amount: float = 0.2) -> RGB:
    """Lighten a color."""
    return parse_color(color).lighten(amount)


def darken(color: Color, amount: float = 0.2) -> RGB:
    """Darken a color."""
    return parse_color(color).darken(amount)


def complement(color: Color) -> RGB:
    """Get the complementary color."""
    rgb = parse_color(color)
    return RGB(255 - rgb.r, 255 - rgb.g, 255 - rgb.b)


def grayscale(color: Color) -> RGB:
    """Convert a color to grayscale."""
    rgb = parse_color(color)
    gray = int(0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b)
    return RGB(gray, gray, gray)
