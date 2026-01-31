"""CSS value types for type-safe styling.

This module provides classes and enums for representing CSS values with
validation, IDE autocomplete support, and type safety.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar

# =============================================================================
# Base Protocol
# =============================================================================


class CSSValue(ABC):
    """Base class for all CSS value types.

    All CSS value classes must implement to_css() which returns the CSS string
    representation. They also support str() conversion for backward compatibility.
    """

    @abstractmethod
    def to_css(self) -> str:
        """Return the CSS string representation of this value."""
        ...

    def __str__(self) -> str:
        """Convert to string (same as to_css for compatibility)."""
        return self.to_css()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_css()!r})"


# =============================================================================
# Size Class
# =============================================================================


class Size(CSSValue):
    """Represents a CSS size/length value with units.

    Examples:
        >>> Size.px(10)
        Size('10px')
        >>> Size.em(1.5)
        Size('1.5em')
        >>> Size.percent(50)
        Size('50%')
        >>> Size.auto()
        Size('auto')
    """

    # Valid CSS length units
    VALID_UNITS: ClassVar[set[str]] = {
        "px",
        "em",
        "rem",
        "%",
        "vh",
        "vw",
        "vmin",
        "vmax",
        "pt",
        "pc",
        "in",
        "cm",
        "mm",
        "ex",
        "ch",
        "fr",
    }

    # Special keyword values
    KEYWORDS: ClassVar[set[str]] = {
        "auto",
        "inherit",
        "initial",
        "unset",
        "none",
        "min-content",
        "max-content",
        "fit-content",
    }

    def __init__(self, value: float | str, unit: str = "") -> None:
        """Create a Size from a value and optional unit.

        Args:
            value: Numeric value or keyword string (e.g., "auto")
            unit: CSS unit (e.g., "px", "em", "%"). Not needed for keywords.

        Raises:
            ValueError: If the value or unit is invalid.
        """
        if isinstance(value, str):
            # Parse string like "10px" or keyword like "auto"
            self._value, self._unit = self._parse_string(value)
        else:
            if unit and unit not in self.VALID_UNITS:
                valid = ", ".join(sorted(self.VALID_UNITS))
                raise ValueError(f"Invalid unit '{unit}'. Valid units: {valid}")
            self._value = value
            self._unit = unit

    def _parse_string(self, s: str) -> tuple[float | None, str]:
        """Parse a CSS size string into value and unit."""
        s = s.strip().lower()

        # Check for keywords
        if s in self.KEYWORDS:
            return None, s

        # Try to parse numeric value with unit
        match = re.match(r"^(-?\d*\.?\d+)\s*([a-z%]+)?$", s)
        if match:
            value = float(match.group(1))
            unit = match.group(2) or "px"  # Default to px if no unit
            if unit not in self.VALID_UNITS:
                raise ValueError(f"Invalid unit '{unit}' in '{s}'")
            return value, unit

        raise ValueError(f"Cannot parse size value: '{s}'")

    def to_css(self) -> str:
        """Return the CSS string representation."""
        if self._value is None:
            return self._unit  # Keyword like "auto"
        if self._unit:
            # Format without trailing zeros
            if self._value == int(self._value):
                return f"{int(self._value)}{self._unit}"
            return f"{self._value}{self._unit}"
        return str(int(self._value) if self._value == int(self._value) else self._value)

    @property
    def value(self) -> float | None:
        """The numeric value, or None for keywords."""
        return self._value

    @property
    def unit(self) -> str:
        """The unit string."""
        return self._unit

    @property
    def is_keyword(self) -> bool:
        """True if this is a keyword value like 'auto'."""
        return self._value is None

    # Factory methods for common units
    @classmethod
    def px(cls, value: float) -> Size:
        """Create a pixel size."""
        return cls(value, "px")

    @classmethod
    def em(cls, value: float) -> Size:
        """Create an em size."""
        return cls(value, "em")

    @classmethod
    def rem(cls, value: float) -> Size:
        """Create a rem size."""
        return cls(value, "rem")

    @classmethod
    def percent(cls, value: float) -> Size:
        """Create a percentage size."""
        return cls(value, "%")

    @classmethod
    def vh(cls, value: float) -> Size:
        """Create a viewport height size."""
        return cls(value, "vh")

    @classmethod
    def vw(cls, value: float) -> Size:
        """Create a viewport width size."""
        return cls(value, "vw")

    @classmethod
    def fr(cls, value: float) -> Size:
        """Create a fractional unit size (for CSS grid)."""
        return cls(value, "fr")

    @classmethod
    def auto(cls) -> Size:
        """Create an 'auto' size."""
        return cls("auto")

    @classmethod
    def none(cls) -> Size:
        """Create a 'none' size."""
        return cls("none")

    @classmethod
    def inherit(cls) -> Size:
        """Create an 'inherit' size."""
        return cls("inherit")

    # -------------------------------------------------------------------------
    # Named Size Presets (beginner-friendly)
    # -------------------------------------------------------------------------

    @classmethod
    def zero(cls) -> Size:
        """Create a zero size (0px)."""
        return cls(0, "px")

    @classmethod
    def xs(cls) -> Size:
        """Create an extra-small size (4px)."""
        return cls(4, "px")

    @classmethod
    def sm(cls) -> Size:
        """Create a small size (8px)."""
        return cls(8, "px")

    @classmethod
    def md(cls) -> Size:
        """Create a medium size (16px)."""
        return cls(16, "px")

    @classmethod
    def lg(cls) -> Size:
        """Create a large size (24px)."""
        return cls(24, "px")

    @classmethod
    def xl(cls) -> Size:
        """Create an extra-large size (32px)."""
        return cls(32, "px")

    @classmethod
    def xxl(cls) -> Size:
        """Create a 2x extra-large size (48px)."""
        return cls(48, "px")

    @classmethod
    def full(cls) -> Size:
        """Create a full width/height (100%)."""
        return cls(100, "%")

    @classmethod
    def half(cls) -> Size:
        """Create a half width/height (50%)."""
        return cls(50, "%")

    @classmethod
    def third(cls) -> Size:
        """Create a third width/height (33.333%)."""
        return cls(33.333, "%")

    @classmethod
    def quarter(cls) -> Size:
        """Create a quarter width/height (25%)."""
        return cls(25, "%")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Size):
            return self._value == other._value and self._unit == other._unit
        if isinstance(other, str):
            return self.to_css() == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._value, self._unit))


# =============================================================================
# Color Class
# =============================================================================


class Color(CSSValue):
    """Represents a CSS color value.

    Supports named colors, hex codes, rgb(), rgba(), hsl(), and hsla().

    Examples:
        >>> Color.red
        Color('red')
        >>> Color.hex("#2563eb")
        Color('#2563eb')
        >>> Color.rgb(255, 128, 0)
        Color('rgb(255, 128, 0)')
        >>> Color.rgba(255, 128, 0, 0.5)
        Color('rgba(255, 128, 0, 0.5)')
    """

    # Named CSS colors (subset of most common)
    NAMED_COLORS: ClassVar[set[str]] = {
        "black",
        "white",
        "red",
        "green",
        "blue",
        "yellow",
        "cyan",
        "magenta",
        "gray",
        "grey",
        "orange",
        "pink",
        "purple",
        "brown",
        "navy",
        "teal",
        "olive",
        "maroon",
        "aqua",
        "fuchsia",
        "lime",
        "silver",
        "transparent",
        "currentcolor",
        "inherit",
        "initial",
        "unset",
    }

    # Class-level color instances (set after class definition)
    transparent: ClassVar[Color]
    black: ClassVar[Color]
    white: ClassVar[Color]
    red: ClassVar[Color]
    green: ClassVar[Color]
    blue: ClassVar[Color]
    yellow: ClassVar[Color]
    cyan: ClassVar[Color]
    magenta: ClassVar[Color]
    gray: ClassVar[Color]
    grey: ClassVar[Color]
    orange: ClassVar[Color]
    pink: ClassVar[Color]
    purple: ClassVar[Color]
    brown: ClassVar[Color]
    navy: ClassVar[Color]
    teal: ClassVar[Color]
    olive: ClassVar[Color]
    maroon: ClassVar[Color]
    aqua: ClassVar[Color]
    lime: ClassVar[Color]
    silver: ClassVar[Color]
    # Semantic colors
    success: ClassVar[Color]
    warning: ClassVar[Color]
    error: ClassVar[Color]
    info: ClassVar[Color]
    muted: ClassVar[Color]
    light_gray: ClassVar[Color]
    dark_gray: ClassVar[Color]

    def __init__(self, value: str) -> None:
        """Create a Color from a CSS color string.

        Args:
            value: A valid CSS color (name, hex, rgb, rgba, hsl, hsla)

        Raises:
            ValueError: If the color format is invalid.
        """
        self._value = self._validate(value.strip())

    def _validate(self, value: str) -> str:
        """Validate and normalize a color value."""
        lower = value.lower()

        # Named colors
        if lower in self.NAMED_COLORS:
            return lower

        # Hex colors
        if value.startswith("#"):
            hex_part = value[1:]
            valid_hex = all(c in "0123456789abcdefABCDEF" for c in hex_part)
            if len(hex_part) in (3, 4, 6, 8) and valid_hex:
                return value
            raise ValueError(f"Invalid hex color: '{value}'")

        # rgb/rgba/hsl/hsla functions
        func_match = re.match(r"^(rgba?|hsla?)\s*\((.+)\)$", lower)
        if func_match:
            return value  # Accept as-is, browser will validate

        raise ValueError(
            f"Invalid color: '{value}'. Use named color, hex (#rgb or #rrggbb), "
            "or function (rgb, rgba, hsl, hsla)"
        )

    def to_css(self) -> str:
        """Return the CSS string representation."""
        return self._value

    # Factory methods
    @classmethod
    def hex(cls, code: str) -> Color:
        """Create a color from a hex code.

        Args:
            code: Hex code with or without '#' prefix
        """
        if not code.startswith("#"):
            code = f"#{code}"
        return cls(code)

    @classmethod
    def rgb(cls, r: int, g: int, b: int) -> Color:
        """Create an RGB color.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        for name, val in [("r", r), ("g", g), ("b", b)]:
            if not 0 <= val <= 255:
                raise ValueError(f"{name} must be 0-255, got {val}")
        return cls(f"rgb({r}, {g}, {b})")

    @classmethod
    def rgba(cls, r: int, g: int, b: int, a: float) -> Color:
        """Create an RGBA color with alpha.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
            a: Alpha component (0.0-1.0)
        """
        for name, val in [("r", r), ("g", g), ("b", b)]:
            if not 0 <= val <= 255:
                raise ValueError(f"{name} must be 0-255, got {val}")
        if not 0.0 <= a <= 1.0:
            raise ValueError(f"alpha must be 0.0-1.0, got {a}")
        return cls(f"rgba({r}, {g}, {b}, {a})")

    @classmethod
    def hsl(cls, h: int, s: int, lightness: int) -> Color:
        """Create an HSL color.

        Args:
            h: Hue (0-360)
            s: Saturation (0-100)
            lightness: Lightness (0-100)
        """
        if not 0 <= h <= 360:
            raise ValueError(f"hue must be 0-360, got {h}")
        if not 0 <= s <= 100:
            raise ValueError(f"saturation must be 0-100, got {s}")
        if not 0 <= lightness <= 100:
            raise ValueError(f"lightness must be 0-100, got {lightness}")
        return cls(f"hsl({h}, {s}%, {lightness}%)")

    @classmethod
    def hsla(cls, h: int, s: int, lightness: int, a: float) -> Color:
        """Create an HSLA color with alpha.

        Args:
            h: Hue (0-360)
            s: Saturation (0-100)
            lightness: Lightness (0-100)
            a: Alpha (0.0-1.0)
        """
        if not 0 <= h <= 360:
            raise ValueError(f"hue must be 0-360, got {h}")
        if not 0 <= s <= 100:
            raise ValueError(f"saturation must be 0-100, got {s}")
        if not 0 <= lightness <= 100:
            raise ValueError(f"lightness must be 0-100, got {lightness}")
        if not 0.0 <= a <= 1.0:
            raise ValueError(f"alpha must be 0.0-1.0, got {a}")
        return cls(f"hsla({h}, {s}%, {lightness}%, {a})")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Color):
            return self._value.lower() == other._value.lower()
        if isinstance(other, str):
            return self._value.lower() == other.lower()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value.lower())


