"""Tests for ChromaForge core module."""

import pytest
from chromaforge import forge, RGB, HSL, HEX
from chromaforge.terminal import ANSIString, strip_ansi, visible_length, truncate


class TestRGB:
    """Tests for RGB color class."""

    def test_rgb_creation(self):
        color = RGB(255, 128, 64)
        assert color.r == 255
        assert color.g == 128
        assert color.b == 64

    def test_rgb_clamping(self):
        color = RGB(300, -50, 128)
        assert color.r == 255
        assert color.g == 0
        assert color.b == 128

    def test_rgb_to_hex(self):
        color = RGB(255, 128, 64)
        assert color.to_hex() == "#ff8040"

    def test_rgb_to_hsl(self):
        color = RGB(255, 0, 0)
        hsl = color.to_hsl()
        assert hsl.h == 0
        assert hsl.s == 100
        assert hsl.l == 50

    def test_rgb_blend(self):
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        purple = red.blend(blue, 0.5)
        assert purple.r == 127
        assert purple.g == 0
        assert purple.b == 127

    def test_rgb_lighten(self):
        color = RGB(100, 100, 100)
        lighter = color.lighten(0.5)
        assert lighter.r > color.r
        assert lighter.g > color.g
        assert lighter.b > color.b

    def test_rgb_darken(self):
        color = RGB(100, 100, 100)
        darker = color.darken(0.5)
        assert darker.r < color.r
        assert darker.g < color.g
        assert darker.b < color.b


class TestHSL:
    """Tests for HSL color class."""

    def test_hsl_creation(self):
        color = HSL(180, 50, 50)
        assert color.h == 180
        assert color.s == 50
        assert color.l == 50

    def test_hsl_to_rgb(self):
        hsl = HSL(0, 100, 50)  # Red
        rgb = hsl.to_rgb()
        assert rgb.r == 255
        assert rgb.g == 0
        assert rgb.b == 0

    def test_hsl_hue_wrap(self):
        color = HSL(400, 50, 50)
        assert color.h == 40  # 400 % 360


class TestHEX:
    """Tests for HEX color class."""

    def test_hex_to_rgb(self):
        color = HEX("#ff8040")
        rgb = color.to_rgb()
        assert rgb.r == 255
        assert rgb.g == 128
        assert rgb.b == 64

    def test_hex_short_form(self):
        color = HEX("#f80")
        rgb = color.to_rgb()
        assert rgb.r == 255
        assert rgb.g == 136
        assert rgb.b == 0

    def test_hex_without_hash(self):
        color = HEX("ff8040")
        rgb = color.to_rgb()
        assert rgb.r == 255


class TestForge:
    """Tests for Forge class."""

    def test_forge_creation(self):
        f = forge("Hello")
        assert f.strip() == "Hello"

    def test_forge_red(self):
        f = forge("Hello").red()
        result = str(f)
        assert "\033[31m" in result
        assert "Hello" in result

    def test_forge_bold(self):
        f = forge("Hello").bold()
        result = str(f)
        assert "\033[1m" in result

    def test_forge_chain(self):
        f = forge("Hello").red().bold().underline()
        result = str(f)
        assert "31" in result  # red
        assert "1" in result   # bold
        assert "4" in result   # underline

    def test_forge_rgb(self):
        f = forge("Hello").rgb(255, 128, 64)
        result = str(f)
        assert "38;2;255;128;64" in result

    def test_forge_on_rgb(self):
        f = forge("Hello").on_rgb(255, 128, 64)
        result = str(f)
        assert "48;2;255;128;64" in result

    def test_forge_hex(self):
        f = forge("Hello").hex("#ff8040")
        result = str(f)
        assert "38;2;255;128;64" in result

    def test_forge_strip(self):
        f = forge("Hello").red().bold()
        assert f.strip() == "Hello"

    def test_forge_len(self):
        f = forge("Hello").red().bold()
        assert f.len() == 5

    def test_forge_add(self):
        f1 = forge("Hello").red()
        f2 = forge(" World").blue()
        combined = f1 + f2
        result = str(combined)
        assert "Hello" in result
        assert "World" in result


class TestANSIString:
    """Tests for ANSIString class."""

    def test_visible_length(self):
        text = "\033[31mHello\033[0m"
        s = ANSIString(text)
        assert s.visible_length() == 5

    def test_visible_length_multiple_codes(self):
        text = "\033[31m\033[1mHello\033[0m \033[32mWorld\033[0m"
        s = ANSIString(text)
        assert s.visible_length() == 11

    def test_strip_ansi(self):
        text = "\033[31mHello\033[0m \033[32mWorld\033[0m"
        s = ANSIString(text)
        assert s.strip_ansi() == "Hello World"

    def test_slice(self):
        text = "\033[31mHello\033[0m World"
        s = ANSIString(text)
        sliced = s.slice(0, 5)
        assert "Hello" in sliced
        assert "\033[0m" in sliced  # Should be closed

    def test_truncate(self):
        text = "\033[31mHello World\033[0m"
        s = ANSIString(text)
        truncated = s.truncate(8, "...")
        assert visible_length(truncated) == 8
        assert "..." in truncated

    def test_truncate_no_change(self):
        text = "\033[31mHi\033[0m"
        s = ANSIString(text)
        truncated = s.truncate(10, "...")
        assert truncated == text

    def test_center(self):
        text = "\033[31mHi\033[0m"
        s = ANSIString(text)
        centered = s.center(10)
        assert len(strip_ansi(centered)) == 10

    def test_ljust(self):
        text = "\033[31mHi\033[0m"
        s = ANSIString(text)
        justified = s.ljust(10)
        stripped = strip_ansi(justified)
        assert len(stripped) == 10
        assert stripped.startswith("Hi")

    def test_rjust(self):
        text = "\033[31mHi\033[0m"
        s = ANSIString(text)
        justified = s.rjust(10)
        stripped = strip_ansi(justified)
        assert len(stripped) == 10
        assert stripped.endswith("Hi")


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_strip_ansi_function(self):
        text = "\033[31mHello\033[0m"
        assert strip_ansi(text) == "Hello"

    def test_visible_length_function(self):
        text = "\033[31mHello\033[0m"
        assert visible_length(text) == 5

    def test_truncate_function(self):
        text = "\033[31mHello World\033[0m"
        result = truncate(text, 8, "...")
        assert visible_length(result) == 8
