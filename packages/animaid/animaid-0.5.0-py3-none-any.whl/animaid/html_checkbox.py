"""HTMLCheckbox - A checkbox widget with two-way binding."""

from __future__ import annotations

import html
import threading
from collections.abc import Callable
from typing import Self


class HTMLCheckbox:
    """A checkbox widget with two-way boolean binding.

    The checked property is automatically synced from the browser when
    the user toggles the checkbox.

    Examples:
        >>> checkbox = HTMLCheckbox("Accept terms", checked=False)
        >>> checkbox = HTMLCheckbox("Enable feature").on_change(handle_change)

        # With Animate - two-way binding
        >>> with Animate() as anim:
        ...     terms = HTMLCheckbox("I accept the terms")
        ...     anim.add(terms)
        ...     # Later, read the current value:
        ...     print(terms.checked)  # True/False synced from browser
    """

    def __init__(
        self,
        label: str,
        checked: bool = False,
    ) -> None:
        """Create a checkbox widget.

        Args:
            label: The text label displayed next to the checkbox.
            checked: The initial checked state.
        """
        self._label = label
        self._value = checked  # _value holds the checked state
        self._on_change: Callable[[bool], None] | None = None
        self._styles: dict[str, str] = {}
        self._css_classes: list[str] = ["anim-checkbox-container"]
        self._anim_id: str | None = None
        self._lock = threading.Lock()

    @property
    def checked(self) -> bool:
        """Get the current checked state (thread-safe).

        The value is automatically synced from the browser when the user
        toggles the checkbox.

        Returns:
            True if checked, False otherwise.
        """
        with self._lock:
            return self._value

    @checked.setter
    def checked(self, value: bool) -> None:
        """Set the checked state (thread-safe).

        Note: Setting the value programmatically does not automatically
        update the browser display. Use anim.refresh() to update.

        Args:
            value: The new checked state.
        """
        with self._lock:
            self._value = value

    @property
    def value(self) -> bool:
        """Alias for checked property (for HTMLInput compatibility)."""
        return self.checked

    @value.setter
    def value(self, new_value: bool) -> None:
        """Alias for checked setter (for HTMLInput compatibility)."""
        self.checked = new_value

    @property
    def label(self) -> str:
        """Get the checkbox label."""
        return self._label

    def on_change(self, callback: Callable[[bool], None]) -> "HTMLCheckbox":
        """Register a callback for state changes.

        The callback is called when the user toggles the checkbox.

        Args:
            callback: A function that takes the new checked state as argument.

        Returns:
            Self for method chaining.

        Examples:
            >>> def handle_change(checked):
            ...     print(f"Checkbox is now: {'checked' if checked else 'unchecked'}")
            >>> checkbox = HTMLCheckbox("Enable").on_change(handle_change)
        """
        self._on_change = callback
        return self

    def render(self) -> str:
        """Return HTML representation of this checkbox.

        Returns:
            A string containing valid HTML for the checkbox.
        """
        attrs = self._build_attributes()
        escaped_label = html.escape(self._label)
        checked_attr = " checked" if self._value else ""

        # Add data-anim-id for event handling
        anim_id_attr = ""
        if self._anim_id:
            anim_id_attr = f' data-anim-id="{html.escape(self._anim_id)}"'

        checkbox_html = (
            f'<input type="checkbox" class="anim-checkbox"{anim_id_attr}{checked_attr}>'
        )
        label_html = f"<span>{escaped_label}</span>"

        if attrs:
            return f"<label {attrs}>{checkbox_html}{label_html}</label>"
        return f"<label>{checkbox_html}{label_html}</label>"

    def __html__(self) -> str:
        """Jinja2 auto-escaping protocol."""
        return self.render()

    def styled(self, **styles: str) -> "HTMLCheckbox":
        """Return a copy with additional inline styles.

        Args:
            **styles: CSS property-value pairs.

        Returns:
            A new instance with the combined styles.
        """
        new_checkbox = HTMLCheckbox(self._label, self._value)
        new_checkbox._on_change = self._on_change
        new_checkbox._anim_id = self._anim_id
        new_checkbox._styles = dict(self._styles)
        new_checkbox._css_classes = list(self._css_classes)

        # Add new styles, converting underscores to hyphens
        for key, value in styles.items():
            css_key = key.replace("_", "-")
            new_checkbox._styles[css_key] = value

        return new_checkbox

    def add_class(self, *class_names: str) -> "HTMLCheckbox":
        """Return a copy with additional CSS classes.

        Args:
            *class_names: CSS class names to add.

        Returns:
            A new instance with the additional classes.
        """
        new_checkbox = HTMLCheckbox(self._label, self._value)
        new_checkbox._on_change = self._on_change
        new_checkbox._anim_id = self._anim_id
        new_checkbox._styles = dict(self._styles)
        new_checkbox._css_classes = list(self._css_classes) + list(class_names)
        return new_checkbox

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
    def large(self) -> "HTMLCheckbox":
        """Return a copy with larger text and checkbox.

        Returns:
            A new instance with large styling.
        """
        return self.styled(font_size="18px")

    def small(self) -> "HTMLCheckbox":
        """Return a copy with smaller text and checkbox.

        Returns:
            A new instance with small styling.
        """
        return self.styled(font_size="12px")