# Named color class attributes (for Color.red, Color.blue, etc.)
# These are defined after the class to avoid forward reference issues
Color.transparent = Color("transparent")
Color.black = Color("black")
Color.white = Color("white")
Color.red = Color("red")
Color.green = Color("green")
Color.blue = Color("blue")
Color.yellow = Color("yellow")
Color.cyan = Color("cyan")
Color.magenta = Color("magenta")
Color.gray = Color("gray")
Color.grey = Color("grey")
Color.orange = Color("orange")
Color.pink = Color("pink")
Color.purple = Color("purple")
Color.brown = Color("brown")
Color.navy = Color("navy")
Color.teal = Color("teal")
Color.olive = Color("olive")
Color.maroon = Color("maroon")
Color.aqua = Color("aqua")
Color.lime = Color("lime")
Color.silver = Color("silver")


# Semantic colors for UI (beginner-friendly)
Color.success = Color("#22c55e")
Color.warning = Color("#f59e0b")
Color.error = Color("#ef4444")
Color.info = Color("#3b82f6")
Color.muted = Color("#6b7280")
Color.light_gray = Color("#f5f5f5")
Color.dark_gray = Color("#374151")


# =============================================================================
# Text Enums
# =============================================================================


class FontWeight(Enum):
    """CSS font-weight values."""

    NORMAL = "normal"
    BOLD = "bold"
    LIGHTER = "lighter"
    BOLDER = "bolder"
    W100 = "100"
    W200 = "200"
    W300 = "300"
    W400 = "400"
    W500 = "500"
    W600 = "600"
    W700 = "700"
    W800 = "800"
    W900 = "900"

    def to_css(self) -> str:
        """Return the CSS value."""
        return self.value

    def __str__(self) -> str:
        return self.value


