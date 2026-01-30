"""
Effects module for ChromaForge.

Provides animated text effects like typing, pulse, shimmer, and glitch.
"""

import sys
import time
import random
from typing import Optional, List, Generator
from .core import Forge, RGB, ESC, RESET_CODE
from .gradient import GRADIENT_PRESETS


def typing(
    text: str,
    delay: float = 0.05,
    color: Optional[str] = None,
    cursor: str = "█",
    show_cursor: bool = True
) -> None:
    """
    Display text with a typewriter effect.

    Args:
        text: The text to display
        delay: Delay between characters in seconds
        color: Optional color for the text
        cursor: Cursor character to show while typing
        show_cursor: Whether to show a blinking cursor

    Example:
        typing("Hello, World!", delay=0.1, color="green")
    """
    color_code = ""
    if color:
        colors = {
            "black": 30, "red": 31, "green": 32, "yellow": 33,
            "blue": 34, "magenta": 35, "cyan": 36, "white": 37,
        }
        if color in colors:
            color_code = f"{ESC}{colors[color]}m"

    for i, char in enumerate(text):
        if show_cursor and i > 0:
            # Remove previous cursor
            sys.stdout.write("\b \b")

        sys.stdout.write(f"{color_code}{char}")

        if show_cursor:
            sys.stdout.write(f"{cursor}")

        sys.stdout.flush()
        time.sleep(delay)

    if show_cursor:
        sys.stdout.write("\b \b")

    if color_code:
        sys.stdout.write(RESET_CODE)

    sys.stdout.write("\n")
    sys.stdout.flush()


def pulse(
    text: str,
    duration: float = 2.0,
    cycles: int = 3,
    color: RGB = RGB(255, 0, 0)
) -> None:
    """
    Display text with a pulsing brightness effect.

    Args:
        text: The text to display
        duration: Total duration of the effect
        cycles: Number of pulse cycles
        color: Base color for the pulse

    Example:
        pulse("ALERT!", duration=3.0, color=RGB(255, 0, 0))
    """
    import math

    frames = int(duration * 30)  # 30 FPS
    frame_delay = duration / frames

    for frame in range(frames):
        # Calculate brightness using sine wave (0.3 to 1.0)
        progress = (frame / frames) * cycles * 2 * math.pi
        brightness = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(progress))

        r = int(color.r * brightness)
        g = int(color.g * brightness)
        b = int(color.b * brightness)

        styled = f"{ESC}38;2;{r};{g};{b}m{text}{RESET_CODE}"
        sys.stdout.write(f"\r{styled}")
        sys.stdout.flush()
        time.sleep(frame_delay)

    sys.stdout.write("\n")


def shimmer(
    text: str,
    duration: float = 3.0,
    colors: Optional[List[RGB]] = None
) -> None:
    """
    Display text with a shimmering rainbow effect.

    Args:
        text: The text to display
        duration: Total duration of the effect
        colors: Colors to use for shimmer (default: rainbow)

    Example:
        shimmer("✨ Sparkle ✨", duration=5.0)
    """
    if colors is None:
        colors = GRADIENT_PRESETS["rainbow"]

    frames = int(duration * 20)  # 20 FPS
    frame_delay = duration / frames
    color_count = len(colors)

    for frame in range(frames):
        offset = frame / frames
        result = []

        for i, char in enumerate(text):
            if char == " ":
                result.append(char)
            else:
                progress = ((i / max(len(text) - 1, 1)) + offset) % 1.0
                segment_progress = progress * (color_count - 1)
                segment_index = int(segment_progress) % (color_count - 1)
                local_progress = segment_progress - int(segment_progress)

                color1 = colors[segment_index]
                color2 = colors[(segment_index + 1) % color_count]
                color = color1.blend(color2, local_progress)

                result.append(f"{color.to_ansi_fg()}{char}")

        sys.stdout.write(f"\r{''.join(result)}{RESET_CODE}")
        sys.stdout.flush()
        time.sleep(frame_delay)

    sys.stdout.write("\n")


def glitch(
    text: str,
    duration: float = 2.0,
    intensity: float = 0.3
) -> None:
    """
    Display text with a glitch effect.

    Args:
        text: The text to display
        duration: Total duration of the effect
        intensity: Glitch intensity (0.0 to 1.0)

    Example:
        glitch("ERROR 404", duration=3.0, intensity=0.5)
    """
    glitch_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
    frames = int(duration * 15)
    frame_delay = duration / frames

    for frame in range(frames):
        result = []
        glitch_active = random.random() < intensity

        for char in text:
            if char == " ":
                result.append(char)
            elif glitch_active and random.random() < intensity * 0.5:
                # Random glitch character
                glitch_char = random.choice(glitch_chars)
                # Random color
                r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
                result.append(f"{ESC}38;2;{r};{g};{b}m{glitch_char}")
            else:
                result.append(char)

        # Sometimes offset the text
        offset = ""
        if glitch_active and random.random() < 0.3:
            offset = " " * random.randint(0, 3)

        sys.stdout.write(f"\r{offset}{''.join(result)}{RESET_CODE}   ")
        sys.stdout.flush()
        time.sleep(frame_delay)

    # Final clean display
    sys.stdout.write(f"\r{text}{RESET_CODE}   \n")


