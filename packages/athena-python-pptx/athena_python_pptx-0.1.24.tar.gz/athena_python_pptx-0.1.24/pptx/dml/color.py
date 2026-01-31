"""
Color classes matching python-pptx.

Provides RGBColor and ColorFormat for color manipulation.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..enum.dml import MSO_THEME_COLOR, MSO_COLOR_TYPE


class RGBColor:
    """
    Immutable RGB color value.

    RGBColor is an immutable value object that represents a color as
    three 8-bit values (red, green, blue). It can be created from
    individual RGB values or from a hex string.

    Examples:
        red = RGBColor(0xFF, 0x00, 0x00)
        blue = RGBColor.from_string('0000FF')
        print(red)  # 'FF0000'
    """

    def __init__(self, r: int, g: int, b: int):
        """
        Create an RGBColor from red, green, blue values.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)

        Raises:
            ValueError: If any component is outside 0-255 range
        """
        for name, val in [('r', r), ('g', g), ('b', b)]:
            if not isinstance(val, int) or not (0 <= val <= 255):
                raise ValueError(
                    f"{name} must be an integer between 0 and 255, got {val}"
                )
        self._r = r
        self._g = g
        self._b = b

    # CSS color names (common subset)
    _CSS_COLORS = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'red': (255, 0, 0),
        'green': (0, 128, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
        'gray': (128, 128, 128),
        'grey': (128, 128, 128),
        'silver': (192, 192, 192),
        'maroon': (128, 0, 0),
        'olive': (128, 128, 0),
        'navy': (0, 0, 128),
        'purple': (128, 0, 128),
        'teal': (0, 128, 128),
        'orange': (255, 165, 0),
        'pink': (255, 192, 203),
        'brown': (165, 42, 42),
        'gold': (255, 215, 0),
        'lime': (0, 255, 0),
        'aqua': (0, 255, 255),
        'coral': (255, 127, 80),
        'salmon': (250, 128, 114),
        'tomato': (255, 99, 71),
        'crimson': (220, 20, 60),
        'indigo': (75, 0, 130),
        'violet': (238, 130, 238),
        'khaki': (240, 230, 140),
        'beige': (245, 245, 220),
        'tan': (210, 180, 140),
        'chocolate': (210, 105, 30),
        'darkblue': (0, 0, 139),
        'darkgreen': (0, 100, 0),
        'darkred': (139, 0, 0),
        'lightblue': (173, 216, 230),
        'lightgreen': (144, 238, 144),
        'lightgray': (211, 211, 211),
        'lightgrey': (211, 211, 211),
        'darkgray': (169, 169, 169),
        'darkgrey': (169, 169, 169),
    }

    @classmethod
    def from_string(cls, hex_str: str) -> RGBColor:
        """
        Create an RGBColor from a hex string.

        Args:
            hex_str: 6-character hex color string (e.g., 'FF0000' or '#FF0000')

        Returns:
            RGBColor instance

        Raises:
            ValueError: If hex_str is not a valid color string
        """
        # Remove leading # if present
        if hex_str.startswith('#'):
            hex_str = hex_str[1:]

        if len(hex_str) != 6:
            raise ValueError(
                f"hex_str must be 6 characters, got {len(hex_str)}: '{hex_str}'"
            )

        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
        except ValueError:
            raise ValueError(f"Invalid hex color string: '{hex_str}'")

        return cls(r, g, b)

    @classmethod
    def from_name(cls, name: str) -> RGBColor:
        """
        Create an RGBColor from a CSS color name.

        Args:
            name: CSS color name (e.g., 'red', 'blue', 'white')

        Returns:
            RGBColor instance

        Raises:
            ValueError: If name is not a recognized color name
        """
        normalized = name.lower().strip()
        if normalized not in cls._CSS_COLORS:
            raise ValueError(
                f"Unknown color name: '{name}'. Known colors: {', '.join(sorted(cls._CSS_COLORS.keys()))}"
            )
        r, g, b = cls._CSS_COLORS[normalized]
        return cls(r, g, b)

    @classmethod
    def from_tuple(cls, rgb: tuple[int, int, int]) -> RGBColor:
        """
        Create an RGBColor from an (r, g, b) tuple.

        Args:
            rgb: Tuple of (red, green, blue) values (0-255)

        Returns:
            RGBColor instance
        """
        return cls(rgb[0], rgb[1], rgb[2])

    @property
    def r(self) -> int:
        """Red component (0-255)."""
        return self._r

    @property
    def g(self) -> int:
        """Green component (0-255)."""
        return self._g

    @property
    def b(self) -> int:
        """Blue component (0-255)."""
        return self._b

    def __str__(self) -> str:
        """Return hex string representation (e.g., 'FF0000')."""
        return f"{self._r:02X}{self._g:02X}{self._b:02X}"

    def __repr__(self) -> str:
        return f"RGBColor(0x{self._r:02X}, 0x{self._g:02X}, 0x{self._b:02X})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RGBColor):
            return NotImplemented
        return (self._r, self._g, self._b) == (other._r, other._g, other._b)

    def __hash__(self) -> int:
        return hash((self._r, self._g, self._b))

    # -------------------------------------------------------------------------
    # Convenience properties and methods
    # -------------------------------------------------------------------------

    def to_tuple(self) -> tuple[int, int, int]:
        """Return color as (r, g, b) tuple."""
        return (self._r, self._g, self._b)

    def to_hex(self, prefix: bool = False) -> str:
        """
        Return color as hex string.

        Args:
            prefix: If True, include '#' prefix

        Returns:
            Hex color string (e.g., 'FF0000' or '#FF0000')
        """
        hex_str = f"{self._r:02X}{self._g:02X}{self._b:02X}"
        return f"#{hex_str}" if prefix else hex_str

    @property
    def luminance(self) -> float:
        """
        Relative luminance (0.0 to 1.0).

        Uses the standard formula for perceived brightness.
        """
        # sRGB to linear conversion
        def linearize(c: int) -> float:
            c_norm = c / 255.0
            if c_norm <= 0.03928:
                return c_norm / 12.92
            return ((c_norm + 0.055) / 1.055) ** 2.4

        r_lin = linearize(self._r)
        g_lin = linearize(self._g)
        b_lin = linearize(self._b)
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

    @property
    def is_dark(self) -> bool:
        """True if this is a dark color (luminance < 0.5)."""
        return self.luminance < 0.5

    @property
    def is_light(self) -> bool:
        """True if this is a light color (luminance >= 0.5)."""
        return self.luminance >= 0.5

    def lighter(self, amount: float = 0.2) -> RGBColor:
        """
        Return a lighter version of this color.

        Args:
            amount: How much lighter (0.0 to 1.0, default 0.2)

        Returns:
            New RGBColor that is lighter
        """
        r = min(255, int(self._r + (255 - self._r) * amount))
        g = min(255, int(self._g + (255 - self._g) * amount))
        b = min(255, int(self._b + (255 - self._b) * amount))
        return RGBColor(r, g, b)

    def darker(self, amount: float = 0.2) -> RGBColor:
        """
        Return a darker version of this color.

        Args:
            amount: How much darker (0.0 to 1.0, default 0.2)

        Returns:
            New RGBColor that is darker
        """
        r = max(0, int(self._r * (1 - amount)))
        g = max(0, int(self._g * (1 - amount)))
        b = max(0, int(self._b * (1 - amount)))
        return RGBColor(r, g, b)

    def complement(self) -> RGBColor:
        """Return the complementary color."""
        return RGBColor(255 - self._r, 255 - self._g, 255 - self._b)

    @property
    def red(self) -> int:
        """Red component (alias for r)."""
        return self._r

    @property
    def green(self) -> int:
        """Green component (alias for g)."""
        return self._g

    @property
    def blue(self) -> int:
        """Blue component (alias for b)."""
        return self._b

    def blend(self, other: "RGBColor", ratio: float = 0.5) -> "RGBColor":
        """
        Blend this color with another color.

        Args:
            other: Color to blend with
            ratio: Blend ratio (0.0 = this color, 1.0 = other color, 0.5 = midpoint)

        Returns:
            New blended RGBColor
        """
        ratio = max(0.0, min(1.0, ratio))
        r = int(self._r + (other._r - self._r) * ratio)
        g = int(self._g + (other._g - self._g) * ratio)
        b = int(self._b + (other._b - self._b) * ratio)
        return RGBColor(r, g, b)

    def grayscale(self) -> "RGBColor":
        """
        Convert to grayscale using luminance-based conversion.

        Returns:
            Grayscale version of this color
        """
        # Use standard luminance weights
        gray = int(0.299 * self._r + 0.587 * self._g + 0.114 * self._b)
        return RGBColor(gray, gray, gray)

    def invert(self) -> "RGBColor":
        """
        Invert the color (same as complement).

        Returns:
            Inverted color
        """
        return self.complement()

    def saturate(self, amount: float = 0.2) -> "RGBColor":
        """
        Increase color saturation.

        Args:
            amount: How much to increase saturation (0.0 to 1.0)

        Returns:
            More saturated color
        """
        gray = int(0.299 * self._r + 0.587 * self._g + 0.114 * self._b)
        r = min(255, max(0, int(self._r + (self._r - gray) * amount)))
        g = min(255, max(0, int(self._g + (self._g - gray) * amount)))
        b = min(255, max(0, int(self._b + (self._b - gray) * amount)))
        return RGBColor(r, g, b)

    def desaturate(self, amount: float = 0.2) -> "RGBColor":
        """
        Decrease color saturation (move toward gray).

        Args:
            amount: How much to decrease saturation (0.0 to 1.0)

        Returns:
            Less saturated color
        """
        gray = int(0.299 * self._r + 0.587 * self._g + 0.114 * self._b)
        r = int(self._r + (gray - self._r) * amount)
        g = int(self._g + (gray - self._g) * amount)
        b = int(self._b + (gray - self._b) * amount)
        return RGBColor(r, g, b)

    def with_alpha(self, alpha: int) -> tuple[int, int, int, int]:
        """
        Return RGBA tuple with specified alpha.

        Args:
            alpha: Alpha value (0-255, where 0=transparent, 255=opaque)

        Returns:
            Tuple of (r, g, b, a)
        """
        return (self._r, self._g, self._b, alpha)

    def to_css(self) -> str:
        """
        Return CSS rgb() color string.

        Returns:
            CSS color string like 'rgb(255, 0, 0)'
        """
        return f"rgb({self._r}, {self._g}, {self._b})"

    def to_css_hex(self) -> str:
        """
        Return CSS hex color string with # prefix.

        Returns:
            CSS hex string like '#FF0000'
        """
        return f"#{self._r:02X}{self._g:02X}{self._b:02X}"

    def distance_to(self, other: "RGBColor") -> float:
        """
        Calculate Euclidean distance to another color in RGB space.

        Useful for comparing color similarity.

        Args:
            other: Color to compare with

        Returns:
            Distance value (0 = identical, ~441 = max difference)
        """
        return (
            (self._r - other._r) ** 2 +
            (self._g - other._g) ** 2 +
            (self._b - other._b) ** 2
        ) ** 0.5

    def is_similar_to(self, other: "RGBColor", threshold: float = 30.0) -> bool:
        """
        Check if this color is similar to another.

        Args:
            other: Color to compare with
            threshold: Maximum distance to consider similar (default 30)

        Returns:
            True if colors are within threshold distance
        """
        return self.distance_to(other) <= threshold

    @classmethod
    def random(cls) -> "RGBColor":
        """
        Generate a random color.

        Returns:
            Random RGBColor
        """
        import random
        return cls(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )

    # -------------------------------------------------------------------------
    # Common color constants
    # -------------------------------------------------------------------------

    @classmethod
    def white(cls) -> "RGBColor":
        """Return white color."""
        return cls(255, 255, 255)

    @classmethod
    def black(cls) -> "RGBColor":
        """Return black color."""
        return cls(0, 0, 0)

    @classmethod
    def red_color(cls) -> "RGBColor":
        """Return pure red color."""
        return cls(255, 0, 0)

    @classmethod
    def green_color(cls) -> "RGBColor":
        """Return pure green color."""
        return cls(0, 255, 0)

    @classmethod
    def blue_color(cls) -> "RGBColor":
        """Return pure blue color."""
        return cls(0, 0, 255)

    # -------------------------------------------------------------------------
    # HSL color space support
    # -------------------------------------------------------------------------

    def to_hsl(self) -> tuple[float, float, float]:
        """
        Convert to HSL (Hue, Saturation, Lightness).

        Returns:
            Tuple of (h, s, l) where:
            - h is hue in degrees (0-360)
            - s is saturation (0-1)
            - l is lightness (0-1)
        """
        r, g, b = self._r / 255.0, self._g / 255.0, self._b / 255.0
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        delta = max_c - min_c

        # Lightness
        l = (max_c + min_c) / 2.0

        if delta == 0:
            h = 0.0
            s = 0.0
        else:
            # Saturation
            s = delta / (1 - abs(2 * l - 1))

            # Hue
            if max_c == r:
                h = 60 * (((g - b) / delta) % 6)
            elif max_c == g:
                h = 60 * (((b - r) / delta) + 2)
            else:
                h = 60 * (((r - g) / delta) + 4)

        return (h, s, l)

    @classmethod
    def from_hsl(cls, h: float, s: float, l: float) -> "RGBColor":
        """
        Create an RGBColor from HSL values.

        Args:
            h: Hue in degrees (0-360)
            s: Saturation (0-1)
            l: Lightness (0-1)

        Returns:
            RGBColor instance
        """
        # Normalize hue to 0-360
        h = h % 360

        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l - c / 2

        if 0 <= h < 60:
            r_p, g_p, b_p = c, x, 0
        elif 60 <= h < 120:
            r_p, g_p, b_p = x, c, 0
        elif 120 <= h < 180:
            r_p, g_p, b_p = 0, c, x
        elif 180 <= h < 240:
            r_p, g_p, b_p = 0, x, c
        elif 240 <= h < 300:
            r_p, g_p, b_p = x, 0, c
        else:
            r_p, g_p, b_p = c, 0, x

        r = int((r_p + m) * 255)
        g = int((g_p + m) * 255)
        b = int((b_p + m) * 255)

        return cls(
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b))
        )

    def rotate_hue(self, degrees: float) -> "RGBColor":
        """
        Rotate the hue by the specified degrees.

        Args:
            degrees: Degrees to rotate hue (positive = clockwise)

        Returns:
            New RGBColor with rotated hue
        """
        h, s, l = self.to_hsl()
        new_h = (h + degrees) % 360
        return RGBColor.from_hsl(new_h, s, l)

    def adjust_saturation(self, amount: float) -> "RGBColor":
        """
        Adjust saturation by a relative amount.

        Args:
            amount: Amount to adjust (-1 to 1, negative = desaturate)

        Returns:
            New RGBColor with adjusted saturation
        """
        h, s, l = self.to_hsl()
        new_s = max(0, min(1, s + amount))
        return RGBColor.from_hsl(h, new_s, l)

    def adjust_lightness(self, amount: float) -> "RGBColor":
        """
        Adjust lightness by a relative amount.

        Args:
            amount: Amount to adjust (-1 to 1, negative = darker)

        Returns:
            New RGBColor with adjusted lightness
        """
        h, s, l = self.to_hsl()
        new_l = max(0, min(1, l + amount))
        return RGBColor.from_hsl(h, s, new_l)

    def set_saturation(self, saturation: float) -> "RGBColor":
        """
        Set saturation to a specific value.

        Args:
            saturation: New saturation value (0-1)

        Returns:
            New RGBColor with the specified saturation
        """
        h, _, l = self.to_hsl()
        return RGBColor.from_hsl(h, max(0, min(1, saturation)), l)

    def set_lightness(self, lightness: float) -> "RGBColor":
        """
        Set lightness to a specific value.

        Args:
            lightness: New lightness value (0-1)

        Returns:
            New RGBColor with the specified lightness
        """
        h, s, _ = self.to_hsl()
        return RGBColor.from_hsl(h, s, max(0, min(1, lightness)))

    @property
    def hue(self) -> float:
        """Get the hue component (0-360 degrees)."""
        h, _, _ = self.to_hsl()
        return h

    @property
    def saturation_hsl(self) -> float:
        """Get the saturation component from HSL (0-1)."""
        _, s, _ = self.to_hsl()
        return s

    @property
    def lightness(self) -> float:
        """Get the lightness component from HSL (0-1)."""
        _, _, l = self.to_hsl()
        return l

    # -------------------------------------------------------------------------
    # Aliases for common operations
    # -------------------------------------------------------------------------

    def lighten(self, amount: float = 0.2) -> "RGBColor":
        """Alias for lighter()."""
        return self.lighter(amount)

    def darken(self, amount: float = 0.2) -> "RGBColor":
        """Alias for darker()."""
        return self.darker(amount)

    def mix(self, other: "RGBColor", ratio: float = 0.5) -> "RGBColor":
        """Alias for blend()."""
        return self.blend(other, ratio)

    # -------------------------------------------------------------------------
    # Additional color constants
    # -------------------------------------------------------------------------

    @classmethod
    def yellow(cls) -> "RGBColor":
        """Return yellow color."""
        return cls(255, 255, 0)

    @classmethod
    def cyan(cls) -> "RGBColor":
        """Return cyan color."""
        return cls(0, 255, 255)

    @classmethod
    def magenta(cls) -> "RGBColor":
        """Return magenta color."""
        return cls(255, 0, 255)

    @classmethod
    def orange(cls) -> "RGBColor":
        """Return orange color."""
        return cls(255, 165, 0)

    @classmethod
    def gray(cls, level: int = 128) -> "RGBColor":
        """
        Return a gray color.

        Args:
            level: Gray level (0=black, 255=white, default 128)

        Returns:
            Gray RGBColor
        """
        level = max(0, min(255, level))
        return cls(level, level, level)

    @classmethod
    def transparent_white(cls) -> "RGBColor":
        """Return white (note: actual transparency is handled separately)."""
        return cls.white()

    # -------------------------------------------------------------------------
    # WCAG Accessibility methods
    # -------------------------------------------------------------------------

    def contrast_ratio(self, other: "RGBColor") -> float:
        """
        Calculate WCAG contrast ratio between two colors.

        The contrast ratio is used to determine if text is readable against
        a background color. WCAG guidelines recommend:
        - 4.5:1 for normal text (AA)
        - 3:1 for large text (AA)
        - 7:1 for normal text (AAA)
        - 4.5:1 for large text (AAA)

        Args:
            other: The other color to compare with

        Returns:
            Contrast ratio (1.0 to 21.0)
        """
        l1 = self.luminance
        l2 = other.luminance
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    def is_readable_on(
        self,
        background: "RGBColor",
        level: str = "AA",
        large_text: bool = False,
    ) -> bool:
        """
        Check if this color is readable as text on a background color.

        Uses WCAG accessibility guidelines for contrast ratios.

        Args:
            background: Background color
            level: WCAG level - 'AA' or 'AAA'
            large_text: Whether the text is large (18pt+ or 14pt+ bold)

        Returns:
            True if the color meets the contrast requirement
        """
        ratio = self.contrast_ratio(background)

        if level.upper() == "AAA":
            return ratio >= 4.5 if large_text else ratio >= 7.0
        else:  # AA
            return ratio >= 3.0 if large_text else ratio >= 4.5

    def best_text_color(self) -> "RGBColor":
        """
        Get the best text color (black or white) for this background.

        Returns black for light backgrounds, white for dark backgrounds.

        Returns:
            RGBColor - either black or white
        """
        return RGBColor.black() if self.is_light else RGBColor.white()

    # -------------------------------------------------------------------------
    # Color harmony methods
    # -------------------------------------------------------------------------

    def analogous(self, degrees: float = 30) -> tuple["RGBColor", "RGBColor"]:
        """
        Get analogous colors (adjacent on color wheel).

        Analogous colors create harmonious, comfortable designs.

        Args:
            degrees: Angle between colors (default 30°)

        Returns:
            Tuple of (color1, color2) - colors on either side
        """
        return (
            self.rotate_hue(-degrees),
            self.rotate_hue(degrees),
        )

    def triadic(self) -> tuple["RGBColor", "RGBColor"]:
        """
        Get triadic colors (evenly spaced 120° apart).

        Triadic colors create vibrant, balanced designs.

        Returns:
            Tuple of (color1, color2) - the other two colors in the triad
        """
        return (
            self.rotate_hue(120),
            self.rotate_hue(240),
        )

    def split_complementary(self, degrees: float = 30) -> tuple["RGBColor", "RGBColor"]:
        """
        Get split complementary colors.

        Like complementary but uses two colors adjacent to the complement,
        creating a softer contrast.

        Args:
            degrees: Angle from complement (default 30°)

        Returns:
            Tuple of (color1, color2) - colors adjacent to the complement
        """
        return (
            self.rotate_hue(180 - degrees),
            self.rotate_hue(180 + degrees),
        )

    def tetradic(self) -> tuple["RGBColor", "RGBColor", "RGBColor"]:
        """
        Get tetradic (rectangular) colors.

        Four colors forming a rectangle on the color wheel.

        Returns:
            Tuple of (color1, color2, color3) - the other three colors
        """
        return (
            self.rotate_hue(60),
            self.rotate_hue(180),
            self.rotate_hue(240),
        )

    def square(self) -> tuple["RGBColor", "RGBColor", "RGBColor"]:
        """
        Get square colors (evenly spaced 90° apart).

        Similar to tetradic but forms a square on the color wheel.

        Returns:
            Tuple of (color1, color2, color3) - the other three colors
        """
        return (
            self.rotate_hue(90),
            self.rotate_hue(180),
            self.rotate_hue(270),
        )

    def monochromatic(self, steps: int = 5) -> list["RGBColor"]:
        """
        Get monochromatic color variations.

        Creates a range of shades from dark to light using the same hue.

        Args:
            steps: Number of colors to generate (default 5)

        Returns:
            List of RGBColor variations from dark to light
        """
        h, s, _ = self.to_hsl()
        colors = []
        for i in range(steps):
            lightness = 0.1 + (0.8 * i / (steps - 1)) if steps > 1 else 0.5
            colors.append(RGBColor.from_hsl(h, s, lightness))
        return colors

    # -------------------------------------------------------------------------
    # HSV color space support
    # -------------------------------------------------------------------------

    def to_hsv(self) -> tuple[float, float, float]:
        """
        Convert to HSV (Hue, Saturation, Value).

        Returns:
            Tuple of (h, s, v) where:
            - h is hue in degrees (0-360)
            - s is saturation (0-1)
            - v is value/brightness (0-1)
        """
        r, g, b = self._r / 255.0, self._g / 255.0, self._b / 255.0
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        delta = max_c - min_c

        # Value
        v = max_c

        # Saturation
        if max_c == 0:
            s = 0.0
        else:
            s = delta / max_c

        # Hue
        if delta == 0:
            h = 0.0
        elif max_c == r:
            h = 60 * (((g - b) / delta) % 6)
        elif max_c == g:
            h = 60 * (((b - r) / delta) + 2)
        else:
            h = 60 * (((r - g) / delta) + 4)

        return (h, s, v)

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float) -> "RGBColor":
        """
        Create an RGBColor from HSV values.

        Args:
            h: Hue in degrees (0-360)
            s: Saturation (0-1)
            v: Value/brightness (0-1)

        Returns:
            RGBColor instance
        """
        h = h % 360
        s = max(0, min(1, s))
        v = max(0, min(1, v))

        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c

        if 0 <= h < 60:
            r_p, g_p, b_p = c, x, 0
        elif 60 <= h < 120:
            r_p, g_p, b_p = x, c, 0
        elif 120 <= h < 180:
            r_p, g_p, b_p = 0, c, x
        elif 180 <= h < 240:
            r_p, g_p, b_p = 0, x, c
        elif 240 <= h < 300:
            r_p, g_p, b_p = x, 0, c
        else:
            r_p, g_p, b_p = c, 0, x

        r = int((r_p + m) * 255)
        g = int((g_p + m) * 255)
        b = int((b_p + m) * 255)

        return cls(
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b))
        )

    @property
    def value(self) -> float:
        """Get the value/brightness component from HSV (0-1)."""
        _, _, v = self.to_hsv()
        return v

    @property
    def saturation_hsv(self) -> float:
        """Get the saturation component from HSV (0-1)."""
        _, s, _ = self.to_hsv()
        return s

    def set_value(self, value: float) -> "RGBColor":
        """
        Set the value/brightness to a specific level.

        Args:
            value: New value (0-1)

        Returns:
            New RGBColor with the specified value
        """
        h, s, _ = self.to_hsv()
        return RGBColor.from_hsv(h, s, max(0, min(1, value)))

    # -------------------------------------------------------------------------
    # Color palette generation
    # -------------------------------------------------------------------------

    def generate_palette(self, scheme: str = "analogous") -> list["RGBColor"]:
        """
        Generate a color palette based on a color scheme.

        Args:
            scheme: Palette scheme - 'analogous', 'triadic', 'complementary',
                   'split_complementary', 'tetradic', 'square', 'monochromatic'

        Returns:
            List of colors in the palette (including this color)
        """
        if scheme == "analogous":
            c1, c2 = self.analogous()
            return [c1, self, c2]
        elif scheme == "triadic":
            c1, c2 = self.triadic()
            return [self, c1, c2]
        elif scheme == "complementary":
            return [self, self.complement()]
        elif scheme == "split_complementary":
            c1, c2 = self.split_complementary()
            return [self, c1, c2]
        elif scheme == "tetradic":
            c1, c2, c3 = self.tetradic()
            return [self, c1, c2, c3]
        elif scheme == "square":
            c1, c2, c3 = self.square()
            return [self, c1, c2, c3]
        elif scheme == "monochromatic":
            return self.monochromatic()
        else:
            raise ValueError(f"Unknown scheme: {scheme}")


class ColorFormat:
    """
    Color format for text, fills, and lines.

    Provides access to color properties including RGB values and
    theme color references.
    """

    def __init__(
        self,
        rgb: Optional[RGBColor] = None,
        theme_color: Optional["MSO_THEME_COLOR"] = None,
        brightness: float = 0.0,
    ):
        """
        Create a ColorFormat.

        Args:
            rgb: RGB color value (if specified)
            theme_color: Theme color reference (if specified)
            brightness: Brightness adjustment (-1.0 to 1.0)
        """
        self._rgb = rgb
        self._theme_color = theme_color
        self._brightness = brightness

    @property
    def rgb(self) -> Optional[RGBColor]:
        """
        RGB color value.

        Returns the RGB color if this is an RGB-specified color,
        or None if this is a theme color.
        """
        return self._rgb

    @rgb.setter
    def rgb(self, value: RGBColor) -> None:
        """Set the RGB color value."""
        if not isinstance(value, RGBColor):
            raise TypeError(f"Expected RGBColor, got {type(value).__name__}")
        self._rgb = value
        self._theme_color = None  # Clear theme color when RGB is set

    @property
    def theme_color(self) -> Optional["MSO_THEME_COLOR"]:
        """Theme color index if this is a theme color."""
        return self._theme_color

    @theme_color.setter
    def theme_color(self, value: "MSO_THEME_COLOR") -> None:
        """Set the theme color."""
        self._theme_color = value
        self._rgb = None  # Clear RGB when theme color is set

    @property
    def brightness(self) -> float:
        """
        Brightness adjustment for this color.

        A value between -1.0 (darker) and 1.0 (lighter).
        """
        return self._brightness

    @brightness.setter
    def brightness(self, value: float) -> None:
        """Set brightness adjustment."""
        if not (-1.0 <= value <= 1.0):
            raise ValueError(f"brightness must be between -1.0 and 1.0, got {value}")
        self._brightness = value

    @property
    def type(self) -> Optional["MSO_COLOR_TYPE"]:
        """
        Color type (MSO_COLOR_TYPE).

        Returns the type of color specification (RGB, SCHEME, etc.)
        or None if no color is set.
        """
        from ..enum.dml import MSO_COLOR_TYPE

        if self._rgb is not None:
            return MSO_COLOR_TYPE.RGB
        if self._theme_color is not None:
            return MSO_COLOR_TYPE.SCHEME
        return None

    def __repr__(self) -> str:
        if self._rgb:
            return f"<ColorFormat rgb={self._rgb}>"
        if self._theme_color:
            return f"<ColorFormat theme_color={self._theme_color}>"
        return "<ColorFormat (none)>"
