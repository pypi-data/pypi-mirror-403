"""Base class for HTML input widgets with two-way binding."""

from __future__ import annotations

import threading
from abc import abstractmethod
from collections.abc import Callable
from typing import Any, Self

from animaid.html_object import HTMLObject


class HTMLInput(HTMLObject):
    """Abstract base class for input widgets with two-way binding.

    Input widgets support:
    - Two-way value binding (value syncs from browser)
    - Event callbacks (on_change, on_click, etc.)
    - Thread-safe value access

    Subclasses must implement:
    - render() to generate the HTML
    - styled() to apply inline styles
    - add_class() to add CSS classes
    """

    _value: Any
    _on_change: Callable[[Any], None] | None
    _lock: threading.Lock
    _anim_id: str | None

    def __init__(self, initial_value: Any = None) -> None:
        """Initialize the input widget.

        Args:
            initial_value: The initial value of the input.
        """
        self._value = initial_value
        self._on_change = None
        self._lock = threading.Lock()
        self._anim_id = None
        self._styles: dict[str, str] = {}
        self._css_classes: list[str] = []

    @property
    def value(self) -> Any:
        """Get the current value (thread-safe).

        The value is automatically synced from the browser when the user
        interacts with the input widget.

        Returns:
            The current value of the input.
        """
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set the value (thread-safe).

        Note: Setting the value programmatically does not automatically
        update the browser display. Use anim.refresh() to update.

        Args:
            new_value: The new value to set.
        """
        with self._lock:
            self._value = new_value

    def on_change(self, callback: Callable[[Any], None]) -> Self:
        """Register a callback for value changes.

        The callback is called whenever the input value changes in the browser.
        The callback receives the new value as its argument.

        Args:
            callback: A function that takes the new value as argument.

        Returns:
            Self for method chaining.

        Examples:
            >>> def handle_change(value):
            ...     print(f"Value changed to: {value}")
            >>> text_input = HTMLTextInput().on_change(handle_change)
        """
        self._on_change = callback
        return self

    @abstractmethod
    def render(self) -> str:
        """Return HTML representation of this input widget.

        Returns:
            A string containing valid HTML for the input.
        """
        ...

    @abstractmethod
    def styled(self, **styles: str) -> Self:
        """Return a copy with additional inline styles.

        Args:
            **styles: CSS property-value pairs.

        Returns:
            A new instance with the combined styles.
        """
        ...

    @abstractmethod
    def add_class(self, *class_names: str) -> Self:
        """Return a copy with additional CSS classes.

        Args:
            *class_names: CSS class names to add.

        Returns:
            A new instance with the additional classes.
        """
        ...

    def _copy_state_to(self, other: HTMLInput) -> None:
        """Copy internal state to another instance.

        Used by subclasses when creating modified copies.

        Args:
            other: The instance to copy state to.
        """
        other._value = self._value
        other._on_change = self._on_change
        other._anim_id = self._anim_id
        other._styles = dict(self._styles)
        other._css_classes = list(self._css_classes)
