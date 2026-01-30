# ChromaForge

**Advanced Terminal Coloring for Python** - A modern, feature-rich terminal styling library that goes beyond colorama and rich.

[![PyPI version](https://img.shields.io/pypi/v/chromaforge.svg)](https://pypi.org/project/chromaforge/)
[![Python 3.8+](https://img.shields.io/pypi/pyversions/chromaforge.svg)](https://pypi.org/project/chromaforge/)
[![License: MIT](https://img.shields.io/pypi/l/chromaforge.svg)](https://opensource.org/licenses/MIT)

## Features

- **True Color (24-bit RGB)** - Full RGB color support for modern terminals
- **Chainable API** - Fluent interface for easy style composition
- **Gradients** - Beautiful text gradients with 12+ presets
- **Animations** - Typing effects, spinners, progress bars, and more
- **UI Components** - Boxes, tables, panels, and rules
- **ANSI-Aware String Handling** - Proper truncation, wrapping, and alignment
- **Themes** - 10 built-in themes including Monokai, Dracula, Nord
- **Zero Dependencies** - Pure Python, no external dependencies
- **Cross-Platform** - Windows, macOS, and Linux support

## Installation

```bash
pip install chromaforge
```

## Quick Start

```python
from chromaforge import forge

# Simple colored text
print(forge("Hello World").red().bold())

# RGB colors
print(forge("Custom Color").rgb(255, 100, 50))

# Hex colors
print(forge("Hex Color").hex("#ff6b6b"))

# Chained styles
print(forge("Styled Text").blue().bold().underline().on_white())

# Gradients
print(forge("Rainbow Text").rainbow())
```

## The Forge API

The `forge()` function is the main entry point for styling text:

```python
from chromaforge import forge

# Basic colors
forge("Text").black()
forge("Text").red()
forge("Text").green()
forge("Text").yellow()
forge("Text").blue()
forge("Text").magenta()
forge("Text").cyan()
forge("Text").white()

# Bright colors
forge("Text").bright_red()
forge("Text").bright_green()
# ... and more

# Background colors
forge("Text").on_red()
forge("Text").on_blue()
forge("Text").on_rgb(50, 50, 50)

# Styles
forge("Text").bold()
forge("Text").dim()
forge("Text").italic()
forge("Text").underline()
forge("Text").strikethrough()
forge("Text").reverse()
forge("Text").blink()

# Chain everything
print(forge("Important!").red().bold().underline().on_yellow())
```

## RGB, HSL, and Hex Colors

```python
from chromaforge import forge, RGB, HSL, HEX

# RGB (0-255)
print(forge("RGB Color").rgb(255, 128, 64))

# HSL (hue: 0-360, saturation: 0-100, lightness: 0-100)
print(forge("HSL Color").hsl(180, 100, 50))

# Hex colors
print(forge("Hex Color").hex("#ff6b6b"))
print(forge("Short Hex").hex("#f66"))

# Background colors
print(forge("BG Color").on_rgb(30, 30, 50))
print(forge("BG Hex").on_hex("#1a1a2e"))

# Color objects
color = RGB(100, 200, 150)
print(f"RGB: {color.r}, {color.g}, {color.b}")
print(f"As Hex: {color.to_hex()}")
print(f"As HSL: {color.to_hsl()}")

# Color manipulation
lighter = color.lighten(0.2)
darker = color.darken(0.2)
blended = color.blend(RGB(255, 0, 0), 0.5)
```

## Gradients

```python
from chromaforge import forge, gradient, Gradient, rainbow, fire, ocean, sunset, neon

# Preset gradients
print(rainbow("Rainbow gradient text!"))
print(fire("Fire gradient text!"))
print(ocean("Ocean gradient text!"))
print(sunset("Sunset gradient text!"))
print(neon("Neon gradient text!"))

# Custom two-color gradient
print(gradient("Custom gradient", "#ff0000", "#0000ff"))

# Multi-color gradient
grad = Gradient(["#ff0000", "#ffff00", "#00ff00", "#0000ff"])
print(grad.apply("Multi-color gradient text"))

# Using forge
print(forge("Gradient").gradient("#ff6b6b", "#4ecdc4"))
```

### Available Gradient Presets

| Preset | Description |
|--------|-------------|
| `rainbow` | Classic rainbow colors |
| `fire` | Yellow to red to dark red |
| `ocean` | Cyan to deep blue |
| `forest` | Light to dark green |
| `sunset` | Gold to purple |
| `neon` | Magenta, cyan, yellow cycle |
| `pastel` | Soft pastel colors |
| `matrix` | Green terminal style |
| `synthwave` | Pink, purple, blue |
| `autumn` | Gold, orange, brown |
| `ice` | White to blue |
| `candy` | Pink, white, green, blue |

## Styles

```python
from chromaforge import Style, StyleBuilder

# Define reusable styles
error_style = Style(fg="red", bold=True)
warning_style = Style(fg="yellow", italic=True)
success_style = Style(fg="#00ff00", bold=True)

print(error_style("Error: Something went wrong!"))
print(warning_style("Warning: Check your input"))
print(success_style("Success: Operation completed"))

# Using StyleBuilder
style = (StyleBuilder()
    .foreground("#ff6b6b")
    .background("#2d2d2d")
    .bold()
    .underline()
    .build())

print(style("Styled with builder"))

# Combine styles
combined = error_style.combine(Style(underline=True))
print(combined("Combined style"))
```

## UI Components

### Box

```python
from chromaforge import Box

# Simple box
box = Box("Hello World", style="rounded", color="cyan")
print(box)

# Box with title
box = Box(
    ["Line 1", "Line 2", "Line 3"],
    title="My Box",
    style="double",
    color="yellow"
)
print(box)
```

**Box Styles:** `single`, `double`, `rounded`, `bold`, `ascii`

### Table

```python
from chromaforge import Table

table = Table(
    headers=["Name", "Age", "City"],
    rows=[
        ["Alice", "30", "New York"],
        ["Bob", "25", "Los Angeles"],
        ["Charlie", "35", "Chicago"],
    ],
    style="rounded",
    color="cyan"
)
print(table)
```

### Progress Bar

```python
from chromaforge import Progress
import time

progress = Progress(total=100, width=40, show_percent=True)
for i in range(101):
    progress.update(i)
    time.sleep(0.02)
progress.finish("Complete!")
```

### Spinner

```python
from chromaforge import Spinner
import time

# As context manager
with Spinner("Loading", style="dots", color="cyan") as spinner:
    time.sleep(3)
spinner.stop("Done!")

# Manual control
spinner = Spinner("Processing", style="moon")
spinner.start()
time.sleep(2)
spinner.stop("Finished!")
```

**Spinner Styles:** `dots`, `line`, `circle`, `square`, `arrow`, `bounce`, `pulse`, `dots2`, `moon`, `clock`

### Panel

```python
from chromaforge import Panel

panel = Panel(
    "This is important information that you should read.",
    title="Notice",
    subtitle="v1.0",
    border_color="yellow",
    style="rounded"
)
print(panel)
```

### Rule (Divider)

```python
from chromaforge import Rule

print(Rule("Section Title", color="cyan"))
print(Rule(style="double"))
print(Rule("Left Aligned", align="left"))
```

### Columns

```python
from chromaforge import Columns

cols = Columns(
    ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6"],
    num_columns=3,
    padding=4
)
print(cols)
```

## Effects & Animations

```python
from chromaforge import typing, pulse, shimmer, glitch
from chromaforge.core import RGB

# Typewriter effect
typing("Hello, World!", delay=0.05, color="green")

# Pulsing text
pulse("ALERT!", duration=3.0, color=RGB(255, 0, 0))

# Shimmering rainbow
shimmer("Sparkle!", duration=5.0)

# Glitch effect
glitch("ERROR 404", duration=2.0, intensity=0.3)
```

### More Effects

```python
from chromaforge.effects import bounce, countdown, wave, loading_dots, matrix_rain

# Bouncing text
bounce("Ping!", width=40, duration=3.0)

# Countdown
countdown(5, "GO!", RGB(255, 0, 0), RGB(0, 255, 0))

# Wave animation
wave("Hello Wave!", duration=3.0, amplitude=2)

# Loading dots
loading_dots("Processing", duration=3.0)

# Matrix rain effect
matrix_rain(width=60, height=15, duration=10.0)
```

## Themes

```python
from chromaforge import Theme, set_theme, get_theme, THEMES, use_theme

# Use a built-in theme
use_theme("dracula")
theme = get_theme()

print(theme.primary_text("Primary color"))
print(theme.success_text("Success message"))
print(theme.error_text("Error message"))
print(theme.warning_text("Warning message"))

# Available themes
print(list(THEMES.keys()))
# ['default', 'monokai', 'dracula', 'nord', 'solarized_dark',
#  'gruvbox', 'ocean', 'forest', 'cyberpunk', 'sunset']

# Create custom theme
custom_theme = Theme(
    name="my_theme",
    primary=RGB(100, 200, 255),
    secondary=RGB(255, 100, 200),
    success=RGB(100, 255, 100),
    error=RGB(255, 100, 100),
)
set_theme(custom_theme)
```

## Terminal Utilities

```python
from chromaforge import (
    Terminal, clear, clear_line, move_cursor,
    hide_cursor, show_cursor, supports_color,
    supports_truecolor, get_terminal_size
)

# Check terminal capabilities
print(f"Color support: {supports_color()}")
print(f"True color: {supports_truecolor()}")
print(f"Size: {get_terminal_size()}")

# Terminal operations
term = Terminal()
term.clear()
term.move_to(10, 5)
term.set_title("My App")

# Fullscreen mode
with term.fullscreen():
    term.move_to(1, 1)
    print("Fullscreen mode!")
    input("Press Enter to exit...")
```

## ANSI-Aware String Handling

ChromaForge properly handles ANSI escape sequences in string operations:

```python
from chromaforge.terminal import ANSIString, truncate, wrap_text

# Create an ANSI string
text = "\033[31mHello\033[0m \033[32mWorld\033[0m"
s = ANSIString(text)

# Get visible length (ignoring ANSI codes)
print(s.visible_length())  # 11

# Truncate with proper ANSI handling
print(truncate(text, 8, "..."))  # Properly closes color codes

# Slice with ANSI preservation
print(s[0:5])  # Gets "Hello" with its red color intact

# Wrap text preserving colors
lines = wrap_text(text, 40)

# Center/justify with ANSI preservation
print(s.center(20))
print(s.ljust(20))
print(s.rjust(20))
```

## Color Functions

```python
from chromaforge import red, green, blue, yellow, rgb, hex_color
from chromaforge.colors import blend, lighten, darken, complement, grayscale, get_color

# Quick color functions
print(red("Red text"))
print(green("Green text"))
print(blue("Blue text"))

# RGB and Hex
print(rgb("Custom", 255, 128, 64))
print(hex_color("Hex color", "#ff6b6b"))

# Color manipulation
from chromaforge.core import RGB

color = RGB(100, 150, 200)
print(f"Original: {color}")
print(f"Lighter: {lighten(color, 0.3)}")
print(f"Darker: {darken(color, 0.3)}")
print(f"Complement: {complement(color)}")
print(f"Grayscale: {grayscale(color)}")

# Blend two colors
blended = blend(RGB(255, 0, 0), RGB(0, 0, 255), 0.5)
print(f"Blended: {blended}")  # Purple

# Named colors from palette
coral = get_color("coral")
turquoise = get_color("turquoise")
```

## Comparison with Other Libraries

| Feature | ChromaForge | Colorama | Rich |
|---------|-------------|----------|------|
| True Color (24-bit) | ✅ | ❌ | ✅ |
| Gradients | ✅ | ❌ | ❌ |
| Chainable API | ✅ | ❌ | ❌ |
| Animations | ✅ | ❌ | ✅ |
| ANSI-aware truncation | ✅ | ❌ | ✅ |
| Zero dependencies | ✅ | ✅ | ❌ |
| Themes | ✅ | ❌ | ✅ |
| HSL colors | ✅ | ❌ | ❌ |
| Color manipulation | ✅ | ❌ | ❌ |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **GitHub:** https://github.com/AeonLtd/chromaforge
- **PyPI:** https://pypi.org/project/chromaforge/
- **Issues:** https://github.com/AeonLtd/chromaforge/issues