class FontStyle(Enum):
    """CSS font-style values."""

    NORMAL = "normal"
    ITALIC = "italic"
    OBLIQUE = "oblique"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class TextTransform(Enum):
    """CSS text-transform values."""

    NONE = "none"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    CAPITALIZE = "capitalize"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class TextDecoration(Enum):
    """CSS text-decoration values."""

    NONE = "none"
    UNDERLINE = "underline"
    OVERLINE = "overline"
    LINE_THROUGH = "line-through"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class TextAlign(Enum):
    """CSS text-align values."""

    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    JUSTIFY = "justify"
    START = "start"
    END = "end"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


# =============================================================================
# Layout Enums
# =============================================================================


class Display(Enum):
    """CSS display values."""

    BLOCK = "block"
    INLINE = "inline"
    INLINE_BLOCK = "inline-block"
    FLEX = "flex"
    INLINE_FLEX = "inline-flex"
    GRID = "grid"
    INLINE_GRID = "inline-grid"
    NONE = "none"
    CONTENTS = "contents"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class FlexDirection(Enum):
    """CSS flex-direction values."""

    ROW = "row"
    ROW_REVERSE = "row-reverse"
    COLUMN = "column"
    COLUMN_REVERSE = "column-reverse"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class FlexWrap(Enum):
    """CSS flex-wrap values."""

    NOWRAP = "nowrap"
    WRAP = "wrap"
    WRAP_REVERSE = "wrap-reverse"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class AlignItems(Enum):
    """CSS align-items values."""

    START = "start"
    END = "end"
    CENTER = "center"
    STRETCH = "stretch"
    BASELINE = "baseline"
    FLEX_START = "flex-start"
    FLEX_END = "flex-end"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class JustifyContent(Enum):
    """CSS justify-content values."""

    START = "start"
    END = "end"
    CENTER = "center"
    STRETCH = "stretch"
    SPACE_BETWEEN = "space-between"
    SPACE_AROUND = "space-around"
    SPACE_EVENLY = "space-evenly"
    FLEX_START = "flex-start"
    FLEX_END = "flex-end"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class Position(Enum):
    """CSS position values."""

    STATIC = "static"
    RELATIVE = "relative"
    ABSOLUTE = "absolute"
    FIXED = "fixed"
    STICKY = "sticky"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class Overflow(Enum):
    """CSS overflow values."""

    VISIBLE = "visible"
    HIDDEN = "hidden"
    SCROLL = "scroll"
    AUTO = "auto"
    CLIP = "clip"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class JustifyItems(Enum):
    """CSS justify-items values for grid containers."""

    START = "start"
    END = "end"
    CENTER = "center"
    STRETCH = "stretch"
    BASELINE = "baseline"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class AlignContent(Enum):
    """CSS align-content values for multi-line flex/grid containers."""

    START = "start"
    END = "end"
    CENTER = "center"
    STRETCH = "stretch"
    SPACE_BETWEEN = "space-between"
    SPACE_AROUND = "space-around"
    SPACE_EVENLY = "space-evenly"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class GridAutoFlow(Enum):
    """CSS grid-auto-flow values."""

    ROW = "row"
    COLUMN = "column"
    ROW_DENSE = "row dense"
    COLUMN_DENSE = "column dense"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class PlaceItems(Enum):
    """CSS place-items shorthand (align + justify)."""

    START = "start"
    END = "end"
    CENTER = "center"
    STRETCH = "stretch"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class ShadowSize(Enum):
    """Predefined box-shadow sizes for cards/containers."""

    NONE = "none"
    SM = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    DEFAULT = "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)"
    MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)"
    LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)"
    XL = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class RadiusSize(Enum):
    """Predefined border-radius sizes."""

    NONE = "0"
    SM = "2px"
    DEFAULT = "4px"
    MD = "6px"
    LG = "8px"
    XL = "12px"
    XXL = "16px"
    FULL = "9999px"  # Fully rounded (pill shape)

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class DividerStyle(Enum):
    """Divider line styles (maps to border-style)."""

    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    DOUBLE = "double"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


