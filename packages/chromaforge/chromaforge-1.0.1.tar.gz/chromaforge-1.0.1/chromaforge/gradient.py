"""
Gradient module for ChromaForge.

Provides gradient text effects with various preset gradients and custom gradient support.
"""

from typing import List, Union, Tuple, Optional
from .core import RGB, HSL, HEX, parse_color, Color, ESC, RESET_CODE, Forge


class Gradient:
    """
    Create gradient text effects.

    Example:
        # Two-color gradient
        grad = Gradient("#ff0000", "#0000ff")
        print(grad.apply("Hello World"))

        # Multi-color gradient
        grad = Gradient(["red", "yellow", "green"])
        print(grad.apply("Rainbow Text"))
    """

    def __init__(self, *colors: Union[Color, List[Color]]):
        """
        Initialize a gradient with colors.

        Args:
            colors: Two or more colors to create the gradient
        """
        if len(colors) == 1 and isinstance(colors[0], list):
            self._colors = [parse_color(c) for c in colors[0]]
        else:
            self._colors = [parse_color(c) for c in colors]

        if len(self._colors) < 2:
            self._colors = [RGB(255, 255, 255), RGB(255, 255, 255)]

    def _interpolate(self, progress: float) -> RGB:
        """Interpolate color at the given progress (0-1)."""
        if progress <= 0:
            return self._colors[0]
        if progress >= 1:
            return self._colors[-1]

        # Find which segment we're in
        segment_count = len(self._colors) - 1
        segment_progress = progress * segment_count
        segment_index = int(segment_progress)
        segment_index = min(segment_index, segment_count - 1)

        local_progress = segment_progress - segment_index

        color1 = self._colors[segment_index]
        color2 = self._colors[segment_index + 1]

        return color1.blend(color2, local_progress)

    def apply(self, text: str) -> Forge:
        """Apply the gradient to text."""
        if not text:
            return Forge("")

        result = []
        length = len(text)

        for i, char in enumerate(text):
            if char == " ":
                result.append(char)
            else:
                progress = i / max(length - 1, 1)
                color = self._interpolate(progress)
                result.append(f"{color.to_ansi_fg()}{char}")

        return Forge("".join(result) + RESET_CODE)

    def apply_vertical(self, lines: List[str]) -> List[Forge]:
        """Apply the gradient vertically across multiple lines."""
        if not lines:
            return []

        result = []
        line_count = len(lines)

        for i, line in enumerate(lines):
            progress = i / max(line_count - 1, 1)
            color = self._interpolate(progress)
            result.append(Forge(f"{color.to_ansi_fg()}{line}{RESET_CODE}"))

        return result

    def get_colors(self, count: int) -> List[RGB]:
        """Get a list of interpolated colors."""
        if count <= 0:
            return []
        if count == 1:
            return [self._colors[0]]

        return [self._interpolate(i / (count - 1)) for i in range(count)]


# Pre-defined gradient presets
GRADIENT_PRESETS = {
    "rainbow": [
        RGB(255, 0, 0),      # Red
        RGB(255, 127, 0),    # Orange
        RGB(255, 255, 0),    # Yellow
        RGB(0, 255, 0),      # Green
        RGB(0, 0, 255),      # Blue
        RGB(75, 0, 130),     # Indigo
        RGB(148, 0, 211),    # Violet
    ],
    "fire": [
        RGB(255, 255, 0),    # Yellow
        RGB(255, 127, 0),    # Orange
        RGB(255, 0, 0),      # Red
        RGB(139, 0, 0),      # Dark Red
    ],
    "ocean": [
        RGB(0, 255, 255),    # Cyan
        RGB(0, 127, 255),    # Light Blue
        RGB(0, 0, 255),      # Blue
        RGB(0, 0, 139),      # Dark Blue
    ],
    "forest": [
        RGB(144, 238, 144),  # Light Green
        RGB(0, 255, 0),      # Green
        RGB(34, 139, 34),    # Forest Green
        RGB(0, 100, 0),      # Dark Green
    ],
    "sunset": [
        RGB(255, 215, 0),    # Gold
        RGB(255, 140, 0),    # Orange
        RGB(255, 69, 0),     # Red-Orange
        RGB(255, 0, 127),    # Pink
        RGB(148, 0, 211),    # Purple
    ],
    "neon": [
        RGB(255, 0, 255),    # Magenta
        RGB(0, 255, 255),    # Cyan
        RGB(255, 255, 0),    # Yellow
        RGB(255, 0, 255),    # Magenta
    ],
    "pastel": [
        RGB(255, 182, 193),  # Light Pink
        RGB(255, 218, 185),  # Peach
        RGB(255, 255, 224),  # Light Yellow
        RGB(152, 251, 152),  # Pale Green
        RGB(173, 216, 230),  # Light Blue
        RGB(230, 230, 250),  # Lavender
    ],
    "matrix": [
        RGB(0, 50, 0),       # Very Dark Green
        RGB(0, 150, 0),      # Dark Green
        RGB(0, 255, 0),      # Green
        RGB(150, 255, 150),  # Light Green
    ],
    "synthwave": [
        RGB(255, 0, 128),    # Hot Pink
        RGB(128, 0, 255),    # Purple
        RGB(0, 128, 255),    # Blue
    ],
    "autumn": [
        RGB(255, 215, 0),    # Gold
        RGB(255, 140, 0),    # Orange
        RGB(205, 92, 92),    # Indian Red
        RGB(139, 69, 19),    # Saddle Brown
    ],
    "ice": [
        RGB(255, 255, 255),  # White
        RGB(200, 220, 255),  # Light Blue
        RGB(100, 150, 255),  # Blue
        RGB(50, 100, 200),   # Dark Blue
    ],
    "candy": [
        RGB(255, 105, 180),  # Hot Pink
        RGB(255, 182, 193),  # Light Pink
        RGB(255, 255, 255),  # White
        RGB(152, 251, 152),  # Pale Green
        RGB(135, 206, 250),  # Light Sky Blue
    ],
}


