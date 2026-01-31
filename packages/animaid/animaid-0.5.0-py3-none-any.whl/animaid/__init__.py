"""
Animaid - Create beautiful HTML from Python data structures.

Quick Start:
    >>> from animaid import HTMLString, HTMLList, HTMLDict

    # Styled text - chain methods for easy styling
    >>> HTMLString("Hello").bold().red().render()
    '<span style="font-weight: bold; color: red">Hello</span>'

    # Styled lists - use presets for common patterns
    >>> HTMLList(["Apple", "Banana", "Cherry"]).pills().render()

    # Styled dicts - display key-value data beautifully
    >>> HTMLDict({"name": "Alice", "age": 30}).card().render()

Beginner Tips:
    - Use method shortcuts: .bold(), .red(), .large() instead of .styled(...)
    - Use presets: .cards(), .pills(), .badge(), .highlight() for common styles
    - Chain methods: HTMLString("Hi").bold().red().large()
    - Methods modify in-place and return self for chaining
"""

from animaid.css_types import (
    # Layout enums
    AlignContent,
    AlignItems,
    # Border
    Border,
    BorderStyle,
    # Type aliases
    BorderValue,
    # Primitives
    Color,
    ColorValue,
    # Base class
    CSSValue,
    Display,
    # Container/decoration enums
    DividerStyle,
    FlexDirection,
    FlexWrap,
    # Text enums
    FontStyle,
    FontWeight,
    GridAutoFlow,
    JustifyContent,
    JustifyItems,
    Overflow,
    PlaceItems,
    Position,
    RadiusSize,
    ShadowSize,
    Size,
    SizeValue,
    # Spacing
    Spacing,
    SpacingValue,
    TextAlign,
    TextDecoration,
    TextTransform,
)
from animaid.containers import (
    HTMLCard,
    HTMLColumn,
    HTMLContainer,
    HTMLDivider,
    HTMLRow,
    HTMLSpacer,
)
from animaid.html_dict import HTMLDict
from animaid.html_float import HTMLFloat
from animaid.html_int import HTMLInt
from animaid.html_list import HTMLList
from animaid.html_object import HTMLObject
from animaid.html_set import HTMLSet
from animaid.html_string import HTMLString
from animaid.html_tuple import HTMLTuple

# Conditional import for Animate and input widgets (requires tutorial dependencies)
try:
    from animaid.animate import Animate
    from animaid.html_button import HTMLButton
    from animaid.html_checkbox import HTMLCheckbox
    from animaid.html_select import HTMLSelect
    from animaid.html_slider import HTMLSlider
    from animaid.html_text_input import HTMLTextInput
    from animaid.input_event import InputEvent
except ImportError:
    Animate = None  # type: ignore[misc, assignment]
    HTMLButton = None  # type: ignore[misc, assignment]
    HTMLCheckbox = None  # type: ignore[misc, assignment]
    HTMLSelect = None  # type: ignore[misc, assignment]
    HTMLSlider = None  # type: ignore[misc, assignment]
    HTMLTextInput = None  # type: ignore[misc, assignment]
    InputEvent = None  # type: ignore[misc, assignment]

__version__ = "0.5.0"

# Beginner-friendly aliases (shorter names)
String = HTMLString
List = HTMLList
Dict = HTMLDict
Int = HTMLInt
Float = HTMLFloat
Tuple = HTMLTuple
Set = HTMLSet

# Short h_ prefixed aliases
h_string = HTMLString
h_list = HTMLList
h_dict = HTMLDict
h_int = HTMLInt
h_float = HTMLFloat
h_tuple = HTMLTuple
h_set = HTMLSet

# Input widget aliases (for when tutorial dependencies are available)
Button = HTMLButton
TextInput = HTMLTextInput
Checkbox = HTMLCheckbox
Slider = HTMLSlider
Select = HTMLSelect

# Container aliases
Container = HTMLContainer
Row = HTMLRow
Column = HTMLColumn
Card = HTMLCard
Divider = HTMLDivider
Spacer = HTMLSpacer

__all__ = [
    "__version__",
    # Animation
    "Animate",
    # Input widgets (full names)
    "HTMLButton",
    "HTMLCheckbox",
    "HTMLSelect",
    "HTMLSlider",
    "HTMLTextInput",
    "InputEvent",
    # Input widgets (short aliases)
    "Button",
    "Checkbox",
    "Select",
    "Slider",
    "TextInput",
    # Container widgets (full names)
    "HTMLCard",
    "HTMLColumn",
    "HTMLContainer",
    "HTMLDivider",
    "HTMLRow",
    "HTMLSpacer",
    # Container widgets (short aliases)
    "Card",
    "Column",
    "Container",
    "Divider",
    "Row",
    "Spacer",
    # HTML types (full names)
    "HTMLDict",
    "HTMLFloat",
    "HTMLInt",
    "HTMLList",
    "HTMLObject",
    "HTMLSet",
    "HTMLString",
    "HTMLTuple",
    # HTML types (short aliases)
    "String",
    "List",
    "Dict",
    "Int",
    "Float",
    "Tuple",
    "Set",
    # HTML types (h_ prefixed aliases)
    "h_string",
    "h_list",
    "h_dict",
    "h_int",
    "h_float",
    "h_tuple",
    "h_set",
    # CSS value types
    "CSSValue",
    "Color",
    "Size",
    # Text enums
    "FontStyle",
    "FontWeight",
    "TextAlign",
    "TextDecoration",
    "TextTransform",
    # Layout enums
    "AlignContent",
    "AlignItems",
    "Display",
    "FlexDirection",
    "FlexWrap",
    "GridAutoFlow",
    "JustifyContent",
    "JustifyItems",
    "Overflow",
    "PlaceItems",
    "Position",
    # Container/decoration enums
    "DividerStyle",
    "RadiusSize",
    "ShadowSize",
    # Border
    "Border",
    "BorderStyle",
    # Spacing
    "Spacing",
    # Type aliases
    "BorderValue",
    "ColorValue",
    "SizeValue",
    "SpacingValue",
]
