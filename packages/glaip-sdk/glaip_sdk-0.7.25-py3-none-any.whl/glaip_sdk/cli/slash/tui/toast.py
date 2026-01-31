"""Toast widgets and state management for the TUI."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, cast

from rich.text import Text
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static


class ToastVariant(str, Enum):
    """Toast message variant for styling and behavior."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


DEFAULT_TOAST_DURATIONS_SECONDS: dict[ToastVariant, float] = {
    ToastVariant.SUCCESS: 2.0,
    ToastVariant.INFO: 3.0,
    ToastVariant.WARNING: 3.0,
    ToastVariant.ERROR: 5.0,
}


@dataclass(frozen=True, slots=True)
class ToastState:
    """Immutable toast notification state."""

    message: str
    variant: ToastVariant
    duration_seconds: float


class ToastBus:
    """Toast state manager with auto-dismiss functionality."""

    class Changed(Message):
        """Message sent when toast state changes."""

        def __init__(self, state: ToastState | None) -> None:
            """Initialize the changed message with new toast state."""
            super().__init__()
            self.state = state

    def __init__(self, on_change: Callable[[ToastBus.Changed], None] | None = None) -> None:
        """Initialize the toast bus with optional change callback."""
        self._state: ToastState | None = None
        self._dismiss_task: asyncio.Task[None] | None = None
        self._on_change = on_change

    @property
    def state(self) -> ToastState | None:
        """Return the current toast state, or None if no toast is shown."""
        return self._state

    def show(
        self,
        message: str,
        variant: ToastVariant | str = ToastVariant.INFO,
        *,
        duration_seconds: float | None = None,
    ) -> None:
        """Show a toast notification with the given message and variant.

        Args:
            message: The message to display in the toast.
            variant: The visual variant of the toast (INFO, SUCCESS, WARNING, ERROR).
            duration_seconds: Optional custom duration in seconds. If None, uses default
                duration for the variant (2s for SUCCESS, 3s for INFO/WARNING, 5s for ERROR).
        """
        resolved_variant = self._coerce_variant(variant)
        resolved_duration = (
            DEFAULT_TOAST_DURATIONS_SECONDS[resolved_variant] if duration_seconds is None else float(duration_seconds)
        )

        self._state = ToastState(
            message=message,
            variant=resolved_variant,
            duration_seconds=resolved_duration,
        )

        self._cancel_dismiss_task()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError(
                "Cannot schedule toast auto-dismiss: no running event loop. "
                "ToastBus.show() must be called from within an async context."
            ) from None

        self._dismiss_task = loop.create_task(self._auto_dismiss(resolved_duration))
        self._notify_changed()

    def clear(self) -> None:
        """Clear the current toast notification immediately."""
        self._cancel_dismiss_task()
        self._state = None
        self._notify_changed()

    def copy_success(self, label: str | None = None) -> None:
        """Show a success toast for clipboard copy operations.

        Args:
            label: Optional label for what was copied (e.g., "Run ID", "JSON").
        """
        message = "Copied to clipboard" if not label else f"Copied {label} to clipboard"
        self.show(message=message, variant=ToastVariant.SUCCESS)

    def copy_failed(self) -> None:
        """Show a warning toast when clipboard copy fails."""
        self.show(message="Clipboard unavailable. Text printed below.", variant=ToastVariant.WARNING)

    def _coerce_variant(self, variant: ToastVariant | str) -> ToastVariant:
        if isinstance(variant, ToastVariant):
            return variant
        try:
            return ToastVariant(variant)
        except ValueError:
            return ToastVariant.INFO

    def _cancel_dismiss_task(self) -> None:
        if self._dismiss_task is None:
            return
        if not self._dismiss_task.done():
            self._dismiss_task.cancel()
        self._dismiss_task = None

    async def _auto_dismiss(self, duration_seconds: float) -> None:
        try:
            await asyncio.sleep(duration_seconds)
        except asyncio.CancelledError:
            return

        self._state = None
        self._dismiss_task = None
        self._notify_changed()

    def _notify_changed(self) -> None:
        if self._on_change:
            self._on_change(ToastBus.Changed(self._state))


class ToastHandlerMixin:
    """Mixin providing common toast handling functionality.

    Classes that inherit from this mixin can handle ToastBus.Changed messages
    by automatically updating all Toast widgets in the component tree.
    """

    def on_toast_bus_changed(self, message: ToastBus.Changed) -> None:
        """Refresh the toast widget when the toast bus updates.

        Args:
            message: The toast bus changed message containing the new state.
        """
        try:
            for toast in self.query(Toast):
                toast.update_state(message.state)
        except Exception:
            pass