def matrix_rain(
    width: int = 80,
    height: int = 20,
    duration: float = 5.0,
    density: float = 0.1
) -> None:
    """
    Display a Matrix-style rain effect.

    Args:
        width: Width of the display
        height: Height of the display
        duration: Duration of the effect
        density: Density of the rain drops

    Example:
        matrix_rain(width=60, height=15, duration=10.0)
    """
    import random
    import string

    chars = string.ascii_letters + string.digits + "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ"
    columns = [0] * width
    speeds = [random.randint(1, 3) for _ in range(width)]

    frames = int(duration * 15)
    frame_delay = duration / frames

    # Hide cursor
    sys.stdout.write(f"{ESC}?25l")

    try:
        for _ in range(frames):
            lines = []

            for y in range(height):
                line = []
                for x in range(width):
                    col_pos = columns[x]
                    if y == col_pos % height:
                        # Bright head
                        char = random.choice(chars)
                        line.append(f"{ESC}38;2;200;255;200m{char}")
                    elif y < col_pos % height and y > (col_pos - 10) % height:
                        # Trail
                        brightness = 255 - (col_pos % height - y) * 25
                        brightness = max(50, brightness)
                        char = random.choice(chars) if random.random() < 0.1 else " "
                        if char != " ":
                            line.append(f"{ESC}38;2;0;{brightness};0m{char}")
                        else:
                            line.append(" ")
                    else:
                        line.append(" ")
                lines.append("".join(line))

            # Move cursor to top
            sys.stdout.write(f"{ESC}H")
            sys.stdout.write("\n".join(lines))
            sys.stdout.write(RESET_CODE)
            sys.stdout.flush()

            # Update columns
            for i in range(width):
                if random.random() < density:
                    columns[i] += speeds[i]

            time.sleep(frame_delay)

    finally:
        # Show cursor
        sys.stdout.write(f"{ESC}?25h")
        sys.stdout.write(RESET_CODE)
        sys.stdout.flush()


def bounce(
    text: str,
    width: int = 40,
    duration: float = 3.0,
    color: Optional[RGB] = None
) -> None:
    """
    Display text bouncing left to right.

    Args:
        text: The text to display
        width: Width of the bounce area
        duration: Duration of the effect
        color: Color for the text

    Example:
        bounce("Ping Pong!", width=50, duration=5.0)
    """
    frames = int(duration * 20)
    frame_delay = duration / frames
    max_pos = width - len(text)

    color_code = ""
    if color:
        color_code = f"{ESC}38;2;{color.r};{color.g};{color.b}m"

    direction = 1
    position = 0

    for _ in range(frames):
        padding = " " * position
        sys.stdout.write(f"\r{padding}{color_code}{text}{RESET_CODE}" + " " * (max_pos - position))
        sys.stdout.flush()

        position += direction
        if position >= max_pos or position <= 0:
            direction *= -1

        time.sleep(frame_delay)

    sys.stdout.write("\n")


def countdown(
    start: int = 10,
    message: str = "GO!",
    color_start: RGB = RGB(255, 0, 0),
    color_end: RGB = RGB(0, 255, 0)
) -> None:
    """
    Display an animated countdown.

    Args:
        start: Starting number
        message: Message to display at the end
        color_start: Starting color (at highest number)
        color_end: Ending color (at 1)

    Example:
        countdown(5, "LAUNCH!", RGB(255, 100, 0), RGB(0, 255, 100))
    """
    for i in range(start, 0, -1):
        progress = (start - i) / (start - 1) if start > 1 else 1
        color = color_start.blend(color_end, progress)

        styled = f"{ESC}38;2;{color.r};{color.g};{color.b}m{ESC}1m{i}{RESET_CODE}"
        sys.stdout.write(f"\r{styled}   ")
        sys.stdout.flush()
        time.sleep(1)

    # Final message
    styled = f"{ESC}38;2;{color_end.r};{color_end.g};{color_end.b}m{ESC}1m{message}{RESET_CODE}"
    sys.stdout.write(f"\r{styled}   \n")
    sys.stdout.flush()


def wave(
    text: str,
    duration: float = 3.0,
    amplitude: int = 2,
    color: Optional[RGB] = None
) -> None:
    """
    Display text with a wave animation.

    Args:
        text: The text to display
        duration: Duration of the effect
        amplitude: Height of the wave
        color: Color for the text

    Example:
        wave("Hello Wave!", duration=5.0)
    """
    import math

    frames = int(duration * 15)
    frame_delay = duration / frames

    color_code = ""
    if color:
        color_code = f"{ESC}38;2;{color.r};{color.g};{color.b}m"

    for frame in range(frames):
        lines = [""] * (amplitude * 2 + 1)
        middle = amplitude

        for i, char in enumerate(text):
            phase = (frame / 5) + (i / 2)
            offset = int(math.sin(phase) * amplitude)
            line_idx = middle - offset

            # Pad other lines with spaces
            for j in range(len(lines)):
                if j == line_idx:
                    lines[j] += f"{color_code}{char}{RESET_CODE}"
                else:
                    lines[j] += " "

        # Clear and redraw
        sys.stdout.write(f"{ESC}{amplitude * 2 + 1}A")  # Move up
        for line in lines:
            sys.stdout.write(f"\r{line}\n")
        sys.stdout.flush()

        time.sleep(frame_delay)


def loading_dots(message: str = "Loading", duration: float = 3.0) -> None:
    """
    Display a loading animation with dots.

    Args:
        message: The loading message
        duration: Duration of the animation

    Example:
        loading_dots("Processing", duration=5.0)
    """
    frames = int(duration * 4)
    frame_delay = duration / frames

    for frame in range(frames):
        dots = "." * ((frame % 4))
        sys.stdout.write(f"\r{message}{dots}   ")
        sys.stdout.flush()
        time.sleep(frame_delay)

    sys.stdout.write(f"\r{message}... Done!\n")
