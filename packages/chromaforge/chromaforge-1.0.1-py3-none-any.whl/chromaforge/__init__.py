"""
ChromaForge - Advanced Terminal Coloring for Python

A modern, feature-rich terminal coloring library that goes beyond
colorama and rich with support for true colors, gradients, animations,
and beautiful UI components.

Example:
    from chromaforge import forge, Style, Gradient

    # Simple colored text
    print(forge("Hello World").red().bold())

    # RGB colors
    print(forge("Custom Color").rgb(255, 100, 50))

    # Gradients
    print(forge("Rainbow Text").gradient("rainbow"))

    # Chained styles
    print(forge("Styled").blue().bold().underline().on_white())
"""

__version__ = "1.0.1"
__author__ = "PyIDE Team"
__email__ = "support@pyide.org"

from .core import (
    forge,
    Forge,
    Color,
    RGB,
    HSL,
    HEX,
)

from .styles import (
    Style,
    StyleBuilder,
    RESET,
    BOLD,
    DIM,
    ITALIC,
    UNDERLINE,
    BLINK,
    REVERSE,
    HIDDEN,
    STRIKETHROUGH,
)

from .colors import (
    # Basic colors
    black, red, green, yellow, blue, magenta, cyan, white,
    # Bright colors
    bright_black, bright_red, bright_green, bright_yellow,
    bright_blue, bright_magenta, bright_cyan, bright_white,
    # Color functions
    rgb, hsl, hex_color,
)

from .gradient import (
    Gradient,
    gradient,
    rainbow,
    fire,
    ocean,
    forest,
    sunset,
    neon,
)

from .effects import (
    typing,
    pulse,
    shimmer,
    glitch,
)

from .components import (
    Box,
    Table,
    Progress,
    Spinner,
    Panel,
    Rule,
    Columns,
)

from .themes import (
    Theme,
    set_theme,
    get_theme,
    THEMES,
)

from .terminal import (
    Terminal,
    supports_color,
    supports_truecolor,
    get_terminal_size,
    clear,
    clear_line,
    move_cursor,
    hide_cursor,
    show_cursor,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "forge",
    "Forge",
    "Color",
    "RGB",
    "HSL",
    "HEX",
    # Styles
    "Style",
    "StyleBuilder",
    "RESET",
    "BOLD",
    "DIM",
    "ITALIC",
    "UNDERLINE",
    "BLINK",
    "REVERSE",
    "HIDDEN",
    "STRIKETHROUGH",
    # Basic colors
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
    # Bright colors
    "bright_black", "bright_red", "bright_green", "bright_yellow",
    "bright_blue", "bright_magenta", "bright_cyan", "bright_white",
    # Color functions
    "rgb", "hsl", "hex_color",
    # Gradients
    "Gradient",
    "gradient",
    "rainbow",
    "fire",
    "ocean",
    "forest",
    "sunset",
    "neon",
    # Effects
    "typing",
    "pulse",
    "shimmer",
    "glitch",
    # Components
    "Box",
    "Table",
    "Progress",
    "Spinner",
    "Panel",
    "Rule",
    "Columns",
    # Themes
    "Theme",
    "set_theme",
    "get_theme",
    "THEMES",
    # Terminal
    "Terminal",
    "supports_color",
    "supports_truecolor",
    "get_terminal_size",
    "clear",
    "clear_line",
    "move_cursor",
    "hide_cursor",
    "show_cursor",
]