def gradient(text: str, start: Color, end: Color) -> Forge:
    """
    Apply a simple two-color gradient to text.

    Args:
        text: The text to style
        start: Starting color
        end: Ending color

    Returns:
        Styled Forge object
    """
    return Gradient(start, end).apply(text)


def gradient_preset(text: str, preset: str) -> Forge:
    """
    Apply a preset gradient to text.

    Args:
        text: The text to style
        preset: Name of the preset gradient

    Returns:
        Styled Forge object
    """
    colors = GRADIENT_PRESETS.get(preset.lower(), GRADIENT_PRESETS["rainbow"])
    return Gradient(colors).apply(text)


def rainbow(text: str) -> Forge:
    """Apply rainbow gradient to text."""
    return Gradient(GRADIENT_PRESETS["rainbow"]).apply(text)


def fire(text: str) -> Forge:
    """Apply fire gradient to text."""
    return Gradient(GRADIENT_PRESETS["fire"]).apply(text)


def ocean(text: str) -> Forge:
    """Apply ocean gradient to text."""
    return Gradient(GRADIENT_PRESETS["ocean"]).apply(text)


def forest(text: str) -> Forge:
    """Apply forest gradient to text."""
    return Gradient(GRADIENT_PRESETS["forest"]).apply(text)


def sunset(text: str) -> Forge:
    """Apply sunset gradient to text."""
    return Gradient(GRADIENT_PRESETS["sunset"]).apply(text)


def neon(text: str) -> Forge:
    """Apply neon gradient to text."""
    return Gradient(GRADIENT_PRESETS["neon"]).apply(text)


def multicolor(text: str, colors: List[Color]) -> Forge:
    """Apply a custom multi-color gradient to text."""
    return Gradient(colors).apply(text)


class AnimatedGradient:
    """
    Create animated gradient effects.

    Example:
        anim = AnimatedGradient("rainbow")
        for frame in anim.frames("Hello World", count=10):
            print(f"\r{frame}", end="", flush=True)
            time.sleep(0.1)
    """

    def __init__(self, preset: str = "rainbow"):
        self._colors = GRADIENT_PRESETS.get(preset.lower(), GRADIENT_PRESETS["rainbow"])

    def frames(self, text: str, count: int = 20) -> List[Forge]:
        """Generate animation frames."""
        frames = []
        color_count = len(self._colors)

        for frame_idx in range(count):
            offset = frame_idx / count
            result = []

            for i, char in enumerate(text):
                if char == " ":
                    result.append(char)
                else:
                    progress = ((i / len(text)) + offset) % 1.0
                    segment_progress = progress * (color_count - 1)
                    segment_index = int(segment_progress) % (color_count - 1)
                    local_progress = segment_progress - int(segment_progress)

                    color1 = self._colors[segment_index]
                    color2 = self._colors[(segment_index + 1) % color_count]
                    color = color1.blend(color2, local_progress)

                    result.append(f"{color.to_ansi_fg()}{char}")

            frames.append(Forge("".join(result) + RESET_CODE))

        return frames
