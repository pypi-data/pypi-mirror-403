"""Harlequin layout base class for multi-pane TUI screens.

This module provides the HarlequinScreen base class, which implements a modern
multi-pane "Harlequin" layout pattern for data-rich TUI screens. The layout uses
a 25/75 split with a list on the left and detail content on the right.

The Harlequin pattern is inspired by the Harlequin SQL client and provides:
- Left Pane (25%): ListView or compact table for item selection
- Right Pane (75%): Detail dashboard showing all fields, status, and action buttons
- Black background (#000000) that overrides terminal transparency
- Primary Blue borders (#005CB8)

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

try:  # pragma: no cover - optional dependency
    from textual.screen import Screen
    from textual.widget import Widget
except Exception:  # pragma: no cover - optional dependency

    class Screen:  # type: ignore[no-redef]
        """Fallback Screen stub when Textual is unavailable."""

        def __class_getitem__(cls, _):
            """Return the class for typing subscripts."""
            return cls

    Widget = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from glaip_sdk.cli.slash.tui.context import TUIContext

try:  # pragma: no cover - optional dependency
    from glaip_sdk.cli.slash.tui.toast import Toast, ToastContainer
except Exception:  # pragma: no cover - optional dependency
    Toast = None  # type: ignore[assignment, misc]
    ToastContainer = None  # type: ignore[assignment, misc]

# GDP Labs Brand Palette
PRIMARY_BLUE = "#005CB8"
BLACK_BACKGROUND = "#000000"


if Widget is not None:

    class HarlequinContainer(Widget):
        """Base container for the Harlequin layout."""

        DEFAULT_CSS = """
        HarlequinContainer {
            layout: horizontal;
        }
        """

    class HarlequinPane(Widget):
        """Pane container for Harlequin layout sections."""

        DEFAULT_CSS = """
        HarlequinPane {
            layout: vertical;
        }
        """

else:
    HarlequinContainer = None  # type: ignore[assignment, misc]
    HarlequinPane = None  # type: ignore[assignment, misc]


class HarlequinScreen(Screen[None]):  # type: ignore[misc]
    """Base class for Harlequin-style multi-pane screens.

    This screen provides a 25/75 split layout with a left pane for navigation
    and a right pane for details. The layout uses a black background that
    overrides terminal transparency and primary blue borders.

    Subclasses should override `compose()` to add their specific widgets to
    the left and right panes. Use the container IDs "left-pane" and "right-pane"
    to target specific panes in CSS or when querying widgets.

    Example:
        ```python
        class AccountHarlequinScreen(HarlequinScreen):
            def compose(self) -> ComposeResult:
                yield from super().compose()
                # Add widgets to left and right panes
                self.query_one("#left-pane").mount(AccountListView())
                self.query_one("#right-pane").mount(AccountDetailView())
        ```

    CSS:
        The screen includes default styling for the Harlequin layout:
        - Black background (#000000) for the entire screen
        - Primary blue borders (#005CB8) for panes
        - 25% width for left pane, 75% width for right pane
    """

    CSS = """
    HarlequinScreen {
        background: #000000;
        layers: base toasts;
    }

    #harlequin-container {
        width: 100%;
        height: 100%;
    }

    #left-pane {
        width: 25%;
        border: solid #005CB8;
        background: #000000;
    }

    #right-pane {
        width: 75%;
        border: solid #005CB8;
        background: #000000;
    }

    #toast-container {
        width: 100%;
        height: auto;
        dock: top;
        align: right top;
        layer: toasts;
    }
    """

    def __init__(
        self,
        *,
        ctx: TUIContext | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the Harlequin screen.

        Args:
            ctx: Optional TUI context for accessing services (keybinds, theme, toasts, clipboard).
            name: Optional name for the screen.
            id: Optional ID for the screen.
            classes: Optional CSS classes for the screen.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._ctx: TUIContext | None = ctx

    def compose(self) -> Any:
        """Compose the Harlequin layout with left and right panes.

        This method creates the base 25/75 split layout. Subclasses should
        call `super().compose()` and then add their specific widgets to the
        left and right panes.

        Returns:
            ComposeResult yielding the base layout containers.
        """
        if HarlequinContainer is None or HarlequinPane is None:
            return

        # Main container with horizontal split (25/75)
        yield HarlequinContainer(
            HarlequinPane(id="left-pane"),
            HarlequinPane(id="right-pane"),
            id="harlequin-container",
        )

        # Toast container for notifications
        if Toast is not None and ToastContainer is not None:
            yield ToastContainer(Toast(), id="toast-container")

    @property
    def ctx(self) -> TUIContext | None:
        """Get the TUI context if available.

        Returns:
            TUIContext instance or None if not provided.
        """
        return self._ctx