class ClipboardToastMixin:
    """Mixin providing clipboard and toast orchestration functionality.

    Classes that inherit from this mixin get shared clipboard adapter selection,
    OSC52 writer setup, toast bus lookup, and copy-success/failure orchestration.
    This consolidates duplicate clipboard/toast logic across TUI apps.

    Expected attributes:
        _ctx: TUIContext | None - Shared TUI context (optional)
        _clip_cache: ClipboardAdapter | None - Cached clipboard adapter (optional)
        _local_toasts: ToastBus | None - Local toast bus instance (optional)
    """

    def _clip_adapter(self) -> Any:  # ClipboardAdapter
        """Get or create a clipboard adapter instance.

        Returns:
            ClipboardAdapter instance, preferring context's adapter if available.
        """
        # Import here to avoid circular dependency
        from glaip_sdk.cli.slash.tui.clipboard import ClipboardAdapter  # noqa: PLC0415

        ctx = getattr(self, "_ctx", None)
        clipboard = getattr(self, "_clip_cache", None)

        if ctx is not None and ctx.clipboard is not None:
            return cast(ClipboardAdapter, ctx.clipboard)
        if clipboard is not None:
            return clipboard

        adapter = ClipboardAdapter(terminal=ctx.terminal if ctx else None)
        if ctx is not None:
            ctx.clipboard = adapter
        else:
            self._clip_cache = adapter
        return adapter

    def _osc52_writer(self) -> Callable[[str], Any] | None:
        """Get an OSC52 writer function if console output is available.

        Returns:
            Writer function that writes OSC52 sequences to console output, or None.
        """
        try:
            # Try self.app.console first (for Screen subclasses)
            if hasattr(self, "app") and hasattr(self.app, "console"):
                console = self.app.console
            # Fall back to self.console (for App subclasses)
            else:
                console = getattr(self, "console", None)
        except Exception:
            return None

        if console is None:
            return None

        output = getattr(console, "file", None)
        if output is None:
            return None

        def _write(sequence: str, _output: Any = output) -> None:
            _output.write(sequence)
            _output.flush()

        return _write

    def _toast_bus(self) -> ToastBus | None:
        """Get the toast bus instance.

        Returns:
            ToastBus instance, preferring context's bus if available, or None.
        """
        local_toasts = getattr(self, "_local_toasts", None)
        ctx = getattr(self, "_ctx", None)

        if local_toasts is not None:
            return local_toasts
        if ctx is not None and ctx.toasts is not None:
            return ctx.toasts
        return None

    def _copy_to_clipboard(self, text: str, *, label: str | None = None) -> None:
        """Copy text to clipboard and show toast notification.

        Args:
            text: The text to copy to clipboard.
            label: Optional label for what was copied (e.g., "Run ID", "JSON").
        """
        adapter = self._clip_adapter()
        writer = self._osc52_writer()
        if writer:
            result = adapter.copy(text, writer=writer)
        else:
            result = adapter.copy(text)

        toasts = self._toast_bus()
        if result.success:
            if toasts:
                toasts.copy_success(label)
            else:
                # Fallback to status announcement if toast bus unavailable
                if hasattr(self, "_announce_status"):
                    if label:
                        self._announce_status(f"Copied {label} to clipboard.")
                    else:
                        self._announce_status("Copied to clipboard.")
            return

        # Copy failed
        if toasts:
            toasts.copy_failed()
        else:
            # Fallback to status announcement if toast bus unavailable
            if hasattr(self, "_announce_status"):
                self._announce_status("Clipboard unavailable. Text printed below.")

        # Append fallback text output
        if hasattr(self, "_append_copy_fallback"):
            self._append_copy_fallback(text)


class ToastContainer(Widget):
    """Simple wrapper for docking toast widgets without relying on containers.

    This class exists to provide a lightweight widget wrapper for toast containers
    that avoids direct dependency on Textual's Container class. It allows the toast
    system to work consistently across different Textual versions and provides a
    stable API for toast container composition.

    Usage:
        yield ToastContainer(Toast(), id="toast-container")
    """


class Toast(Static):
    """A Textual widget that displays toast notifications at the top-right of the screen.

    The Toast widget is updated via `update_state()` calls from message handlers
    (e.g., `on_toast_bus_changed`). The widget does not auto-subscribe to ToastBus
    state changes; the app must call `update_state()` when toast state changes.
    """

    DEFAULT_CSS = """
    #toast-container {
        width: 100%;
        height: auto;
        dock: top;
        align: right top;
    }

    Toast {
        width: auto;
        min-width: 20;
        max-width: 40;
        height: auto;
        padding: 0 1;
        margin: 1 2;
        background: $surface;
        color: $text;
        border: solid $primary;
        display: none;
    }

    Toast.visible {
        display: block;
    }

    Toast.info {
        border: solid $accent;
    }

    Toast.success {
        border: solid $success;
    }

    Toast.warning {
        border: solid $warning;
    }

    Toast.error {
        border: solid $error;
    }
    """

    def __init__(self) -> None:
        """Initialize the Toast widget.

        The widget is updated via `update_state()` calls from message handlers
        (e.g., `on_toast_bus_changed`). The widget does not auto-subscribe to
        a ToastBus; the app must call `update_state()` when toast state changes.
        """
        super().__init__("")

    def update_state(self, state: ToastState | None) -> None:
        """Update the toast display based on the provided state.

        Args:
            state: The toast state to display, or None to hide the toast.
        """
        if not state:
            self.remove_class("visible")
            return

        icon = "ℹ️"
        if state.variant == ToastVariant.SUCCESS:
            icon = "✅"
        elif state.variant == ToastVariant.WARNING:
            icon = "⚠️"
        elif state.variant == ToastVariant.ERROR:
            icon = "❌"

        self.update(Text.assemble((f"{icon} ", "bold"), state.message))

        self.remove_class("info", "success", "warning", "error")
        self.add_class(state.variant.value)
        self.add_class("visible")
