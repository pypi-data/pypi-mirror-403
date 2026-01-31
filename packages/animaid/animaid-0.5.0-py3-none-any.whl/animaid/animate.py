"""Animate - Tkinter-like interactive GUI environment using HTML."""

from __future__ import annotations

import asyncio
import queue
import threading
import time
import webbrowser
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from animaid.input_event import InputEvent

if TYPE_CHECKING:
    from animaid.html_object import HTMLObject


class Animate:
    """A Tkinter-like interactive GUI environment using HTML.

    The browser becomes the display surface, and AnimAID objects become
    widgets that can be added, updated, and removed programmatically
    with real-time visual feedback.

    Examples:
        >>> from animaid import Animate, HTMLString
        >>> anim = Animate()
        >>> anim.run()  # Starts server, opens browser
        >>> anim.add(HTMLString("Hello").bold)
        'item_0'
        >>> anim.add(HTMLString("World").italic)
        'item_1'
        >>> anim.stop()

        # Context manager support
        >>> with Animate() as anim:
        ...     anim.add(HTMLString("Temporary display"))
        # Server stops when context exits
    """

    def __init__(
        self,
        port: int = 8200,
        title: str = "AnimAID",
        auto_open: bool = True,
    ) -> None:
        """Initialize the Animate environment.

        Args:
            port: Port number for the server (default: 8200).
            title: Title displayed in the browser window.
            auto_open: Whether to automatically open browser on run().
        """
        self._port = port
        self._title = title
        self._auto_open = auto_open
        self._items: list[tuple[str, Any]] = []  # (id, item) pairs
        self._connections: set[Any] = set()  # WebSocket connections
        self._server_thread: threading.Thread | None = None
        self._server: Any = None
        self._lock = threading.Lock()
        self._type_counters: dict[str, int] = {}  # Counters per type name
        self._running = False
        self._shutdown_event: asyncio.Event | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._obs_id_to_item_id: dict[str, str] = {}  # Maps obs_id -> item_id
        self._pubsub_subscribed = False
        # Input event handling
        self._event_queue: queue.Queue[InputEvent] = queue.Queue()
        self._input_handlers: dict[str, Callable[..., Any]] = {}

    def run(self) -> Animate:
        """Start the server in a background thread and open the browser.

        Returns:
            Self for method chaining.
        """
        if self._running:
            return self

        # Subscribe to pypubsub for reactive updates
        try:
            from pubsub import pub

            pub.subscribe(self._on_data_changed, "animaid.changed")
            self._pubsub_subscribed = True
        except ImportError:
            pass  # pypubsub not installed

        from animaid.animate_server import create_animate_app

        app = create_animate_app(self)

        def server_thread() -> None:
            import uvicorn

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            self._shutdown_event = asyncio.Event()

            config = uvicorn.Config(
                app,
                host="127.0.0.1",
                port=self._port,
                log_level="warning",
                ws="wsproto",  # Use wsproto to avoid websockets deprecation warnings
            )
            server = uvicorn.Server(config)
            self._server = server

            loop.run_until_complete(server.serve())

        self._server_thread = threading.Thread(target=server_thread, daemon=True)
        self._server_thread.start()
        self._running = True

        # Wait for server to be ready
        time.sleep(0.5)

        # Open browser if requested
        if self._auto_open:
            webbrowser.open(self.url)

        return self

    def stop(self) -> None:
        """Stop the server."""
        if not self._running:
            return

        self._running = False

        # Unsubscribe from pypubsub
        if self._pubsub_subscribed:
            try:
                from pubsub import pub

                pub.unsubscribe(self._on_data_changed, "animaid.changed")
            except Exception:
                pass
            self._pubsub_subscribed = False

        if self._server is not None:
            self._server.should_exit = True

        # Give the server a moment to shut down
        if self._server_thread is not None:
            self._server_thread.join(timeout=2.0)

        self._server = None
        self._server_thread = None

    def add(self, item: HTMLObject | str, id: str | None = None) -> str:
        """Add an item to the display.

        Args:
            item: An HTMLObject or string to display.
            id: Optional custom ID for the item. Auto-generated if not provided.

        Returns:
            The ID of the added item.
        """
        if id is None:
            id = self._generate_id(item)

        with self._lock:
            self._items.append((id, item))

            # Track observable ID if present (for reactive updates)
            obs_id = getattr(item, "_obs_id", None)
            if obs_id:
                self._obs_id_to_item_id[obs_id] = id

            # Store the animate ID on the object for easy removal
            try:
                item._anim_id = id  # type: ignore[union-attr]
            except (AttributeError, TypeError):
                pass  # Can't set attribute on strings or other immutable types

        self._broadcast_add(id, item)
        return id

    def update(self, id: str, item: HTMLObject | str) -> bool:
        """Update an existing item by ID.

        Args:
            id: The ID of the item to update.
            item: The new content to display.

        Returns:
            True if the item was found and updated, False otherwise.
        """
        with self._lock:
            for i, (item_id, _) in enumerate(self._items):
                if item_id == id:
                    self._items[i] = (id, item)
                    self._broadcast_update(id, item)
                    return True
        return False

    def remove(self, item_or_id: HTMLObject | str) -> bool:
        """Remove an item by ID or by object reference.

        Args:
            item_or_id: The ID of the item to remove, or the item object itself.

        Returns:
            True if the item was found and removed, False otherwise.
        """
        # Check if passed an object with _anim_id (use that ID)
        # Must check _anim_id first since HTMLString is a str subclass
        anim_id = getattr(item_or_id, "_anim_id", None)
        if anim_id is not None:
            id = anim_id
        elif isinstance(item_or_id, str):
            id = item_or_id
        else:
            return False

        with self._lock:
            for i, (item_id, item) in enumerate(self._items):
                if item_id == id:
                    # Clean up obs_id mapping
                    obs_id = getattr(item, "_obs_id", None)
                    if obs_id:
                        self._obs_id_to_item_id.pop(obs_id, None)

                    # Clean up _anim_id on the item
                    try:
                        item._anim_id = None  # type: ignore[union-attr]
                    except (AttributeError, TypeError):
                        pass

                    self._items.pop(i)
                    self._broadcast_remove(id)
                    return True
        return False

    def clear(self, item_or_id: HTMLObject | str) -> bool:
        """Remove an item by ID or by object reference.

        Args:
            item_or_id: The ID of the item to remove, or the item object itself.

        Returns:
            True if the item was found and removed, False otherwise.
        """
        return self.remove(item_or_id)

    def clear_all(self) -> None:
        """Remove all items from the display."""
        with self._lock:
            self._items.clear()
            self._obs_id_to_item_id.clear()

        self._broadcast_clear()

    def get(self, id: str) -> Any:
        """Get an item by ID.

        Args:
            id: The ID of the item to retrieve.

        Returns:
            The item if found, None otherwise.
        """
        with self._lock:
            for item_id, item in self._items:
                if item_id == id:
                    return item
        return None

    def items(self) -> list[tuple[str, Any]]:
        """Get a copy of all items.

        Returns:
            A list of (id, item) tuples.
        """
        with self._lock:
            return list(self._items)

    @property
    def url(self) -> str:
        """Get the server URL."""
        return f"http://127.0.0.1:{self._port}"

    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running

    @property
    def title(self) -> str:
        """Get the display title."""
        return self._title

    @property
    def port(self) -> int:
        """Get the server port."""
        return self._port

    def register_connection(self, websocket: Any) -> None:
        """Register a WebSocket connection.

        This is called by the server when a new client connects.

        Args:
            websocket: The WebSocket connection to register.
        """
        self._connections.add(websocket)

    def unregister_connection(self, websocket: Any) -> None:
        """Unregister a WebSocket connection.

        This is called by the server when a client disconnects.

        Args:
            websocket: The WebSocket connection to unregister.
        """
        self._connections.discard(websocket)

    def _generate_id(self, item: HTMLObject | str) -> str:
        """Generate a unique ID for an item based on its type.

        Args:
            item: The item to generate an ID for.

        Returns:
            A type-based ID like 'string_1', 'list_2', etc.
        """
        # Get the type name
        type_name = type(item).__name__
        # Strip 'HTML' prefix if present (HTMLString -> String)
        if type_name.startswith("HTML"):
            type_name = type_name[4:]
        # Convert to lowercase
        type_name = type_name.lower()

        with self._lock:
            # Get and increment counter for this type
            count = self._type_counters.get(type_name, 0) + 1
            self._type_counters[type_name] = count
            return f"{type_name}_{count}"

    def _render_item(self, item: HTMLObject | str) -> str:
        """Render an item to HTML string."""
        if hasattr(item, "render"):
            return item.render()
        return str(item)

    def _broadcast_add(self, id: str, item: HTMLObject | str) -> None:
        """Broadcast an add message to all connected clients."""
        html = self._render_item(item)
        self._broadcast({"type": "add", "id": id, "html": html})

    def _broadcast_update(self, id: str, item: HTMLObject | str) -> None:
        """Broadcast an update message to all connected clients."""
        html = self._render_item(item)
        self._broadcast({"type": "update", "id": id, "html": html})

    def _broadcast_remove(self, id: str) -> None:
        """Broadcast a remove message to all connected clients."""
        self._broadcast({"type": "remove", "id": id})

    def _broadcast_clear(self) -> None:
        """Broadcast a clear message to all connected clients."""
        self._broadcast({"type": "clear"})

    def _broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected WebSocket clients."""
        import json

        if not self._connections:
            return

        data = json.dumps(message)
        dead_connections = set()

        for ws in list(self._connections):
            try:
                if self._loop is not None:
                    asyncio.run_coroutine_threadsafe(ws.send_text(data), self._loop)
            except Exception:
                dead_connections.add(ws)

        # Clean up dead connections
        self._connections -= dead_connections

    def get_full_state(self) -> list[dict[str, str]]:
        """Get the full state as a list of rendered items.

        Returns:
            A list of {"id": ..., "html": ...} dicts.
        """
        with self._lock:
            return [
                {"id": id, "html": self._render_item(item)} for id, item in self._items
            ]

    def _on_data_changed(self, obs_id: str) -> None:
        """Handle pypubsub notification when an observable item changes.

        Args:
            obs_id: The observable ID of the changed item.
        """
        item_id = self._obs_id_to_item_id.get(obs_id)
        if item_id:
            self.refresh(item_id)

    def refresh(self, id: str) -> bool:
        """Re-render and broadcast a single item.

        Use this to manually refresh an item after external changes.

        Args:
            id: The ID of the item to refresh.

        Returns:
            True if item was found and refreshed, False otherwise.
        """
        with self._lock:
            for item_id, item in self._items:
                if item_id == id:
                    self._broadcast_update(id, item)
                    return True
        return False

    def refresh_all(self) -> None:
        """Re-render and broadcast all items.

        Use this to manually refresh all items after external changes.
        """
        with self._lock:
            for item_id, item in self._items:
                self._broadcast_update(item_id, item)

    def wait_for_event(self, timeout: float | None = None) -> InputEvent | None:
        """Block until an input event occurs.

        Args:
            timeout: Maximum time to wait in seconds. None means wait forever.

        Returns:
            The InputEvent if one occurred, None if timeout expired.

        Examples:
            >>> event = anim.wait_for_event(timeout=1.0)
            >>> if event and event.event_type == "click":
            ...     print(f"Button {event.id} was clicked!")
        """
        try:
            return self._event_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_events(self) -> list[InputEvent]:
        """Get all pending events without blocking.

        Returns:
            A list of all pending InputEvent objects. Empty list if none.

        Examples:
            >>> events = anim.get_events()
            >>> for event in events:
            ...     print(f"Event: {event.event_type} on {event.id}")
        """
        events = []
        while True:
            try:
                events.append(self._event_queue.get_nowait())
            except queue.Empty:
                break
        return events

    def handle_input_event(self, message: dict[str, Any]) -> None:
        """Handle an input event from the browser.

        This is called by the server when an input event is received.
        It updates the item's internal value, calls registered callbacks,
        and queues the event for polling.

        Args:
            message: The event message containing id, event type, and value.
        """
        import time

        item_id = message.get("id", "")
        event_type = message.get("event", "")
        value = message.get("value")

        # Get the item
        item = self.get(item_id)

        # Update item's internal value if it has one
        if item is not None and hasattr(item, "_value") and value is not None:
            if hasattr(item, "_lock"):
                with item._lock:
                    item._value = value
            else:
                item._value = value

        # Call registered callbacks on the item
        if item is not None:
            if event_type == "change" and hasattr(item, "_on_change"):
                callback = item._on_change
                if callback is not None:
                    callback(value)
            elif event_type == "click" and hasattr(item, "_on_click"):
                callback = item._on_click
                if callback is not None:
                    callback()
            elif event_type == "submit" and hasattr(item, "_on_submit"):
                callback = item._on_submit
                if callback is not None:
                    callback(value)

        # Queue event for polling
        self._event_queue.put(
            InputEvent(
                id=item_id,
                event_type=event_type,
                value=value,
                timestamp=time.time(),
            )
        )

    def __enter__(self) -> Animate:
        """Enter context manager - start the server."""
        return self.run()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit context manager - stop the server."""
        self.stop()