# =============================================================================
# Border Enum and Class
# =============================================================================


class BorderStyle(Enum):
    """CSS border-style values."""

    NONE = "none"
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    DOUBLE = "double"
    GROOVE = "groove"
    RIDGE = "ridge"
    INSET = "inset"
    OUTSET = "outset"
    HIDDEN = "hidden"

    def to_css(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class Border(CSSValue):
    """Represents a CSS border value (width + style + color).

    Examples:
        >>> Border(Size.px(1), BorderStyle.SOLID, Color.black)
        Border('1px solid black')
        >>> Border.solid(2, "red")
        Border('2px solid red')
        >>> Border().width(Size.px(2)).dashed().color(Color.blue)
        Border('2px dashed blue')
    """

    def __init__(
        self,
        width: Size | str | int | float = "1px",
        style: BorderStyle | str = BorderStyle.SOLID,
        color: Color | str = "black",
    ) -> None:
        """Create a Border.

        Args:
            width: Border width (Size, string, or number in pixels)
            style: Border style (BorderStyle enum or string)
            color: Border color (Color or string)
        """
        # Normalize width
        if isinstance(width, (int, float)):
            self._width = Size.px(width)
        elif isinstance(width, str):
            self._width = Size(width)
        else:
            self._width = width

        # Normalize style
        if isinstance(style, str):
            try:
                self._style = BorderStyle(style)
            except ValueError:
                raise ValueError(f"Invalid border style: '{style}'")
        else:
            self._style = style

        # Normalize color
        if isinstance(color, str):
            self._color = Color(color)
        else:
            self._color = color

    def to_css(self) -> str:
        """Return the CSS border shorthand."""
        return f"{self._width.to_css()} {self._style.to_css()} {self._color.to_css()}"

    @property
    def width_value(self) -> Size:
        """The border width."""
        return self._width

    @property
    def style_value(self) -> BorderStyle:
        """The border style."""
        return self._style

    @property
    def color_value(self) -> Color:
        """The border color."""
        return self._color

    # Fluent builder methods (return new instances)
    def width(self, w: Size | str | int | float) -> Border:
        """Return a new Border with the specified width."""
        return Border(w, self._style, self._color)

    def style(self, s: BorderStyle | str) -> Border:
        """Return a new Border with the specified style."""
        return Border(self._width, s, self._color)

    def color(self, c: Color | str) -> Border:
        """Return a new Border with the specified color."""
        return Border(self._width, self._style, c)

    # Instance methods for changing style (fluent API)
    def as_solid(self) -> Border:
        """Return a new Border with solid style."""
        return self.style(BorderStyle.SOLID)

    def as_dashed(self) -> Border:
        """Return a new Border with dashed style."""
        return self.style(BorderStyle.DASHED)

    def as_dotted(self) -> Border:
        """Return a new Border with dotted style."""
        return self.style(BorderStyle.DOTTED)

    def as_double(self) -> Border:
        """Return a new Border with double style."""
        return self.style(BorderStyle.DOUBLE)

    def as_none(self) -> Border:
        """Return a new Border with no style."""
        return self.style(BorderStyle.NONE)

    # -------------------------------------------------------------------------
    # Class Methods - Clean Factory Methods (beginner-friendly)
    # -------------------------------------------------------------------------

    @classmethod
    def solid(
        cls, width: Size | str | int | float = 1, color: Color | str = "black"
    ) -> Border:
        """Create a solid border.

        Args:
            width: Border width (default 1px)
            color: Border color (default black)

        Examples:
            >>> Border.solid()
            Border('1px solid black')
            >>> Border.solid(2, "red")
            Border('2px solid red')
        """
        return cls(width, BorderStyle.SOLID, color)

    @classmethod
    def dashed(
        cls, width: Size | str | int | float = 1, color: Color | str = "black"
    ) -> Border:
        """Create a dashed border.

        Args:
            width: Border width (default 1px)
            color: Border color (default black)

        Examples:
            >>> Border.dashed()
            Border('1px dashed black')
            >>> Border.dashed(2, "blue")
            Border('2px dashed blue')
        """
        return cls(width, BorderStyle.DASHED, color)

    @classmethod
    def dotted(
        cls, width: Size | str | int | float = 1, color: Color | str = "black"
    ) -> Border:
        """Create a dotted border.

        Args:
            width: Border width (default 1px)
            color: Border color (default black)

        Examples:
            >>> Border.dotted()
            Border('1px dotted black')
        """
        return cls(width, BorderStyle.DOTTED, color)

    @classmethod
    def double(
        cls, width: Size | str | int | float = 3, color: Color | str = "black"
    ) -> Border:
        """Create a double border.

        Args:
            width: Border width (default 3px - minimum for double to show)
            color: Border color (default black)

        Examples:
            >>> Border.double()
            Border('3px double black')
        """
        return cls(width, BorderStyle.DOUBLE, color)

    @classmethod
    def none(cls) -> Border:
        """Create a border with no visible style.

        Examples:
            >>> Border.none()
            Border('1px none black')
        """
        return cls(0, BorderStyle.NONE, "transparent")

    # -------------------------------------------------------------------------
    # Width Presets (beginner-friendly)
    # -------------------------------------------------------------------------

    @classmethod
    def thin(
        cls, color: Color | str = "black", style: BorderStyle | str = BorderStyle.SOLID
    ) -> Border:
        """Create a thin border (1px).

        Args:
            color: Border color (default black)
            style: Border style (default solid)

        Examples:
            >>> Border.thin()
            Border('1px solid black')
            >>> Border.thin("red")
            Border('1px solid red')
        """
        return cls(1, style, color)

    @classmethod
    def medium(
        cls, color: Color | str = "black", style: BorderStyle | str = BorderStyle.SOLID
    ) -> Border:
        """Create a medium border (2px).

        Args:
            color: Border color (default black)
            style: Border style (default solid)

        Examples:
            >>> Border.medium()
            Border('2px solid black')
        """
        return cls(2, style, color)

    @classmethod
    def thick(
        cls, color: Color | str = "black", style: BorderStyle | str = BorderStyle.SOLID
    ) -> Border:
        """Create a thick border (4px).

        Args:
            color: Border color (default black)
            style: Border style (default solid)

        Examples:
            >>> Border.thick()
            Border('4px solid black')
            >>> Border.thick("navy")
            Border('4px solid navy')
        """
        return cls(4, style, color)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Border):
            return (
                self._width == other._width
                and self._style == other._style
                and self._color == other._color
            )
        if isinstance(other, str):
            return self.to_css() == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._width, self._style, self._color))


