"""HTMLSlider - A range slider widget with two-way binding."""

from __future__ import annotations

import html
import threading
from collections.abc import Callable
from typing import Self


class HTMLSlider:
    """A range slider widget with two-way numeric binding.

    The value property is automatically synced from the browser when
    the user moves the slider.

    Examples:
        >>> slider = HTMLSlider(min=0, max=100, value=50)
        >>> slider = HTMLSlider(min=0, max=1, step=0.1).on_change(handle_change)

        # With Animate - two-way binding
        >>> with Animate() as anim:
        ...     volume = HTMLSlider(min=0, max=100, value=75)
        ...     anim.add(volume)
        ...     # Later, read the current value:
        ...     print(volume.value)  # Numeric value synced from browser
    """

    def __init__(
        self,
        min: float = 0,
        max: float = 100,
        value: float | None = None,
        step: float = 1,
    ) -> None:
        """Create a slider widget.

        Args:
            min: The minimum value of the slider.
            max: The maximum value of the slider.
            value: The initial value (defaults to min).
            step: The step increment between values.
        """
        self._min = min
        self._max = max
        self._step = step
        self._value = value if value is not None else min
        self._on_change: Callable[[float], None] | None = None
        self._styles: dict[str, str] = {}
        self._css_classes: list[str] = ["anim-slider"]
        self._anim_id: str | None = None
        self._lock = threading.Lock()

    @property
    def value(self) -> float:
        """Get the current value (thread-safe).

        The value is automatically synced from the browser when the user
        moves the slider.

        Returns:
            The current numeric value of the slider.
        """
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value: float) -> None:
        """Set the value (thread-safe).

        Note: Setting the value programmatically does not automatically
        update the browser display. Use anim.refresh() to update.

        Args:
            new_value: The new value to set.
        """
        with self._lock:
            self._value = new_value

    @property
    def min(self) -> float:
        """Get the minimum value."""
        return self._min

    @property
    def max(self) -> float:
        """Get the maximum value."""
        return self._max

    @property
    def step(self) -> float:
        """Get the step increment."""
        return self._step

    def on_change(self, callback: Callable[[float], None]) -> "HTMLSlider":
        """Register a callback for value changes.

        The callback is called when the user moves the slider.

        Args:
            callback: A function that takes the new value as argument.

        Returns:
            Self for method chaining.

        Examples:
            >>> def handle_change(value):
            ...     print(f"Slider value: {value}")
            >>> slider = HTMLSlider(0, 100).on_change(handle_change)
        """
        self._on_change = callback
        return self

    def render(self) -> str:
        """Return HTML representation of this slider.

        Returns:
            A string containing valid HTML for the slider.
        """
        attrs = self._build_attributes()

        # Add data-anim-id for event handling
        anim_id_attr = ""
        if self._anim_id:
            anim_id_attr = f' data-anim-id="{html.escape(self._anim_id)}"'

        range_attrs = (
            f'min="{self._min}" max="{self._max}" '
            f'step="{self._step}" value="{self._value}"'
        )

        if attrs:
            return f'<input type="range" {attrs}{anim_id_attr} {range_attrs}>'
        return f'<input type="range"{anim_id_attr} {range_attrs}>'

    def __html__(self) -> str:
        """Jinja2 auto-escaping protocol."""
        return self.render()

    def styled(self, **styles: str) -> "HTMLSlider":
        """Return a copy with additional inline styles.

        Args:
            **styles: CSS property-value pairs.

        Returns:
            A new instance with the combined styles.
        """
        new_slider = HTMLSlider(self._min, self._max, self._value, self._step)
        new_slider._on_change = self._on_change
        new_slider._anim_id = self._anim_id
        new_slider._styles = dict(self._styles)
        new_slider._css_classes = list(self._css_classes)

        # Add new styles, converting underscores to hyphens
        for key, value in styles.items():
            css_key = key.replace("_", "-")
            new_slider._styles[css_key] = value

        return new_slider

    def add_class(self, *class_names: str) -> "HTMLSlider":
        """Return a copy with additional CSS classes.

        Args:
            *class_names: CSS class names to add.

        Returns:
            A new instance with the additional classes.
        """
        new_slider = HTMLSlider(self._min, self._max, self._value, self._step)
        new_slider._on_change = self._on_change
        new_slider._anim_id = self._anim_id
        new_slider._styles = dict(self._styles)
        new_slider._css_classes = list(self._css_classes) + list(class_names)
        return new_slider

    def _build_style_string(self) -> str:
        """Convert internal styles dict to CSS style attribute value."""
        if not self._styles:
            return ""
        return "; ".join(f"{k}: {v}" for k, v in self._styles.items())

    def _build_class_string(self) -> str:
        """Convert internal classes list to CSS class attribute value."""
        if not self._css_classes:
            return ""
        return " ".join(self._css_classes)

    def _build_attributes(self) -> str:
        """Build the complete HTML attributes string."""
        parts = []

        class_str = self._build_class_string()
        if class_str:
            parts.append(f'class="{class_str}"')

        style_str = self._build_style_string()
        if style_str:
            parts.append(f'style="{style_str}"')

        return " ".join(parts)

    # Styled presets
    def wide(self) -> "HTMLSlider":
        """Return a copy that expands to full width.

        Returns:
            A new instance with full width styling.
        """
        return self.styled(width="100%", max_width="none")

    def thin(self) -> "HTMLSlider":
        """Return a copy with a thinner slider track.

        Returns:
            A new instance with thin styling.
        """
        return self.styled(height="4px")

    def thick(self) -> "HTMLSlider":
        """Return a copy with a thicker slider track.

        Returns:
            A new instance with thick styling.
        """
        return self.styled(height="10px")
