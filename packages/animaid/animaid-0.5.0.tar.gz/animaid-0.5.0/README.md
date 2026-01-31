# AnimAID

[![Documentation Status](https://readthedocs.org/projects/animaid/badge/?version=latest)](https://animaid.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/animaid.svg)](https://badge.fury.io/py/animaid)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Turn Python data structures into beautiful HTML with zero effort.**

📖 **[Documentation](https://animaid.readthedocs.io)** | 🚀 **[PyPI](https://pypi.org/project/animaid/)** | 💻 **[GitHub](https://github.com/jdrumgoole/animaid)**

AnimAID is a Python library that wraps common data types (strings, numbers, lists, dicts, tuples, sets) and gives them the ability to render themselves as styled HTML. It's perfect for:

- Building interactive tutorials and documentation
- Creating quick web dashboards
- Generating HTML reports
- Learning web development concepts through Python

## Quick Start

### Installation

```bash
pip install animaid
```

### Your First Styled String

```python
from animaid import HTMLString

# Create a styled string
greeting = HTMLString("Hello, World!")
greeting = greeting.bold().color("blue")

# Get the HTML
print(greeting.render())
# Output: <span style="font-weight: bold; color: blue">Hello, World!</span>
```

That's it! You just created styled HTML from Python.

## What Can AnimAID Do?

AnimAID provides HTML-renderable versions of Python's built-in types:

| Python Type | AnimAID Type | What It Does |
|-------------|--------------|--------------|
| `str` | `HTMLString` | Style text with colors, fonts, backgrounds |
| `int` | `HTMLInt` | Format numbers with commas, currency, percentages |
| `float` | `HTMLFloat` | Control decimal places, add units |
| `list` | `HTMLList` | Render as styled lists, cards, or pills |
| `dict` | `HTMLDict` | Display as tables, cards, or definition lists |
| `tuple` | `HTMLTuple` | Show tuples with labels or custom separators |
| `set` | `HTMLSet` | Render unique items as tags or pills |
| - | `Animate` | Interactive browser display with real-time updates |

## Learning by Example

### Styling Text (HTMLString)

```python
from animaid import HTMLString

# Basic styling
text = HTMLString("Important!")
text = text.bold().italic().color("red")
print(text.render())
```

You can chain multiple styles together:

```python
# Chaining styles
badge = (HTMLString("NEW")
    .uppercase()
    .bold()
    .padding("4px 8px")
    .background("#4CAF50")
    .color("white")
    .border_radius("4px"))
```

![HTMLString Example](https://raw.githubusercontent.com/jdrumgoole/animaid/main/docs/images/tutorial-string-highlight.png)

### Formatting Numbers (HTMLInt)

```python
from animaid import HTMLInt

# Display as currency
price = HTMLInt(1234567)
price = price.currency("$").bold().color("#2e7d32")
print(price.render())
# Output: $1,234,567
```

Common number formats:
- `.comma()` - Add thousand separators: 1,234,567
- `.currency("$")` - Format as money: $1,234,567
- `.percent()` - Show as percentage: 85%
- `.ordinal()` - Show as ordinal: 1st, 2nd, 3rd

![HTMLInt Example](https://raw.githubusercontent.com/jdrumgoole/animaid/main/docs/images/tutorial-int-currency.png)

### Creating Lists (HTMLList)

```python
from animaid import HTMLList

# Simple list
fruits = HTMLList(["Apple", "Banana", "Cherry"])
print(fruits.render())

# Styled as horizontal cards
cards = (HTMLList(["Apple", "Banana", "Cherry", "Date"])
    .horizontal()
    .plain()
    .gap("16px")
    .item_padding("16px")
    .item_border("1px solid #e0e0e0")
    .item_border_radius("8px"))
```

![HTMLList Example](https://raw.githubusercontent.com/jdrumgoole/animaid/main/docs/images/tutorial-list-cards.png)

### Displaying Dictionaries (HTMLDict)

```python
from animaid import HTMLDict

# User profile as a card
profile = HTMLDict({
    "name": "Alice",
    "role": "Developer",
    "status": "Active"
})

styled = (profile
    .as_divs()
    .key_bold()
    .padding("16px")
    .border("1px solid #e0e0e0")
    .border_radius("8px")
    .background("white"))
```

![HTMLDict Example](https://raw.githubusercontent.com/jdrumgoole/animaid/main/docs/images/tutorial-dict-card.png)

### Working with Sets (HTMLSet)

Sets automatically remove duplicates:

```python
from animaid import HTMLSet

# Duplicates are removed automatically
tags = HTMLSet(["Python", "Web", "Python", "HTML"])
# Only contains: Python, Web, HTML

# Style as pills
pills = tags.pills()  # Rounded pill-style items
```

![HTMLSet Example](https://raw.githubusercontent.com/jdrumgoole/animaid/main/docs/images/tutorial-set-pills.png)

## The Fluent API

AnimAID uses a "fluent" API where methods modify the object in-place and return `self`, letting you chain calls:

```python
# Method chaining
result = (HTMLString("Hello")
    .bold()
    .italic()
    .color("blue")
    .padding("10px")
    .border("1px solid black"))
```

Methods modify the original object and return it, so you can also do:

```python
# Step by step
text = HTMLString("Hello")
text.bold()
text.color("blue")
```

Both approaches work the same way!

## Quick Style Presets

Many types come with presets for common use cases:

```python
# String presets
HTMLString("Note").highlight()   # Yellow background
HTMLString("def foo").code()     # Monospace, dark background
HTMLString("3").badge()          # Circular badge style

# Number presets
HTMLInt(99).currency("$")        # $99 in green
HTMLInt(42).badge()              # Circular number badge

# List presets
HTMLList(items).pills()          # Rounded pill items
HTMLList(items).cards()          # Card-style items
HTMLList(items).tags()           # Tag-style items

# Set presets
HTMLSet(items).pills()           # Pill-style unique items
HTMLSet(items).tags()            # Tag-style items
```

## CSS Helper Types

AnimAID includes helper types for CSS values:

```python
from animaid import Color, Size, Spacing, Border

# Colors
Color.red                    # Named color
Color.hex("#4CAF50")         # Hex color
Color.rgb(100, 150, 200)     # RGB color

# Sizes
Size.px(16)                  # 16px
Size.em(1.5)                 # 1.5em
Size.sm()                    # Small preset (8px)
Size.md()                    # Medium preset (16px)

# Spacing
Spacing.px(10)               # 10px all around
Spacing.symmetric(10, 20)    # 10px top/bottom, 20px left/right

# Borders
Border.solid(1, Color.gray)  # 1px solid gray
Border.dashed(2, Color.red)  # 2px dashed red
```

## Interactive Display (Animate)

The `Animate` class provides a Tkinter-like interactive environment using HTML. The browser becomes the display surface where you can add, update, and remove AnimAID objects in real-time.

```python
from animaid import Animate, HTMLString, HTMLList

# Create and start (opens browser automatically)
anim = Animate()
anim.run()

# Add items - browser updates in real-time
anim.add(HTMLString("Hello World!").bold().xl())
anim.add(HTMLList(["Apple", "Banana", "Cherry"]).pills())

# Update existing items
item_id = anim.add(HTMLString("Loading..."))
anim.update(item_id, HTMLString("Done!").success())

# Clean up
anim.stop()
```

Or use the context manager:

```python
with Animate() as anim:
    anim.add(HTMLString("Temporary display").bold())
    input("Press Enter to exit...")
# Server stops automatically
```

**Note:** Animate requires the tutorial dependencies: `pip install animaid[tutorial]`

### Reactive Updates

All HTML objects automatically notify Animate when their styles change. The browser updates in real-time:

```python
from animaid import Animate, HTMLList, HTMLDict, HTMLString, HTMLInt

anim = Animate()
anim.run()

# Styling changes trigger automatic updates for ALL types
message = HTMLString("Hello")
anim.add(message)
message.bold().red()   # Browser updates automatically

number = HTMLInt(42)
anim.add(number)
number.badge()         # Browser updates automatically

# Mutable types also update on data changes
scores = HTMLList([10, 20, 30]).pills()
anim.add(scores)
scores.append(40)      # Browser shows [10, 20, 30, 40]
scores[0] = 100        # Browser shows [100, 20, 30, 40]

data = HTMLDict({"score": 0})
anim.add(data)
data["score"] = 500    # Browser updates automatically
```

**Note:** Immutable types (`HTMLString`, `HTMLInt`, `HTMLFloat`, `HTMLTuple`) can have their styles changed in-place, but to change their underlying data/content, use `anim.update(item_id, new_value)`.

## Demo Programs

AnimAID includes demo programs that showcase its interactive capabilities:

```bash
# List available demos
animaid-demo --list

# Run a specific demo
animaid-demo countdown_timer
```

Available demos:

**Core Demos:**
- **[countdown_timer](https://github.com/jdrumgoole/animaid/blob/main/demos/countdown_timer.py)** - Real-time countdown with color transitions
- **[live_list](https://github.com/jdrumgoole/animaid/blob/main/demos/live_list.py)** - Reactive shopping cart with `.append()` and `.pop()`
- **[score_tracker](https://github.com/jdrumgoole/animaid/blob/main/demos/score_tracker.py)** - Game score tracking with automatic dict updates
- **[sorting_visualizer](https://github.com/jdrumgoole/animaid/blob/main/demos/sorting_visualizer.py)** - Bubble sort algorithm visualization
- **[dashboard](https://github.com/jdrumgoole/animaid/blob/main/demos/dashboard.py)** - Multi-type dashboard with all HTML types
- **[typewriter](https://github.com/jdrumgoole/animaid/blob/main/demos/typewriter.py)** - Typewriter effect with progressive styling
- **[todo_app](https://github.com/jdrumgoole/animaid/blob/main/demos/todo_app.py)** - Interactive todo list with CRUD operations
- **[data_pipeline](https://github.com/jdrumgoole/animaid/blob/main/demos/data_pipeline.py)** - ETL pipeline progress tracking

**Input Widget Demos:**
- **[input_button](https://github.com/jdrumgoole/animaid/blob/main/demos/input_button.py)** - Button styles, sizes, and click events
- **[input_text](https://github.com/jdrumgoole/animaid/blob/main/demos/input_text.py)** - Text input with live feedback
- **[input_checkbox](https://github.com/jdrumgoole/animaid/blob/main/demos/input_checkbox.py)** - Checkbox toggles and preferences
- **[input_select](https://github.com/jdrumgoole/animaid/blob/main/demos/input_select.py)** - Select dropdowns with dynamic updates
- **[input_slider](https://github.com/jdrumgoole/animaid/blob/main/demos/input_slider.py)** - RGB color mixer with sliders

Each demo opens a browser and shows real-time updates as the Python code runs.

### Demo Previews

**Sorting Visualizer** - Watch bubble sort in action ([source](https://github.com/jdrumgoole/animaid/blob/main/demos/sorting_visualizer.py)):

![Sorting Visualizer](https://raw.githubusercontent.com/jdrumgoole/animaid/main/docs/images/demos/sorting_visualizer.gif)

**Dashboard** - Multiple HTML types updating together ([source](https://github.com/jdrumgoole/animaid/blob/main/demos/dashboard.py)):

![Dashboard](https://raw.githubusercontent.com/jdrumgoole/animaid/main/docs/images/demos/dashboard.gif)

## Documentation

Full documentation is available at **[animaid.readthedocs.io](https://animaid.readthedocs.io)**

The documentation includes:
- Complete API reference
- CSS helper types guide
- Animate class usage
- Demo program gallery

## Interactive Tutorial

AnimAID includes a web-based tutorial that lets you experiment with all the features:

```bash
# Install with tutorial dependencies
pip install animaid[tutorial]

# Start the tutorial (opens browser automatically)
animaid-tutorial
```

The tutorial provides:
- **Python Objects Tab**: Explore all HTML types (HTMLString, HTMLList, HTMLDict, etc.) with a unified interface
- **Input Widgets Tab**: Interactive input widgets (buttons, text inputs, checkboxes, sliders, selects)
- **Dict of Lists / List of Dicts**: Nested data structure visualizations
- Live preview of styled output
- Generated Python code you can copy
- Generated HTML output
- Quick preset buttons for common styles

![AnimAID Tutorial](https://raw.githubusercontent.com/jdrumgoole/animaid/main/docs/images/tutorial-app-main.png)

### Input Widgets

The tutorial also demonstrates interactive input widgets that work with the `Animate` class:

![Input Widgets](https://raw.githubusercontent.com/jdrumgoole/animaid/main/docs/images/tutorial-app-inputs.png)

## Type Aliases

For convenience, AnimAID provides short aliases:

```python
from animaid import String, Int, Float, List, Dict, Tuple, Set

# These are equivalent:
HTMLString("hello")  # Full name
String("hello")      # Short alias
```

## Common Styling Methods

Most AnimAID types share these styling methods:

| Method | Example | Description |
|--------|---------|-------------|
| `.bold()` | `.bold()` | Make text bold |
| `.italic()` | `.italic()` | Make text italic |
| `.color(c)` | `.color("red")` | Set text color |
| `.background(c)` | `.background("#f0f0f0")` | Set background color |
| `.padding(p)` | `.padding("10px")` | Add padding |
| `.margin(m)` | `.margin("5px")` | Add margin |
| `.border(b)` | `.border("1px solid black")` | Add border |
| `.border_radius(r)` | `.border_radius("5px")` | Round corners |
| `.font_size(s)` | `.font_size("18px")` | Set font size |

## Development

```bash
# Clone the repository
git clone https://github.com/jdrumgoole/animaid.git
cd animaid

# Install with development dependencies
pip install -e ".[dev,docs,tutorial]"

# Run tests
pytest

# Run linting
ruff check src tests

# Build documentation
sphinx-build -b html docs docs/_build/html

# Start the tutorial server
animaid-tutorial
```

For development with [uv](https://docs.astral.sh/uv/):
```bash
uv pip install -e ".[dev,docs,tutorial]"
uv run pytest
uv run invoke check  # Run all checks
```

## Requirements

- Python 3.10+
- No external dependencies for the core library

## License

**Code:** Apache License 2.0 - see [LICENSE](LICENSE) for details.

**Documentation:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run the tests (`invoke test`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request