# =============================================================================
# Spacing Class
# =============================================================================


class Spacing(CSSValue):
    """Represents CSS spacing (padding/margin) with 1-4 values.

    Examples:
        >>> Spacing.all(Size.px(10))
        Spacing('10px')
        >>> Spacing.symmetric(Size.px(10), Size.px(20))
        Spacing('10px 20px')
        >>> Spacing.edges(Size.px(1), Size.px(2), Size.px(3), Size.px(4))
        Spacing('1px 2px 3px 4px')
    """

    def __init__(
        self,
        top: Size | str | int | float,
        right: Size | str | int | float | None = None,
        bottom: Size | str | int | float | None = None,
        left: Size | str | int | float | None = None,
    ) -> None:
        """Create a Spacing value.

        Args:
            top: Top value (or all sides if others are None)
            right: Right value (or horizontal if bottom/left are None)
            bottom: Bottom value
            left: Left value
        """
        self._top = self._normalize(top)
        self._right = self._normalize(right) if right is not None else None
        self._bottom = self._normalize(bottom) if bottom is not None else None
        self._left = self._normalize(left) if left is not None else None

    def _normalize(self, value: Size | str | int | float) -> Size:
        """Normalize a value to Size."""
        if isinstance(value, Size):
            return value
        if isinstance(value, (int, float)):
            return Size.px(value)
        return Size(value)

    def to_css(self) -> str:
        """Return the CSS spacing value."""
        if self._right is None:
            # Single value: all sides
            return self._top.to_css()
        if self._bottom is None:
            # Two values: vertical horizontal
            return f"{self._top.to_css()} {self._right.to_css()}"
        if self._left is None:
            # Three values: top horizontal bottom
            top = self._top.to_css()
            right = self._right.to_css()
            bottom = self._bottom.to_css()
            return f"{top} {right} {bottom}"
        # Four values: top right bottom left
        top = self._top.to_css()
        right = self._right.to_css()
        bottom = self._bottom.to_css()
        left = self._left.to_css()
        return f"{top} {right} {bottom} {left}"

    @property
    def top(self) -> Size:
        """Top spacing."""
        return self._top

    @property
    def right(self) -> Size:
        """Right spacing (same as top if not specified)."""
        return self._right if self._right is not None else self._top

    @property
    def bottom(self) -> Size:
        """Bottom spacing (same as top if not specified)."""
        return self._bottom if self._bottom is not None else self._top

    @property
    def left(self) -> Size:
        """Left spacing (same as right if not specified)."""
        if self._left is not None:
            return self._left
        return self._right if self._right is not None else self._top

    # Factory methods
    @classmethod
    def all(cls, value: Size | str | int | float) -> Spacing:
        """Create uniform spacing on all sides."""
        return cls(value)

    @classmethod
    def symmetric(
        cls,
        vertical: Size | str | int | float,
        horizontal: Size | str | int | float,
    ) -> Spacing:
        """Create symmetric spacing (vertical and horizontal)."""
        return cls(vertical, horizontal)

    @classmethod
    def edges(
        cls,
        top: Size | str | int | float,
        right: Size | str | int | float,
        bottom: Size | str | int | float,
        left: Size | str | int | float,
    ) -> Spacing:
        """Create spacing with explicit values for all four edges."""
        return cls(top, right, bottom, left)

    @classmethod
    def horizontal(cls, value: Size | str | int | float) -> Spacing:
        """Create horizontal-only spacing (left and right)."""
        return cls(0, value)

    @classmethod
    def vertical(cls, value: Size | str | int | float) -> Spacing:
        """Create vertical-only spacing (top and bottom)."""
        return cls(value, 0)

    # -------------------------------------------------------------------------
    # Named Presets (beginner-friendly)
    # -------------------------------------------------------------------------

    @classmethod
    def zero(cls) -> Spacing:
        """Create zero spacing."""
        return cls(0)

    @classmethod
    def xs(cls) -> Spacing:
        """Create extra-small spacing (4px)."""
        return cls(4)

    @classmethod
    def sm(cls) -> Spacing:
        """Create small spacing (8px)."""
        return cls(8)

    @classmethod
    def md(cls) -> Spacing:
        """Create medium spacing (16px)."""
        return cls(16)

    @classmethod
    def lg(cls) -> Spacing:
        """Create large spacing (24px)."""
        return cls(24)

    @classmethod
    def xl(cls) -> Spacing:
        """Create extra-large spacing (32px)."""
        return cls(32)

    # -------------------------------------------------------------------------
    # Common UI Patterns (beginner-friendly)
    # -------------------------------------------------------------------------

    @classmethod
    def button(cls) -> Spacing:
        """Create typical button padding (8px 16px)."""
        return cls(8, 16)

    @classmethod
    def card(cls) -> Spacing:
        """Create typical card padding (16px)."""
        return cls(16)

    @classmethod
    def input(cls) -> Spacing:
        """Create typical input field padding (8px 12px)."""
        return cls(8, 12)

    @classmethod
    def section(cls) -> Spacing:
        """Create typical section margins (24px top/bottom, 0 left/right)."""
        return cls(24, 0)

    @classmethod
    def compact(cls) -> Spacing:
        """Create compact spacing (4px 8px)."""
        return cls(4, 8)

    @classmethod
    def relaxed(cls) -> Spacing:
        """Create relaxed/generous spacing (16px 24px)."""
        return cls(16, 24)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Spacing):
            return self.to_css() == other.to_css()
        if isinstance(other, str):
            return self.to_css() == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.to_css())


# =============================================================================
# Type aliases for convenience
# =============================================================================

# Union types for method signatures that accept both new types and strings
SizeValue = Size | str | int | float
ColorValue = Color | str
BorderValue = Border | str
SpacingValue = Spacing | str | int | float
