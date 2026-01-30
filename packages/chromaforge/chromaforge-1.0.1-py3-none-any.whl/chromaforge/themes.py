"""
Themes module for ChromaForge.

Provides theme support for consistent styling across applications.
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from .core import RGB
from .styles import Style


@dataclass
class Theme:
    """
    A complete color theme for terminal applications.

    Example:
        theme = Theme(
            name="ocean",
            primary=RGB(0, 150, 255),
            secondary=RGB(0, 200, 200),
            success=RGB(0, 255, 100),
            warning=RGB(255, 200, 0),
            error=RGB(255, 50, 50),
            info=RGB(100, 150, 255),
        )
        set_theme(theme)
    """

    name: str
    primary: RGB = field(default_factory=lambda: RGB(100, 150, 255))
    secondary: RGB = field(default_factory=lambda: RGB(150, 100, 255))
    success: RGB = field(default_factory=lambda: RGB(0, 255, 100))
    warning: RGB = field(default_factory=lambda: RGB(255, 200, 0))
    error: RGB = field(default_factory=lambda: RGB(255, 50, 50))
    info: RGB = field(default_factory=lambda: RGB(100, 200, 255))
    muted: RGB = field(default_factory=lambda: RGB(128, 128, 128))

    # Background colors
    bg_primary: RGB = field(default_factory=lambda: RGB(20, 20, 30))
    bg_secondary: RGB = field(default_factory=lambda: RGB(30, 30, 45))
    bg_highlight: RGB = field(default_factory=lambda: RGB(50, 50, 70))

    # Text colors
    text: RGB = field(default_factory=lambda: RGB(240, 240, 240))
    text_muted: RGB = field(default_factory=lambda: RGB(150, 150, 150))
    text_highlight: RGB = field(default_factory=lambda: RGB(255, 255, 255))

    # Accent colors
    accent1: RGB = field(default_factory=lambda: RGB(255, 100, 150))
    accent2: RGB = field(default_factory=lambda: RGB(100, 255, 200))
    accent3: RGB = field(default_factory=lambda: RGB(255, 200, 100))

    def get_style(self, name: str) -> Style:
        """Get a style by semantic name."""
        color_map = {
            "primary": self.primary,
            "secondary": self.secondary,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "info": self.info,
            "muted": self.muted,
        }

        color = color_map.get(name)
        if color:
            return Style(fg=f"#{color.r:02x}{color.g:02x}{color.b:02x}")
        return Style()

    def primary_text(self, text: str) -> str:
        """Apply primary color to text."""
        return f"\033[38;2;{self.primary.r};{self.primary.g};{self.primary.b}m{text}\033[0m"

    def secondary_text(self, text: str) -> str:
        """Apply secondary color to text."""
        return f"\033[38;2;{self.secondary.r};{self.secondary.g};{self.secondary.b}m{text}\033[0m"

    def success_text(self, text: str) -> str:
        """Apply success color to text."""
        return f"\033[38;2;{self.success.r};{self.success.g};{self.success.b}m{text}\033[0m"

    def warning_text(self, text: str) -> str:
        """Apply warning color to text."""
        return f"\033[38;2;{self.warning.r};{self.warning.g};{self.warning.b}m{text}\033[0m"

    def error_text(self, text: str) -> str:
        """Apply error color to text."""
        return f"\033[38;2;{self.error.r};{self.error.g};{self.error.b}m{text}\033[0m"

    def info_text(self, text: str) -> str:
        """Apply info color to text."""
        return f"\033[38;2;{self.info.r};{self.info.g};{self.info.b}m{text}\033[0m"


# Pre-defined themes
THEMES: Dict[str, Theme] = {
    "default": Theme(name="default"),

    "monokai": Theme(
        name="monokai",
        primary=RGB(166, 226, 46),
        secondary=RGB(102, 217, 239),
        success=RGB(166, 226, 46),
        warning=RGB(253, 151, 31),
        error=RGB(249, 38, 114),
        info=RGB(102, 217, 239),
        muted=RGB(117, 113, 94),
        bg_primary=RGB(39, 40, 34),
        bg_secondary=RGB(49, 50, 44),
        text=RGB(248, 248, 242),
        accent1=RGB(249, 38, 114),
        accent2=RGB(174, 129, 255),
        accent3=RGB(230, 219, 116),
    ),

    "dracula": Theme(
        name="dracula",
        primary=RGB(189, 147, 249),
        secondary=RGB(139, 233, 253),
        success=RGB(80, 250, 123),
        warning=RGB(255, 184, 108),
        error=RGB(255, 85, 85),
        info=RGB(139, 233, 253),
        muted=RGB(98, 114, 164),
        bg_primary=RGB(40, 42, 54),
        bg_secondary=RGB(68, 71, 90),
        text=RGB(248, 248, 242),
        accent1=RGB(255, 121, 198),
        accent2=RGB(80, 250, 123),
        accent3=RGB(241, 250, 140),
    ),

    "nord": Theme(
        name="nord",
        primary=RGB(136, 192, 208),
        secondary=RGB(129, 161, 193),
        success=RGB(163, 190, 140),
        warning=RGB(235, 203, 139),
        error=RGB(191, 97, 106),
        info=RGB(136, 192, 208),
        muted=RGB(76, 86, 106),
        bg_primary=RGB(46, 52, 64),
        bg_secondary=RGB(59, 66, 82),
        text=RGB(236, 239, 244),
        accent1=RGB(180, 142, 173),
        accent2=RGB(143, 188, 187),
        accent3=RGB(208, 135, 112),
    ),

    "solarized_dark": Theme(
        name="solarized_dark",
        primary=RGB(38, 139, 210),
        secondary=RGB(42, 161, 152),
        success=RGB(133, 153, 0),
        warning=RGB(181, 137, 0),
        error=RGB(220, 50, 47),
        info=RGB(38, 139, 210),
        muted=RGB(88, 110, 117),
        bg_primary=RGB(0, 43, 54),
        bg_secondary=RGB(7, 54, 66),
        text=RGB(147, 161, 161),
        accent1=RGB(211, 54, 130),
        accent2=RGB(108, 113, 196),
        accent3=RGB(203, 75, 22),
    ),

    "gruvbox": Theme(
        name="gruvbox",
        primary=RGB(215, 153, 33),
        secondary=RGB(152, 151, 26),
        success=RGB(184, 187, 38),
        warning=RGB(250, 189, 47),
        error=RGB(251, 73, 52),
        info=RGB(131, 165, 152),
        muted=RGB(146, 131, 116),
        bg_primary=RGB(40, 40, 40),
        bg_secondary=RGB(60, 56, 54),
        text=RGB(235, 219, 178),
        accent1=RGB(211, 134, 155),
        accent2=RGB(142, 192, 124),
        accent3=RGB(254, 128, 25),
    ),

    "ocean": Theme(
        name="ocean",
        primary=RGB(0, 150, 255),
        secondary=RGB(0, 200, 200),
        success=RGB(0, 255, 150),
        warning=RGB(255, 200, 50),
        error=RGB(255, 80, 80),
        info=RGB(100, 200, 255),
        muted=RGB(100, 130, 150),
        bg_primary=RGB(10, 25, 45),
        bg_secondary=RGB(20, 40, 65),
        text=RGB(200, 230, 255),
        accent1=RGB(0, 255, 200),
        accent2=RGB(150, 100, 255),
        accent3=RGB(255, 150, 50),
    ),

    "forest": Theme(
        name="forest",
        primary=RGB(100, 200, 100),
        secondary=RGB(150, 180, 80),
        success=RGB(80, 255, 80),
        warning=RGB(230, 200, 50),
        error=RGB(255, 100, 80),
        info=RGB(100, 180, 150),
        muted=RGB(100, 120, 100),
        bg_primary=RGB(20, 35, 20),
        bg_secondary=RGB(30, 50, 30),
        text=RGB(200, 230, 200),
        accent1=RGB(200, 255, 100),
        accent2=RGB(100, 200, 180),
        accent3=RGB(230, 180, 100),
    ),

    "cyberpunk": Theme(
        name="cyberpunk",
        primary=RGB(255, 0, 128),
        secondary=RGB(0, 255, 255),
        success=RGB(0, 255, 100),
        warning=RGB(255, 255, 0),
        error=RGB(255, 0, 50),
        info=RGB(0, 200, 255),
        muted=RGB(100, 100, 120),
        bg_primary=RGB(10, 10, 20),
        bg_secondary=RGB(20, 20, 40),
        text=RGB(230, 230, 250),
        accent1=RGB(255, 100, 200),
        accent2=RGB(100, 255, 255),
        accent3=RGB(255, 200, 0),
    ),

    "sunset": Theme(
        name="sunset",
        primary=RGB(255, 100, 50),
        secondary=RGB(255, 150, 80),
        success=RGB(100, 255, 150),
        warning=RGB(255, 200, 50),
        error=RGB(255, 50, 80),
        info=RGB(200, 150, 255),
        muted=RGB(150, 120, 100),
        bg_primary=RGB(40, 20, 30),
        bg_secondary=RGB(60, 30, 45),
        text=RGB(255, 230, 220),
        accent1=RGB(255, 100, 150),
        accent2=RGB(255, 200, 100),
        accent3=RGB(200, 100, 255),
    ),
}

# Current active theme
_current_theme: Theme = THEMES["default"]


def set_theme(theme: Theme) -> None:
    """Set the current theme."""
    global _current_theme
    _current_theme = theme


def get_theme() -> Theme:
    """Get the current theme."""
    return _current_theme


def use_theme(name: str) -> None:
    """Use a pre-defined theme by name."""
    if name in THEMES:
        set_theme(THEMES[name])
    else:
        raise ValueError(f"Unknown theme: {name}. Available: {list(THEMES.keys())}")


def register_theme(theme: Theme) -> None:
    """Register a custom theme."""
    THEMES[theme.name] = theme


def list_themes() -> list:
    """List all available theme names."""
    return list(THEMES.keys())
