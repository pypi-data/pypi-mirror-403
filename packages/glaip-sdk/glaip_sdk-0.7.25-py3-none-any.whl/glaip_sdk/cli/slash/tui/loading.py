"""Shared helpers for toggling Textual loading indicators.

This module provides unified helpers for showing/hiding both the built-in
Textual LoadingIndicator and the custom PulseIndicator.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from textual.widgets import LoadingIndicator

from glaip_sdk.cli.slash.tui.indicators import PulseIndicator


def _set_indicator_display(app: Any, selector: str, visible: bool) -> None:
    try:
        indicator = app.query_one(selector, PulseIndicator)
        if visible:
            indicator.display = True
            indicator.start()
        else:
            indicator.stop()
            indicator.display = False
        return
    except Exception:
        pass

    try:
        indicator = app.query_one(selector, LoadingIndicator)
        indicator.display = visible
    except Exception:
        return


def show_loading_indicator(
    app: Any,
    selector: str,
    *,
    message: str | None = None,
    set_status: Callable[..., None] | None = None,
    status_style: str = "cyan",
) -> None:
    """Show a loading indicator (PulseIndicator or LoadingIndicator) and optionally set a status message.

    Args:
        app: Textual app instance containing the indicator widget
        selector: CSS selector for the indicator widget
        message: Optional message to display in the indicator
        set_status: Optional callback to set status message (for fallback display)
        status_style: Style for status message if set_status is provided
    """
    _set_indicator_display(app, selector, True)

    try:
        indicator = app.query_one(selector, PulseIndicator)
        if message:
            indicator.update_message(message)
    except Exception:
        pass

    if message and set_status:
        try:
            set_status(message, status_style)
        except TypeError:
            try:
                set_status(message)
            except Exception:
                return


def hide_loading_indicator(app: Any, selector: str) -> None:
    """Hide a loading indicator (PulseIndicator or LoadingIndicator).

    Args:
        app: Textual app instance containing the indicator widget
        selector: CSS selector for the indicator widget
    """
    _set_indicator_display(app, selector, False)
