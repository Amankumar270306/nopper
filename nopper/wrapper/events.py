"""EventBus — Observer pattern for plugin/middleware lifecycle events."""

from collections.abc import Callable
from typing import Any


class EventBus:
    """Event bus for publishing and subscribing to SDK events.

    Built-in event names:
      - "on_request": Fired before handing request to Node
      - "on_response": Fired after receiving response from Node
      - "on_error": Fired when an execution error occurs
      - "on_token": Fired during streaming chunk emission
      - "on_cost": Fired when token usage and cost are computed
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., Any]]] = {}

    def on(self, event: str, handler: Callable[..., Any]) -> None:
        """Subscribe a handler to an event."""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def emit(self, event: str, **kwargs: Any) -> None:
        """Publish an event to all subscribers."""
        if event in self._handlers:
            for handler in self._handlers[event]:
                try:
                    handler(**kwargs)
                except Exception:
                    pass  # Event handlers must not crash execution
