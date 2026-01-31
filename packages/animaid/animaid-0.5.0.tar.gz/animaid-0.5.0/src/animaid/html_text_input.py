"""HTMLTextInput - A text input widget with two-way binding."""

from __future__ import annotations

import html
import threading
from collections.abc import Callable
from typing import Self


class HTMLTextInput:
    """A text input widget with two-way value binding.

    The value property is automatically synced from the browser when
    the user types in the input field.

    Examples:
        >>> text = HTMLTextInput(placeholder="Enter your name...")
        >>> text = HTMLTextInput(value="Default").on_change(handle_change)

        # With Animate - two-way binding
        >>> with Animate() as anim:
        ...     name_input = HTMLTextInput(placeholder="Name")
        ...     anim.add(name_input)
        ...     # Later, read the current value:
        ...     print(name_input.value)  # Value synced from browser
    """

    def __init__(
        self,
        value: str = "",
        placeholder: str = "",
    ) -> None:
        """Create a text input widget.

        Args:
            value: The initial value of the input.
            placeholder: Placeholder text shown when input is empty.
        """
        self._value = value
        self._placeholder = placeholder
        self._on_change: Callable[[str], None] | None = None
        self._on_submit: Callable[[str], None] | None = None
        self._styles: dict[str, str] = {}
        self._css_classes: list[str] = ["anim-text-input"]
        self._anim_id: str | None = None
        self._lock = threading.Lock()

    @property
    def value(self) -> str:
        """Get the current value (thread-safe).

        The value is automatically synced from the browser when the user
        types in the input field.

        Returns:
            The current text value of the input.
        """
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        """Set the value (thread-safe).

        Note: Setting the value programmatically does not automatically
        update the browser display. Use anim.refresh() to update.

        Args:
            new_value: The new value to set.
        """
        with self._lock:
            self._value = new_value

    @property
    def placeholder(self) -> str:
        """Get the placeholder text."""
        return self._placeholder

    def on_change(self, callback: Callable[[str], None]) -> "HTMLTextInput":
        """Register a callback for value changes.

        The callback is called on each keystroke when the user types.

        Args:
            callback: A function that takes the new value as argument.

        Returns:
            Self for method chaining.

        Examples:
            >>> def handle_change(value):
            ...     print(f"Input changed to: {value}")
            >>> text = HTMLTextInput().on_change(handle_change)
        """
        self._on_change = callback
        return self

    def on_submit(self, callback: Callable[[str], None]) -> "HTMLTextInput":
        """Register a callback for submit (Enter key).

        The callback is called when the user presses Enter in the input.

        Args:
            callback: A function that takes the submitted value as argument.

        Returns:
            Self for method chaining.

        Examples:
            >>> def handle_submit(value):
            ...     print(f"Submitted: {value}")
            >>> text = HTMLTextInput().on_submit(handle_submit)
        """
        self._on_submit = callback
        return self

    def render(self) -> str:
        """Return HTML representation of this text input.

        Returns:
            A string containing valid HTML for the input.
        """
        attrs = self._build_attributes()
        escaped_value = html.escape(self._value)
        escaped_placeholder = html.escape(self._placeholder)

        # Add data-anim-id for event handling
        anim_id_attr = ""
        if self._anim_id:
            anim_id_attr = f' data-anim-id="{html.escape(self._anim_id)}"'

        placeholder_attr = ""
        if self._placeholder:
            placeholder_attr = f' placeholder="{escaped_placeholder}"'

        if attrs:
            return (
                f'<input type="text" {attrs}{anim_id_attr}'
                f' value="{escaped_value}"{placeholder_attr}>'
            )
        return (
            f'<input type="text"{anim_id_attr}'
            f' value="{escaped_value}"{placeholder_attr}>'
        )

    def __html__(self) -> str:
        """Jinja2 auto-escaping protocol."""
        return self.render()

    def styled(self, **styles: str) -> "HTMLTextInput":
        """Return a copy with additional inline styles.

        Args:
            **styles: CSS property-value pairs.

        Returns:
            A new instance with the combined styles.
        """
        new_input = HTMLTextInput(self._value, self._placeholder)
        new_input._on_change = self._on_change
        new_input._on_submit = self._on_submit
        new_input._anim_id = self._anim_id
        new_input._styles = dict(self._styles)
        new_input._css_classes = list(self._css_classes)

        # Add new styles, converting underscores to hyphens
        for key, value in styles.items():
            css_key = key.replace("_", "-")
            new_input._styles[css_key] = value

        return new_input

    def add_class(self, *class_names: str) -> "HTMLTextInput":
        """Return a copy with additional CSS classes.

        Args:
            *class_names: CSS class names to add.

        Returns:
            A new instance with the additional classes.
        """
        new_input = HTMLTextInput(self._value, self._placeholder)
        new_input._on_change = self._on_change
        new_input._on_submit = self._on_submit
        new_input._anim_id = self._anim_id
        new_input._styles = dict(self._styles)
        new_input._css_classes = list(self._css_classes) + list(class_names)
        return new_input

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
    def wide(self) -> "HTMLTextInput":
        """Return a copy that expands to full width.

        Returns:
            A new instance with full width styling.
        """
        return self.styled(width="100%", max_width="none")

    def large(self) -> "HTMLTextInput":
        """Return a copy with larger text and padding.

        Returns:
            A new instance with large styling.
        """
        return self.styled(font_size="18px", padding="14px 18px")

    def small(self) -> "HTMLTextInput":
        """Return a copy with smaller text and padding.

        Returns:
            A new instance with small styling.
        """
        return self.styled(font_size="12px", padding="6px 10px")
